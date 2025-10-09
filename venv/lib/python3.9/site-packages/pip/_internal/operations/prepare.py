"""Prepares a distribution for installation"""

# The following comment should be removed at some point in the future.
# mypy: strict-optional=False
from __future__ import annotations

import mimetypes
import os
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from pip._vendor.packaging.utils import canonicalize_name

from pip._internal.build_env import BuildEnvironmentInstaller
from pip._internal.distributions import make_distribution_for_install_requirement
from pip._internal.distributions.installed import InstalledDistribution
from pip._internal.exceptions import (
    DirectoryUrlHashUnsupported,
    HashMismatch,
    HashUnpinned,
    InstallationError,
    MetadataInconsistent,
    NetworkConnectionError,
    VcsHashUnsupported,
)
from pip._internal.index.package_finder import PackageFinder
from pip._internal.metadata import BaseDistribution, get_metadata_distribution
from pip._internal.models.direct_url import ArchiveInfo
from pip._internal.models.link import Link
from pip._internal.models.wheel import Wheel
from pip._internal.network.download import Downloader
from pip._internal.network.lazy_wheel import (
    HTTPRangeRequestUnsupported,
    dist_from_wheel_url,
)
from pip._internal.network.session import PipSession
from pip._internal.operations.build.build_tracker import BuildTracker
from pip._internal.req.req_install import InstallRequirement
from pip._internal.utils._log import getLogger
from pip._internal.utils.direct_url_helpers import (
    direct_url_for_editable,
    direct_url_from_link,
)
from pip._internal.utils.hashes import Hashes, MissingHashes
from pip._internal.utils.logging import indent_log
from pip._internal.utils.misc import (
    display_path,
    hash_file,
    hide_url,
    redact_auth_from_requirement,
)
from pip._internal.utils.temp_dir import TempDirectory
from pip._internal.utils.unpacking import unpack_file
from pip._internal.vcs import vcs

if TYPE_CHECKING:
    from pip._internal.cli.progress_bars import BarType

logger = getLogger(__name__)


def _get_prepared_distribution(
    req: InstallRequirement,
    build_tracker: BuildTracker,
    build_env_installer: BuildEnvironmentInstaller,
    build_isolation: bool,
    check_build_deps: bool,
) -> BaseDistribution:
    """Prepare a distribution for installation."""
    abstract_dist = make_distribution_for_install_requirement(req)
    tracker_id = abstract_dist.build_tracker_id
    if tracker_id is not None:
        with build_tracker.track(req, tracker_id):
            abstract_dist.prepare_distribution_metadata(
                build_env_installer, build_isolation, check_build_deps
            )
    return abstract_dist.get_metadata_distribution()


def unpack_vcs_link(link: Link, location: str, verbosity: int) -> None:
    vcs_backend = vcs.get_backend_for_scheme(link.scheme)
    assert vcs_backend is not None
    vcs_backend.unpack(location, url=hide_url(link.url), verbosity=verbosity)


@dataclass
class File:
    path: str
    content_type: str | None = None

    def __post_init__(self) -> None:
        if self.content_type is None:
            # Try to guess the file's MIME type. If the system MIME tables
            # can't be loaded, give up.
            try:
                self.content_type = mimetypes.guess_type(self.path)[0]
            except OSError:
                pass


def get_http_url(
    link: Link,
    download: Downloader,
    download_dir: str | None = None,
    hashes: Hashes | None = None,
) -> File:
    temp_dir = TempDirectory(kind="unpack", globally_managed=True)
    # If a download dir is specified, is the file already downloaded there?
    already_downloaded_path = None
    if download_dir:
        already_downloaded_path = _check_download_dir(link, download_dir, hashes)

    if already_downloaded_path:
        from_path = already_downloaded_path
        content_type = None
    else:
        # let's download to a tmp dir
        from_path, content_type = download(link, temp_dir.path)
        if hashes:
            hashes.check_against_path(from_path)

    return File(from_path, content_type)


def get_file_url(
    link: Link, download_dir: str | None = None, hashes: Hashes | None = None
) -> File:
    """Get file and optionally check its hash."""
    # If a download dir is specified, is the file already there and valid?
    already_downloaded_path = None
    if download_dir:
        already_downloaded_path = _check_download_dir(link, download_dir, hashes)

    if already_downloaded_path:
        from_path = already_downloaded_path
    else:
        from_path = link.file_path

    # If --require-hashes is off, `hashes` is either empty, the
    # link's embedded hash, or MissingHashes; it is required to
    # match. If --require-hashes is on, we are satisfied by any
    # hash in `hashes` matching: a URL-based or an option-based
    # one; no internet-sourced hash will be in `hashes`.
    if hashes:
        hashes.check_against_path(from_path)
    return File(from_path, None)


def unpack_url(
    link: Link,
    location: str,
    download: Downloader,
    verbosity: int,
    download_dir: str | None = None,
    hashes: Hashes | None = None,
) -> File | None:
    """Unpack link into location, downloading if required.

    :param hashes: A Hashes object, one of whose embedded hashes must match,
        or HashMismatch will be raised. If the Hashes is empty, no matches are
        required, and unhashable types of requirements (like VCS ones, which
        would ordinarily raise HashUnsupported) are allowed.
    """
    # non-editable vcs urls
    if link.is_vcs:
        unpack_vcs_link(link, location, verbosity=verbosity)
        return None

    assert not link.is_existing_dir()

    # file urls
    if link.is_file:
        file = get_file_url(link, download_dir, hashes=hashes)

    # http urls
    else:
        file = get_http_url(
            link,
            download,
            download_dir,
            hashes=hashes,
        )

    # unpack the archive to the build dir location. even when only downloading
    # archives, they have to be unpacked to parse dependencies, except wheels
    if not link.is_wheel:
        unpack_file(file.path, location, file.content_type)

    return file


def _check_download_dir(
    link: Link,
    download_dir: str,
    hashes: Hashes | None,
    warn_on_hash_mismatch: bool = True,
) -> str | None:
    """Check download_dir for previously downloaded file with correct hash
    If a correct file is found return its path else None
    """
    download_path = os.path.join(download_dir, link.filename)

    if not os.path.exists(download_path):
        return None

    # If already downloaded, does its hash match?
    logger.info("File was already downloaded %s", download_path)
    if hashes:
        try:
            hashes.check_against_path(download_path)
        except HashMismatch:
            if warn_on_hash_mismatch:
                logger.warning(
                    "Previously-downloaded file %s has bad hash. Re-downloading.",
                    download_path,
                )
            os.unlink(download_path)
            return None
    return download_path


class RequirementPreparer:
    """Prepares a Requirement"""

    def __init__(  # noqa: PLR0913 (too many parameters)
        self,
        *,
        build_dir: str,
        download_dir: str | None,
        src_dir: str,
        build_isolation: bool,
        build_isolation_installer: BuildEnvironmentInstaller,
        check_build_deps: bool,
        build_tracker: BuildTracker,
        session: PipSession,
        progress_bar: BarType,
        finder: PackageFinder,
        require_hashes: bool,
        use_user_site: bool,
        lazy_wheel: bool,
        verbosity: int,
        legacy_resolver: bool,
        resume_retries: int,
    ) -> None:
        super().__init__()

        self.src_dir = src_dir
        self.build_dir = build_dir
        self.build_tracker = build_tracker
        self._session = session
        self._download = Downloader(session, progress_bar, resume_retries)
        self.finder = finder

        # Where still-packed archives should be written to. If None, they are
        # not saved, and are deleted immediately after unpacking.
        self.download_dir = download_dir

        # Is build isolation allowed?
        self.build_isolation = build_isolation
        self.build_env_installer = build_isolation_installer

        # Should check build dependencies?
        self.check_build_deps = check_build_deps

        # Should hash-checking be required?
        self.require_hashes = require_hashes

        # Should install in user site-packages?
        self.use_user_site = use_user_site

        # Should wheels be downloaded lazily?
        self.use_lazy_wheel = lazy_wheel

        # How verbose should underlying tooling be?
        self.verbosity = verbosity

        # Are we using the legacy resolver?
        self.legacy_resolver = legacy_resolver

        # Memoized downloaded files, as mapping of url: path.
        self._downloaded: dict[str, str] = {}

        # Previous "header" printed for a link-based InstallRequirement
        self._previous_requirement_header = ("", "")

    def _log_preparing_link(self, req: InstallRequirement) -> None:
        """Provide context for the requirement being prepared."""
        if req.link.is_file and not req.is_wheel_from_cache:
            message = "Processing %s"
            information = str(display_path(req.link.file_path))
        else:
            message = "Collecting %s"
            information = redact_auth_from_requirement(req.req) if req.req else str(req)

        # If we used req.req, inject requirement source if available (this
        # would already be included if we used req directly)
        if req.req and req.comes_from:
            if isinstance(req.comes_from, str):
                comes_from: str | None = req.comes_from
            else:
                comes_from = req.comes_from.from_path()
            if comes_from:
                information += f" (from {comes_from})"

        if (message, information) != self._previous_requirement_header:
            self._previous_requirement_header = (message, information)
            logger.info(message, information)

        if req.is_wheel_from_cache:
            with indent_log():
                logger.info("Using cached %s", req.link.filename)

    def _ensure_link_req_src_dir(
        self, req: InstallRequirement, parallel_builds: bool
    ) -> None:
        """Ensure source_dir of a linked InstallRequirement."""
        # Since source_dir is only set for editable requirements.
        if req.link.is_wheel:
            # We don't need to unpack wheels, so no need for a source
            # directory.
            return
        assert req.source_dir is None
        if req.link.is_existing_dir():
            # build local directories in-tree
            req.source_dir = req.link.file_path
            return

        # We always delete unpacked sdists after pip runs.
        req.ensure_has_source_dir(
            self.build_dir,
            autodelete=True,
            parallel_builds=parallel_builds,
        )
        req.ensure_pristine_source_checkout()

    def _get_linked_req_hashes(self, req: InstallRequirement) -> Hashes:
        # By the time this is called, the requirement's link should have
        # been checked so we can tell what kind of requirements req is
        # and raise some more informative errors than otherwise.
        # (For example, we can raise VcsHashUnsupported for a VCS URL
        # rather than HashMissing.)
        if not self.require_hashes:
            return req.hashes(trust_internet=True)

        # We could check these first 2 conditions inside unpack_url
        # and save repetition of conditions, but then we would
        # report less-useful error messages for unhashable
        # requirements, complaining that there's no hash provided.
        if req.link.is_vcs:
            raise VcsHashUnsupported()
        if req.link.is_existing_dir():
            raise DirectoryUrlHashUnsupported()

        # Unpinned packages are asking for trouble when a new version
        # is uploaded.  This isn't a security check, but it saves users
        # a surprising hash mismatch in the future.
        # file:/// URLs aren't pinnable, so don't complain about them
        # not being pinned.
        if not req.is_direct and not req.is_pinned:
            raise HashUnpinned()

        # If known-good hashes are missing for this requirement,
        # shim it with a facade object that will provoke hash
        # computation and then raise a HashMissing exception
        # showing the user what the hash should be.
        return req.hashes(trust_internet=False) or MissingHashes()

    def _fetch_metadata_only(
        self,
        req: InstallRequirement,
    ) -> BaseDistribution | None:
        if self.legacy_resolver:
            logger.debug(
                "Metadata-only fetching is not used in the legacy resolver",
            )
            return None
        if self.require_hashes:
            logger.debug(
                "Metadata-only fetching is not used as hash checking is required",
            )
            return None
        # Try PEP 658 metadata first, then fall back to lazy wheel if unavailable.
        return self._fetch_metadata_using_link_data_attr(
            req
        ) or self._fetch_metadata_using_lazy_wheel(req.link)

    def _fetch_metadata_using_link_data_attr(
        self,
        req: InstallRequirement,
    ) -> BaseDistribution | None:
        """Fetch metadata from the data-dist-info-metadata attribute, if possible."""
        # (1) Get the link to the metadata file, if provided by the backend.
        metadata_link = req.link.metadata_link()
        if metadata_link is None:
            return None
        assert req.req is not None
        logger.verbose(
            "Obtaining dependency information for %s from %s",
            req.req,
            metadata_link,
        )
        # (2) Download the contents of the METADATA file, separate from the dist itself.
        metadata_file = get_http_url(
            metadata_link,
            self._download,
            hashes=metadata_link.as_hashes(),
        )
        with open(metadata_file.path, "rb") as f:
            metadata_contents = f.read()
        # (3) Generate a dist just from those file contents.
        metadata_dist = get_metadata_distribution(
            metadata_contents,
            req.link.filename,
            req.req.name,
        )
        # (4) Ensure the Name: field from the METADATA file matches the name from the
        #     install requirement.
        #
        #     NB: raw_name will fall back to the name from the install requirement if
        #     the Name: field is not present, but it's noted in the raw_name docstring
        #     that that should NEVER happen anyway.
        if canonicalize_name(metadata_dist.raw_name) != canonicalize_name(req.req.name):
            raise MetadataInconsistent(
                req, "Name", req.req.name, metadata_dist.raw_name
            )
        return metadata_dist

    def _fetch_metadata_using_lazy_wheel(
        self,
        link: Link,
    ) -> BaseDistribution | None:
        """Fetch metadata using lazy wheel, if possible."""
        # --use-feature=fast-deps must be provided.
        if not self.use_lazy_wheel:
            return None
        if link.is_file or not link.is_wheel:
            logger.debug(
                "Lazy wheel is not used as %r does not point to a remote wheel",
                link,
            )
            return None

        wheel = Wheel(link.filename)
        name = canonicalize_name(wheel.name)
        logger.info(
            "Obtaining dependency information from %s %s",
            name,
            wheel.version,
        )
        url = link.url.split("#", 1)[0]
        try:
            return dist_from_wheel_url(name, url, self._session)
        except HTTPRangeRequestUnsupported:
            logger.debug("%s does not support range requests", url)
            return None

    def _complete_partial_requirements(
        self,
        partially_downloaded_reqs: Iterable[InstallRequirement],
        parallel_builds: bool = False,
    ) -> None:
        """Download any requirements which were only fetched by metadata."""
        # Download to a temporary directory. These will be copied over as
        # needed for downstream 'download', 'wheel', and 'install' commands.
        temp_dir = TempDirectory(kind="unpack", globally_managed=True).path

        # Map each link to the requirement that owns it. This allows us to set
        # `req.local_file_path` on the appropriate requirement after passing
        # all the links at once into BatchDownloader.
        links_to_fully_download: dict[Link, InstallRequirement] = {}
        for req in partially_downloaded_reqs:
            assert req.link
            links_to_fully_download[req.link] = req

        batch_download = self._download.batch(links_to_fully_download.keys(), temp_dir)
        for link, (filepath, _) in batch_download:
            logger.debug("Downloading link %s to %s", link, filepath)
            req = links_to_fully_download[link]
            # Record the downloaded file path so wheel reqs can extract a Distribution
            # in .get_dist().
            req.local_file_path = filepath
            # Record that the file is downloaded so we don't do it again in
            # _prepare_linked_requirement().
            self._downloaded[req.link.url] = filepath

            # If this is an sdist, we need to unpack it after downloading, but the
            # .source_dir won't be set up until we are in _prepare_linked_requirement().
            # Add the downloaded archive to the install requirement to unpack after
            # preparing the source dir.
            if not req.is_wheel:
                req.needs_unpacked_archive(Path(filepath))

        # This step is necessary to ensure all lazy wheels are processed
        # successfully by the 'download', 'wheel', and 'install' commands.
        for req in partially_downloaded_reqs:
            self._prepare_linked_requirement(req, parallel_builds)

    def prepare_linked_requirement(
        self, req: InstallRequirement, parallel_builds: bool = False
    ) -> BaseDistribution:
        """Prepare a requirement to be obtained from req.link."""
        assert req.link
        self._log_preparing_link(req)
        with indent_log():
            # Check if the relevant file is already available
            # in the download directory
            file_path = None
            if self.download_dir is not None and req.link.is_wheel:
                hashes = self._get_linked_req_hashes(req)
                file_path = _check_download_dir(
                    req.link,
                    self.download_dir,
                    hashes,
                    # When a locally built wheel has been found in cache, we don't warn
                    # about re-downloading when the already downloaded wheel hash does
                    # not match. This is because the hash must be checked against the
                    # original link, not the cached link. It that case the already
                    # downloaded file will be removed and re-fetched from cache (which
                    # implies a hash check against the cache entry's origin.json).
                    warn_on_hash_mismatch=not req.is_wheel_from_cache,
                )

            if file_path is not None:
                # The file is already available, so mark it as downloaded
                self._downloaded[req.link.url] = file_path
            else:
                # The file is not available, attempt to fetch only metadata
                metadata_dist = self._fetch_metadata_only(req)
                if metadata_dist is not None:
                    req.needs_more_preparation = True
                    return metadata_dist

            # None of the optimizations worked, fully prepare the requirement
            return self._prepare_linked_requirement(req, parallel_builds)

    def prepare_linked_requirements_more(
        self, reqs: Iterable[InstallRequirement], parallel_builds: bool = False
    ) -> None:
        """Prepare linked requirements more, if needed."""
        reqs = [req for req in reqs if req.needs_more_preparation]
        for req in reqs:
            # Determine if any of these requirements were already downloaded.
            if self.download_dir is not None and req.link.is_wheel:
                hashes = self._get_linked_req_hashes(req)
                file_path = _check_download_dir(req.link, self.download_dir, hashes)
                if file_path is not None:
                    self._downloaded[req.link.url] = file_path
                    req.needs_more_preparation = False

        # Prepare requirements we found were already downloaded for some
        # reason. The other downloads will be completed separately.
        partially_downloaded_reqs: list[InstallRequirement] = []
        for req in reqs:
            if req.needs_more_preparation:
                partially_downloaded_reqs.append(req)
            else:
                self._prepare_linked_requirement(req, parallel_builds)

        # TODO: separate this part out from RequirementPreparer when the v1
        # resolver can be removed!
        self._complete_partial_requirements(
            partially_downloaded_reqs,
            parallel_builds=parallel_builds,
        )

    def _prepare_linked_requirement(
        self, req: InstallRequirement, parallel_builds: bool
    ) -> BaseDistribution:
        assert req.link
        link = req.link

        hashes = self._get_linked_req_hashes(req)

        if hashes and req.is_wheel_from_cache:
            assert req.download_info is not None
            assert link.is_wheel
            assert link.is_file
            # We need to verify hashes, and we have found the requirement in the cache
            # of locally built wheels.
            if (
                isinstance(req.download_info.info, ArchiveInfo)
                and req.download_info.info.hashes
                and hashes.has_one_of(req.download_info.info.hashes)
            ):
                # At this point we know the requirement was built from a hashable source
                # artifact, and we verified that the cache entry's hash of the original
                # artifact matches one of the hashes we expect. We don't verify hashes
                # against the cached wheel, because the wheel is not the original.
                hashes = None
            else:
                logger.warning(
                    "The hashes of the source archive found in cache entry "
                    "don't match, ignoring cached built wheel "
                    "and re-downloading source."
                )
                req.link = req.cached_wheel_source_link
                link = req.link

        self._ensure_link_req_src_dir(req, parallel_builds)

        if link.is_existing_dir():
            local_file = None
        elif link.url not in self._downloaded:
            try:
                local_file = unpack_url(
                    link,
                    req.source_dir,
                    self._download,
                    self.verbosity,
                    self.download_dir,
                    hashes,
                )
            except NetworkConnectionError as exc:
                raise InstallationError(
                    f"Could not install requirement {req} because of HTTP "
                    f"error {exc} for URL {link}"
                )
        else:
            file_path = self._downloaded[link.url]
            if hashes:
                hashes.check_against_path(file_path)
            local_file = File(file_path, content_type=None)

        # If download_info is set, we got it from the wheel cache.
        if req.download_info is None:
            # Editables don't go through this function (see
            # prepare_editable_requirement).
            assert not req.editable
            req.download_info = direct_url_from_link(link, req.source_dir)
            # Make sure we have a hash in download_info. If we got it as part of the
            # URL, it will have been verified and we can rely on it. Otherwise we
            # compute it from the downloaded file.
            # FIXME: https://github.com/pypa/pip/issues/11943
            if (
                isinstance(req.download_info.info, ArchiveInfo)
                and not req.download_info.info.hashes
                and local_file
            ):
                hash = hash_file(local_file.path)[0].hexdigest()
                # We populate info.hash for backward compatibility.
                # This will automatically populate info.hashes.
                req.download_info.info.hash = f"sha256={hash}"

        # For use in later processing,
        # preserve the file path on the requirement.
        if local_file:
            req.local_file_path = local_file.path

        dist = _get_prepared_distribution(
            req,
            self.build_tracker,
            self.build_env_installer,
            self.build_isolation,
            self.check_build_deps,
        )
        return dist

    def save_linked_requirement(self, req: InstallRequirement) -> None:
        assert self.download_dir is not None
        assert req.link is not None
        link = req.link
        if link.is_vcs or (link.is_existing_dir() and req.editable):
            # Make a .zip of the source_dir we already created.
            req.archive(self.download_dir)
            return

        if link.is_existing_dir():
            logger.debug(
                "Not copying link to destination directory "
                "since it is a directory: %s",
                link,
            )
            return
        if req.local_file_path is None:
            # No distribution was downloaded for this requirement.
            return

        download_location = os.path.join(self.download_dir, link.filename)
        if not os.path.exists(download_location):
            shutil.copy(req.local_file_path, download_location)
            download_path = display_path(download_location)
            logger.info("Saved %s", download_path)

    def prepare_editable_requirement(
        self,
        req: InstallRequirement,
    ) -> BaseDistribution:
        """Prepare an editable requirement."""
        assert req.editable, "cannot prepare a non-editable req as editable"

        logger.info("Obtaining %s", req)

        with indent_log():
            if self.require_hashes:
                raise InstallationError(
                    f"The editable requirement {req} cannot be installed when "
                    "requiring hashes, because there is no single file to "
                    "hash."
                )
            req.ensure_has_source_dir(self.src_dir)
            req.update_editable()
            assert req.source_dir
            req.download_info = direct_url_for_editable(req.unpacked_source_directory)

            dist = _get_prepared_distribution(
                req,
                self.build_tracker,
                self.build_env_installer,
                self.build_isolation,
                self.check_build_deps,
            )

            req.check_if_exists(self.use_user_site)

        return dist

    def prepare_installed_requirement(
        self,
        req: InstallRequirement,
        skip_reason: str,
    ) -> BaseDistribution:
        """Prepare an already-installed requirement."""
        assert req.satisfied_by, "req should have been satisfied but isn't"
        assert skip_reason is not None, (
            "did not get skip reason skipped but req.satisfied_by "
            f"is set to {req.satisfied_by}"
        )
        logger.info(
            "Requirement %s: %s (%s)", skip_reason, req, req.satisfied_by.version
        )
        with indent_log():
            if self.require_hashes:
                logger.debug(
                    "Since it is already installed, we are trusting this "
                    "package without checking its hash. To ensure a "
                    "completely repeatable environment, install into an "
                    "empty virtualenv."
                )
            return InstalledDistribution(req).get_metadata_distribution()

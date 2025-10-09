from __future__ import annotations

import functools
import logging
import os
import shutil
import sys
import uuid
import zipfile
from collections.abc import Collection, Iterable, Sequence
from optparse import Values
from pathlib import Path
from typing import Any

from pip._vendor.packaging.markers import Marker
from pip._vendor.packaging.requirements import Requirement
from pip._vendor.packaging.specifiers import SpecifierSet
from pip._vendor.packaging.utils import canonicalize_name
from pip._vendor.packaging.version import Version
from pip._vendor.packaging.version import parse as parse_version
from pip._vendor.pyproject_hooks import BuildBackendHookCaller

from pip._internal.build_env import BuildEnvironment, NoOpBuildEnvironment
from pip._internal.exceptions import InstallationError, PreviousBuildDirError
from pip._internal.locations import get_scheme
from pip._internal.metadata import (
    BaseDistribution,
    get_default_environment,
    get_directory_distribution,
    get_wheel_distribution,
)
from pip._internal.metadata.base import FilesystemWheel
from pip._internal.models.direct_url import DirectUrl
from pip._internal.models.link import Link
from pip._internal.operations.build.metadata import generate_metadata
from pip._internal.operations.build.metadata_editable import generate_editable_metadata
from pip._internal.operations.build.metadata_legacy import (
    generate_metadata as generate_metadata_legacy,
)
from pip._internal.operations.install.editable_legacy import (
    install_editable as install_editable_legacy,
)
from pip._internal.operations.install.wheel import install_wheel
from pip._internal.pyproject import load_pyproject_toml, make_pyproject_path
from pip._internal.req.req_uninstall import UninstallPathSet
from pip._internal.utils.deprecation import deprecated
from pip._internal.utils.hashes import Hashes
from pip._internal.utils.misc import (
    ConfiguredBuildBackendHookCaller,
    ask_path_exists,
    backup_dir,
    display_path,
    hide_url,
    is_installable_dir,
    redact_auth_from_requirement,
    redact_auth_from_url,
)
from pip._internal.utils.packaging import get_requirement
from pip._internal.utils.subprocess import runner_with_spinner_message
from pip._internal.utils.temp_dir import TempDirectory, tempdir_kinds
from pip._internal.utils.unpacking import unpack_file
from pip._internal.utils.virtualenv import running_under_virtualenv
from pip._internal.vcs import vcs

logger = logging.getLogger(__name__)


class InstallRequirement:
    """
    Represents something that may be installed later on, may have information
    about where to fetch the relevant requirement and also contains logic for
    installing the said requirement.
    """

    def __init__(
        self,
        req: Requirement | None,
        comes_from: str | InstallRequirement | None,
        editable: bool = False,
        link: Link | None = None,
        markers: Marker | None = None,
        use_pep517: bool | None = None,
        isolated: bool = False,
        *,
        global_options: list[str] | None = None,
        hash_options: dict[str, list[str]] | None = None,
        config_settings: dict[str, str | list[str]] | None = None,
        constraint: bool = False,
        extras: Collection[str] = (),
        user_supplied: bool = False,
        permit_editable_wheels: bool = False,
    ) -> None:
        assert req is None or isinstance(req, Requirement), req
        self.req = req
        self.comes_from = comes_from
        self.constraint = constraint
        self.editable = editable
        self.permit_editable_wheels = permit_editable_wheels

        # source_dir is the local directory where the linked requirement is
        # located, or unpacked. In case unpacking is needed, creating and
        # populating source_dir is done by the RequirementPreparer. Note this
        # is not necessarily the directory where pyproject.toml or setup.py is
        # located - that one is obtained via unpacked_source_directory.
        self.source_dir: str | None = None
        if self.editable:
            assert link
            if link.is_file:
                self.source_dir = os.path.normpath(os.path.abspath(link.file_path))

        # original_link is the direct URL that was provided by the user for the
        # requirement, either directly or via a constraints file.
        if link is None and req and req.url:
            # PEP 508 URL requirement
            link = Link(req.url)
        self.link = self.original_link = link

        # When this InstallRequirement is a wheel obtained from the cache of locally
        # built wheels, this is the source link corresponding to the cache entry, which
        # was used to download and build the cached wheel.
        self.cached_wheel_source_link: Link | None = None

        # Information about the location of the artifact that was downloaded . This
        # property is guaranteed to be set in resolver results.
        self.download_info: DirectUrl | None = None

        # Path to any downloaded or already-existing package.
        self.local_file_path: str | None = None
        if self.link and self.link.is_file:
            self.local_file_path = self.link.file_path

        if extras:
            self.extras = extras
        elif req:
            self.extras = req.extras
        else:
            self.extras = set()
        if markers is None and req:
            markers = req.marker
        self.markers = markers

        # This holds the Distribution object if this requirement is already installed.
        self.satisfied_by: BaseDistribution | None = None
        # Whether the installation process should try to uninstall an existing
        # distribution before installing this requirement.
        self.should_reinstall = False
        # Temporary build location
        self._temp_build_dir: TempDirectory | None = None
        # Set to True after successful installation
        self.install_succeeded: bool | None = None
        # Supplied options
        self.global_options = global_options if global_options else []
        self.hash_options = hash_options if hash_options else {}
        self.config_settings = config_settings
        # Set to True after successful preparation of this requirement
        self.prepared = False
        # User supplied requirement are explicitly requested for installation
        # by the user via CLI arguments or requirements files, as opposed to,
        # e.g. dependencies, extras or constraints.
        self.user_supplied = user_supplied

        self.isolated = isolated
        self.build_env: BuildEnvironment = NoOpBuildEnvironment()

        # For PEP 517, the directory where we request the project metadata
        # gets stored. We need this to pass to build_wheel, so the backend
        # can ensure that the wheel matches the metadata (see the PEP for
        # details).
        self.metadata_directory: str | None = None

        # The static build requirements (from pyproject.toml)
        self.pyproject_requires: list[str] | None = None

        # Build requirements that we will check are available
        self.requirements_to_check: list[str] = []

        # The PEP 517 backend we should use to build the project
        self.pep517_backend: BuildBackendHookCaller | None = None

        # Are we using PEP 517 for this requirement?
        # After pyproject.toml has been loaded, the only valid values are True
        # and False. Before loading, None is valid (meaning "use the default").
        # Setting an explicit value before loading pyproject.toml is supported,
        # but after loading this flag should be treated as read only.
        self.use_pep517 = use_pep517

        # If config settings are provided, enforce PEP 517.
        if self.config_settings:
            if self.use_pep517 is False:
                logger.warning(
                    "--no-use-pep517 ignored for %s "
                    "because --config-settings are specified.",
                    self,
                )
            self.use_pep517 = True

        # This requirement needs more preparation before it can be built
        self.needs_more_preparation = False

        # This requirement needs to be unpacked before it can be installed.
        self._archive_source: Path | None = None

    def __str__(self) -> str:
        if self.req:
            s = redact_auth_from_requirement(self.req)
            if self.link:
                s += f" from {redact_auth_from_url(self.link.url)}"
        elif self.link:
            s = redact_auth_from_url(self.link.url)
        else:
            s = "<InstallRequirement>"
        if self.satisfied_by is not None:
            if self.satisfied_by.location is not None:
                location = display_path(self.satisfied_by.location)
            else:
                location = "<memory>"
            s += f" in {location}"
        if self.comes_from:
            if isinstance(self.comes_from, str):
                comes_from: str | None = self.comes_from
            else:
                comes_from = self.comes_from.from_path()
            if comes_from:
                s += f" (from {comes_from})"
        return s

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} object: "
            f"{str(self)} editable={self.editable!r}>"
        )

    def format_debug(self) -> str:
        """An un-tested helper for getting state, for debugging."""
        attributes = vars(self)
        names = sorted(attributes)

        state = (f"{attr}={attributes[attr]!r}" for attr in sorted(names))
        return "<{name} object: {{{state}}}>".format(
            name=self.__class__.__name__,
            state=", ".join(state),
        )

    # Things that are valid for all kinds of requirements?
    @property
    def name(self) -> str | None:
        if self.req is None:
            return None
        return self.req.name

    @functools.cached_property
    def supports_pyproject_editable(self) -> bool:
        if not self.use_pep517:
            return False
        assert self.pep517_backend
        with self.build_env:
            runner = runner_with_spinner_message(
                "Checking if build backend supports build_editable"
            )
            with self.pep517_backend.subprocess_runner(runner):
                return "build_editable" in self.pep517_backend._supported_features()

    @property
    def specifier(self) -> SpecifierSet:
        assert self.req is not None
        return self.req.specifier

    @property
    def is_direct(self) -> bool:
        """Whether this requirement was specified as a direct URL."""
        return self.original_link is not None

    @property
    def is_pinned(self) -> bool:
        """Return whether I am pinned to an exact version.

        For example, some-package==1.2 is pinned; some-package>1.2 is not.
        """
        assert self.req is not None
        specifiers = self.req.specifier
        return len(specifiers) == 1 and next(iter(specifiers)).operator in {"==", "==="}

    def match_markers(self, extras_requested: Iterable[str] | None = None) -> bool:
        if not extras_requested:
            # Provide an extra to safely evaluate the markers
            # without matching any extra
            extras_requested = ("",)
        if self.markers is not None:
            return any(
                self.markers.evaluate({"extra": extra}) for extra in extras_requested
            )
        else:
            return True

    @property
    def has_hash_options(self) -> bool:
        """Return whether any known-good hashes are specified as options.

        These activate --require-hashes mode; hashes specified as part of a
        URL do not.

        """
        return bool(self.hash_options)

    def hashes(self, trust_internet: bool = True) -> Hashes:
        """Return a hash-comparer that considers my option- and URL-based
        hashes to be known-good.

        Hashes in URLs--ones embedded in the requirements file, not ones
        downloaded from an index server--are almost peers with ones from
        flags. They satisfy --require-hashes (whether it was implicitly or
        explicitly activated) but do not activate it. md5 and sha224 are not
        allowed in flags, which should nudge people toward good algos. We
        always OR all hashes together, even ones from URLs.

        :param trust_internet: Whether to trust URL-based (#md5=...) hashes
            downloaded from the internet, as by populate_link()

        """
        good_hashes = self.hash_options.copy()
        if trust_internet:
            link = self.link
        elif self.is_direct and self.user_supplied:
            link = self.original_link
        else:
            link = None
        if link and link.hash:
            assert link.hash_name is not None
            good_hashes.setdefault(link.hash_name, []).append(link.hash)
        return Hashes(good_hashes)

    def from_path(self) -> str | None:
        """Format a nice indicator to show where this "comes from" """
        if self.req is None:
            return None
        s = str(self.req)
        if self.comes_from:
            comes_from: str | None
            if isinstance(self.comes_from, str):
                comes_from = self.comes_from
            else:
                comes_from = self.comes_from.from_path()
            if comes_from:
                s += "->" + comes_from
        return s

    def ensure_build_location(
        self, build_dir: str, autodelete: bool, parallel_builds: bool
    ) -> str:
        assert build_dir is not None
        if self._temp_build_dir is not None:
            assert self._temp_build_dir.path
            return self._temp_build_dir.path
        if self.req is None:
            # Some systems have /tmp as a symlink which confuses custom
            # builds (such as numpy). Thus, we ensure that the real path
            # is returned.
            self._temp_build_dir = TempDirectory(
                kind=tempdir_kinds.REQ_BUILD, globally_managed=True
            )

            return self._temp_build_dir.path

        # This is the only remaining place where we manually determine the path
        # for the temporary directory. It is only needed for editables where
        # it is the value of the --src option.

        # When parallel builds are enabled, add a UUID to the build directory
        # name so multiple builds do not interfere with each other.
        dir_name: str = canonicalize_name(self.req.name)
        if parallel_builds:
            dir_name = f"{dir_name}_{uuid.uuid4().hex}"

        # FIXME: Is there a better place to create the build_dir? (hg and bzr
        # need this)
        if not os.path.exists(build_dir):
            logger.debug("Creating directory %s", build_dir)
            os.makedirs(build_dir)
        actual_build_dir = os.path.join(build_dir, dir_name)
        # `None` indicates that we respect the globally-configured deletion
        # settings, which is what we actually want when auto-deleting.
        delete_arg = None if autodelete else False
        return TempDirectory(
            path=actual_build_dir,
            delete=delete_arg,
            kind=tempdir_kinds.REQ_BUILD,
            globally_managed=True,
        ).path

    def _set_requirement(self) -> None:
        """Set requirement after generating metadata."""
        assert self.req is None
        assert self.metadata is not None
        assert self.source_dir is not None

        # Construct a Requirement object from the generated metadata
        if isinstance(parse_version(self.metadata["Version"]), Version):
            op = "=="
        else:
            op = "==="

        self.req = get_requirement(
            "".join(
                [
                    self.metadata["Name"],
                    op,
                    self.metadata["Version"],
                ]
            )
        )

    def warn_on_mismatching_name(self) -> None:
        assert self.req is not None
        metadata_name = canonicalize_name(self.metadata["Name"])
        if canonicalize_name(self.req.name) == metadata_name:
            # Everything is fine.
            return

        # If we're here, there's a mismatch. Log a warning about it.
        logger.warning(
            "Generating metadata for package %s "
            "produced metadata for project name %s. Fix your "
            "#egg=%s fragments.",
            self.name,
            metadata_name,
            self.name,
        )
        self.req = get_requirement(metadata_name)

    def check_if_exists(self, use_user_site: bool) -> None:
        """Find an installed distribution that satisfies or conflicts
        with this requirement, and set self.satisfied_by or
        self.should_reinstall appropriately.
        """
        if self.req is None:
            return
        existing_dist = get_default_environment().get_distribution(self.req.name)
        if not existing_dist:
            return

        version_compatible = self.req.specifier.contains(
            existing_dist.version,
            prereleases=True,
        )
        if not version_compatible:
            self.satisfied_by = None
            if use_user_site:
                if existing_dist.in_usersite:
                    self.should_reinstall = True
                elif running_under_virtualenv() and existing_dist.in_site_packages:
                    raise InstallationError(
                        f"Will not install to the user site because it will "
                        f"lack sys.path precedence to {existing_dist.raw_name} "
                        f"in {existing_dist.location}"
                    )
            else:
                self.should_reinstall = True
        else:
            if self.editable:
                self.should_reinstall = True
                # when installing editables, nothing pre-existing should ever
                # satisfy
                self.satisfied_by = None
            else:
                self.satisfied_by = existing_dist

    # Things valid for wheels
    @property
    def is_wheel(self) -> bool:
        if not self.link:
            return False
        return self.link.is_wheel

    @property
    def is_wheel_from_cache(self) -> bool:
        # When True, it means that this InstallRequirement is a local wheel file in the
        # cache of locally built wheels.
        return self.cached_wheel_source_link is not None

    # Things valid for sdists
    @property
    def unpacked_source_directory(self) -> str:
        assert self.source_dir, f"No source dir for {self}"
        return os.path.join(
            self.source_dir, self.link and self.link.subdirectory_fragment or ""
        )

    @property
    def setup_py_path(self) -> str:
        assert self.source_dir, f"No source dir for {self}"
        setup_py = os.path.join(self.unpacked_source_directory, "setup.py")

        return setup_py

    @property
    def setup_cfg_path(self) -> str:
        assert self.source_dir, f"No source dir for {self}"
        setup_cfg = os.path.join(self.unpacked_source_directory, "setup.cfg")

        return setup_cfg

    @property
    def pyproject_toml_path(self) -> str:
        assert self.source_dir, f"No source dir for {self}"
        return make_pyproject_path(self.unpacked_source_directory)

    def load_pyproject_toml(self) -> None:
        """Load the pyproject.toml file.

        After calling this routine, all of the attributes related to PEP 517
        processing for this requirement have been set. In particular, the
        use_pep517 attribute can be used to determine whether we should
        follow the PEP 517 or legacy (setup.py) code path.
        """
        pyproject_toml_data = load_pyproject_toml(
            self.use_pep517, self.pyproject_toml_path, self.setup_py_path, str(self)
        )

        if pyproject_toml_data is None:
            assert not self.config_settings
            self.use_pep517 = False
            return

        self.use_pep517 = True
        requires, backend, check, backend_path = pyproject_toml_data
        self.requirements_to_check = check
        self.pyproject_requires = requires
        self.pep517_backend = ConfiguredBuildBackendHookCaller(
            self,
            self.unpacked_source_directory,
            backend,
            backend_path=backend_path,
        )

    def isolated_editable_sanity_check(self) -> None:
        """Check that an editable requirement if valid for use with PEP 517/518.

        This verifies that an editable that has a pyproject.toml either supports PEP 660
        or as a setup.py or a setup.cfg
        """
        if (
            self.editable
            and self.use_pep517
            and not self.supports_pyproject_editable
            and not os.path.isfile(self.setup_py_path)
            and not os.path.isfile(self.setup_cfg_path)
        ):
            raise InstallationError(
                f"Project {self} has a 'pyproject.toml' and its build "
                f"backend is missing the 'build_editable' hook. Since it does not "
                f"have a 'setup.py' nor a 'setup.cfg', "
                f"it cannot be installed in editable mode. "
                f"Consider using a build backend that supports PEP 660."
            )

    def prepare_metadata(self) -> None:
        """Ensure that project metadata is available.

        Under PEP 517 and PEP 660, call the backend hook to prepare the metadata.
        Under legacy processing, call setup.py egg-info.
        """
        assert self.source_dir, f"No source dir for {self}"
        details = self.name or f"from {self.link}"

        if self.use_pep517:
            assert self.pep517_backend is not None
            if (
                self.editable
                and self.permit_editable_wheels
                and self.supports_pyproject_editable
            ):
                self.metadata_directory = generate_editable_metadata(
                    build_env=self.build_env,
                    backend=self.pep517_backend,
                    details=details,
                )
            else:
                self.metadata_directory = generate_metadata(
                    build_env=self.build_env,
                    backend=self.pep517_backend,
                    details=details,
                )
        else:
            self.metadata_directory = generate_metadata_legacy(
                build_env=self.build_env,
                setup_py_path=self.setup_py_path,
                source_dir=self.unpacked_source_directory,
                isolated=self.isolated,
                details=details,
            )

        # Act on the newly generated metadata, based on the name and version.
        if not self.name:
            self._set_requirement()
        else:
            self.warn_on_mismatching_name()

        self.assert_source_matches_version()

    @property
    def metadata(self) -> Any:
        if not hasattr(self, "_metadata"):
            self._metadata = self.get_dist().metadata

        return self._metadata

    def get_dist(self) -> BaseDistribution:
        if self.metadata_directory:
            return get_directory_distribution(self.metadata_directory)
        elif self.local_file_path and self.is_wheel:
            assert self.req is not None
            return get_wheel_distribution(
                FilesystemWheel(self.local_file_path),
                canonicalize_name(self.req.name),
            )
        raise AssertionError(
            f"InstallRequirement {self} has no metadata directory and no wheel: "
            f"can't make a distribution."
        )

    def assert_source_matches_version(self) -> None:
        assert self.source_dir, f"No source dir for {self}"
        version = self.metadata["version"]
        if self.req and self.req.specifier and version not in self.req.specifier:
            logger.warning(
                "Requested %s, but installing version %s",
                self,
                version,
            )
        else:
            logger.debug(
                "Source in %s has version %s, which satisfies requirement %s",
                display_path(self.source_dir),
                version,
                self,
            )

    # For both source distributions and editables
    def ensure_has_source_dir(
        self,
        parent_dir: str,
        autodelete: bool = False,
        parallel_builds: bool = False,
    ) -> None:
        """Ensure that a source_dir is set.

        This will create a temporary build dir if the name of the requirement
        isn't known yet.

        :param parent_dir: The ideal pip parent_dir for the source_dir.
            Generally src_dir for editables and build_dir for sdists.
        :return: self.source_dir
        """
        if self.source_dir is None:
            self.source_dir = self.ensure_build_location(
                parent_dir,
                autodelete=autodelete,
                parallel_builds=parallel_builds,
            )

    def needs_unpacked_archive(self, archive_source: Path) -> None:
        assert self._archive_source is None
        self._archive_source = archive_source

    def ensure_pristine_source_checkout(self) -> None:
        """Ensure the source directory has not yet been built in."""
        assert self.source_dir is not None
        if self._archive_source is not None:
            unpack_file(str(self._archive_source), self.source_dir)
        elif is_installable_dir(self.source_dir):
            # If a checkout exists, it's unwise to keep going.
            # version inconsistencies are logged later, but do not fail
            # the installation.
            raise PreviousBuildDirError(
                f"pip can't proceed with requirements '{self}' due to a "
                f"pre-existing build directory ({self.source_dir}). This is likely "
                "due to a previous installation that failed . pip is "
                "being responsible and not assuming it can delete this. "
                "Please delete it and try again."
            )

    # For editable installations
    def update_editable(self) -> None:
        if not self.link:
            logger.debug(
                "Cannot update repository at %s; repository location is unknown",
                self.source_dir,
            )
            return
        assert self.editable
        assert self.source_dir
        if self.link.scheme == "file":
            # Static paths don't get updated
            return
        vcs_backend = vcs.get_backend_for_scheme(self.link.scheme)
        # Editable requirements are validated in Requirement constructors.
        # So here, if it's neither a path nor a valid VCS URL, it's a bug.
        assert vcs_backend, f"Unsupported VCS URL {self.link.url}"
        hidden_url = hide_url(self.link.url)
        vcs_backend.obtain(self.source_dir, url=hidden_url, verbosity=0)

    # Top-level Actions
    def uninstall(
        self, auto_confirm: bool = False, verbose: bool = False
    ) -> UninstallPathSet | None:
        """
        Uninstall the distribution currently satisfying this requirement.

        Prompts before removing or modifying files unless
        ``auto_confirm`` is True.

        Refuses to delete or modify files outside of ``sys.prefix`` -
        thus uninstallation within a virtual environment can only
        modify that virtual environment, even if the virtualenv is
        linked to global site-packages.

        """
        assert self.req
        dist = get_default_environment().get_distribution(self.req.name)
        if not dist:
            logger.warning("Skipping %s as it is not installed.", self.name)
            return None
        logger.info("Found existing installation: %s", dist)

        uninstalled_pathset = UninstallPathSet.from_dist(dist)
        uninstalled_pathset.remove(auto_confirm, verbose)
        return uninstalled_pathset

    def _get_archive_name(self, path: str, parentdir: str, rootdir: str) -> str:
        def _clean_zip_name(name: str, prefix: str) -> str:
            assert name.startswith(
                prefix + os.path.sep
            ), f"name {name!r} doesn't start with prefix {prefix!r}"
            name = name[len(prefix) + 1 :]
            name = name.replace(os.path.sep, "/")
            return name

        assert self.req is not None
        path = os.path.join(parentdir, path)
        name = _clean_zip_name(path, rootdir)
        return self.req.name + "/" + name

    def archive(self, build_dir: str | None) -> None:
        """Saves archive to provided build_dir.

        Used for saving downloaded VCS requirements as part of `pip download`.
        """
        assert self.source_dir
        if build_dir is None:
            return

        create_archive = True
        archive_name = "{}-{}.zip".format(self.name, self.metadata["version"])
        archive_path = os.path.join(build_dir, archive_name)

        if os.path.exists(archive_path):
            response = ask_path_exists(
                f"The file {display_path(archive_path)} exists. (i)gnore, (w)ipe, "
                "(b)ackup, (a)bort ",
                ("i", "w", "b", "a"),
            )
            if response == "i":
                create_archive = False
            elif response == "w":
                logger.warning("Deleting %s", display_path(archive_path))
                os.remove(archive_path)
            elif response == "b":
                dest_file = backup_dir(archive_path)
                logger.warning(
                    "Backing up %s to %s",
                    display_path(archive_path),
                    display_path(dest_file),
                )
                shutil.move(archive_path, dest_file)
            elif response == "a":
                sys.exit(-1)

        if not create_archive:
            return

        zip_output = zipfile.ZipFile(
            archive_path,
            "w",
            zipfile.ZIP_DEFLATED,
            allowZip64=True,
        )
        with zip_output:
            dir = os.path.normcase(os.path.abspath(self.unpacked_source_directory))
            for dirpath, dirnames, filenames in os.walk(dir):
                for dirname in dirnames:
                    dir_arcname = self._get_archive_name(
                        dirname,
                        parentdir=dirpath,
                        rootdir=dir,
                    )
                    zipdir = zipfile.ZipInfo(dir_arcname + "/")
                    zipdir.external_attr = 0x1ED << 16  # 0o755
                    zip_output.writestr(zipdir, "")
                for filename in filenames:
                    file_arcname = self._get_archive_name(
                        filename,
                        parentdir=dirpath,
                        rootdir=dir,
                    )
                    filename = os.path.join(dirpath, filename)
                    zip_output.write(filename, file_arcname)

        logger.info("Saved %s", display_path(archive_path))

    def install(
        self,
        global_options: Sequence[str] | None = None,
        root: str | None = None,
        home: str | None = None,
        prefix: str | None = None,
        warn_script_location: bool = True,
        use_user_site: bool = False,
        pycompile: bool = True,
    ) -> None:
        assert self.req is not None
        scheme = get_scheme(
            self.req.name,
            user=use_user_site,
            home=home,
            root=root,
            isolated=self.isolated,
            prefix=prefix,
        )

        if self.editable and not self.is_wheel:
            deprecated(
                reason=(
                    f"Legacy editable install of {self} (setup.py develop) "
                    "is deprecated."
                ),
                replacement=(
                    "to add a pyproject.toml or enable --use-pep517, "
                    "and use setuptools >= 64. "
                    "If the resulting installation is not behaving as expected, "
                    "try using --config-settings editable_mode=compat. "
                    "Please consult the setuptools documentation for more information"
                ),
                gone_in="25.3",
                issue=11457,
            )
            if self.config_settings:
                logger.warning(
                    "--config-settings ignored for legacy editable install of %s. "
                    "Consider upgrading to a version of setuptools "
                    "that supports PEP 660 (>= 64).",
                    self,
                )
            install_editable_legacy(
                global_options=global_options if global_options is not None else [],
                prefix=prefix,
                home=home,
                use_user_site=use_user_site,
                name=self.req.name,
                setup_py_path=self.setup_py_path,
                isolated=self.isolated,
                build_env=self.build_env,
                unpacked_source_directory=self.unpacked_source_directory,
            )
            self.install_succeeded = True
            return

        assert self.is_wheel
        assert self.local_file_path

        install_wheel(
            self.req.name,
            self.local_file_path,
            scheme=scheme,
            req_description=str(self.req),
            pycompile=pycompile,
            warn_script_location=warn_script_location,
            direct_url=self.download_info if self.is_direct else None,
            requested=self.user_supplied,
        )
        self.install_succeeded = True


def check_invalid_constraint_type(req: InstallRequirement) -> str:
    # Check for unsupported forms
    problem = ""
    if not req.name:
        problem = "Unnamed requirements are not allowed as constraints"
    elif req.editable:
        problem = "Editable requirements are not allowed as constraints"
    elif req.extras:
        problem = "Constraints cannot have extras"

    if problem:
        deprecated(
            reason=(
                "Constraints are only allowed to take the form of a package "
                "name and a version specifier. Other forms were originally "
                "permitted as an accident of the implementation, but were "
                "undocumented. The new implementation of the resolver no "
                "longer supports these forms."
            ),
            replacement="replacing the constraint with a requirement",
            # No plan yet for when the new resolver becomes default
            gone_in=None,
            issue=8210,
        )

    return problem


def _has_option(options: Values, reqs: list[InstallRequirement], option: str) -> bool:
    if getattr(options, option, None):
        return True
    for req in reqs:
        if getattr(req, option, None):
            return True
    return False


def check_legacy_setup_py_options(
    options: Values,
    reqs: list[InstallRequirement],
) -> None:
    has_build_options = _has_option(options, reqs, "build_options")
    has_global_options = _has_option(options, reqs, "global_options")
    if has_build_options or has_global_options:
        deprecated(
            reason="--build-option and --global-option are deprecated.",
            issue=11859,
            replacement="to use --config-settings",
            gone_in="25.3",
        )
        logger.warning(
            "Implying --no-binary=:all: due to the presence of "
            "--build-option / --global-option. "
        )
        options.format_control.disallow_binaries()

"""Orchestrator for building wheels from InstallRequirements."""

from __future__ import annotations

import logging
import os.path
import re
import shutil
from collections.abc import Iterable

from pip._vendor.packaging.utils import canonicalize_name, canonicalize_version
from pip._vendor.packaging.version import InvalidVersion, Version

from pip._internal.cache import WheelCache
from pip._internal.exceptions import InvalidWheelFilename, UnsupportedWheel
from pip._internal.metadata import FilesystemWheel, get_wheel_distribution
from pip._internal.models.link import Link
from pip._internal.models.wheel import Wheel
from pip._internal.operations.build.wheel import build_wheel_pep517
from pip._internal.operations.build.wheel_editable import build_wheel_editable
from pip._internal.operations.build.wheel_legacy import build_wheel_legacy
from pip._internal.req.req_install import InstallRequirement
from pip._internal.utils.logging import indent_log
from pip._internal.utils.misc import ensure_dir, hash_file
from pip._internal.utils.setuptools_build import make_setuptools_clean_args
from pip._internal.utils.subprocess import call_subprocess
from pip._internal.utils.temp_dir import TempDirectory
from pip._internal.utils.urls import path_to_url
from pip._internal.vcs import vcs

logger = logging.getLogger(__name__)

_egg_info_re = re.compile(r"([a-z0-9_.]+)-([a-z0-9_.!+-]+)", re.IGNORECASE)

BuildResult = tuple[list[InstallRequirement], list[InstallRequirement]]


def _contains_egg_info(s: str) -> bool:
    """Determine whether the string looks like an egg_info.

    :param s: The string to parse. E.g. foo-2.1
    """
    return bool(_egg_info_re.search(s))


def _should_build(
    req: InstallRequirement,
) -> bool:
    """Return whether an InstallRequirement should be built into a wheel."""
    assert not req.constraint

    if req.is_wheel:
        return False

    assert req.source_dir

    if req.editable:
        # we only build PEP 660 editable requirements
        return req.supports_pyproject_editable

    return True


def should_build_for_install_command(
    req: InstallRequirement,
) -> bool:
    return _should_build(req)


def _should_cache(
    req: InstallRequirement,
) -> bool | None:
    """
    Return whether a built InstallRequirement can be stored in the persistent
    wheel cache, assuming the wheel cache is available, and _should_build()
    has determined a wheel needs to be built.
    """
    if req.editable or not req.source_dir:
        # never cache editable requirements
        return False

    if req.link and req.link.is_vcs:
        # VCS checkout. Do not cache
        # unless it points to an immutable commit hash.
        assert not req.editable
        assert req.source_dir
        vcs_backend = vcs.get_backend_for_scheme(req.link.scheme)
        assert vcs_backend
        if vcs_backend.is_immutable_rev_checkout(req.link.url, req.source_dir):
            return True
        return False

    assert req.link
    base, ext = req.link.splitext()
    if _contains_egg_info(base):
        return True

    # Otherwise, do not cache.
    return False


def _get_cache_dir(
    req: InstallRequirement,
    wheel_cache: WheelCache,
) -> str:
    """Return the persistent or temporary cache directory where the built
    wheel need to be stored.
    """
    cache_available = bool(wheel_cache.cache_dir)
    assert req.link
    if cache_available and _should_cache(req):
        cache_dir = wheel_cache.get_path_for_link(req.link)
    else:
        cache_dir = wheel_cache.get_ephem_path_for_link(req.link)
    return cache_dir


def _verify_one(req: InstallRequirement, wheel_path: str) -> None:
    canonical_name = canonicalize_name(req.name or "")
    w = Wheel(os.path.basename(wheel_path))
    if canonicalize_name(w.name) != canonical_name:
        raise InvalidWheelFilename(
            f"Wheel has unexpected file name: expected {canonical_name!r}, "
            f"got {w.name!r}",
        )
    dist = get_wheel_distribution(FilesystemWheel(wheel_path), canonical_name)
    dist_verstr = str(dist.version)
    if canonicalize_version(dist_verstr) != canonicalize_version(w.version):
        raise InvalidWheelFilename(
            f"Wheel has unexpected file name: expected {dist_verstr!r}, "
            f"got {w.version!r}",
        )
    metadata_version_value = dist.metadata_version
    if metadata_version_value is None:
        raise UnsupportedWheel("Missing Metadata-Version")
    try:
        metadata_version = Version(metadata_version_value)
    except InvalidVersion:
        msg = f"Invalid Metadata-Version: {metadata_version_value}"
        raise UnsupportedWheel(msg)
    if metadata_version >= Version("1.2") and not isinstance(dist.version, Version):
        raise UnsupportedWheel(
            f"Metadata 1.2 mandates PEP 440 version, but {dist_verstr!r} is not"
        )


def _build_one(
    req: InstallRequirement,
    output_dir: str,
    verify: bool,
    build_options: list[str],
    global_options: list[str],
    editable: bool,
) -> str | None:
    """Build one wheel.

    :return: The filename of the built wheel, or None if the build failed.
    """
    artifact = "editable" if editable else "wheel"
    try:
        ensure_dir(output_dir)
    except OSError as e:
        logger.warning(
            "Building %s for %s failed: %s",
            artifact,
            req.name,
            e,
        )
        return None

    # Install build deps into temporary directory (PEP 518)
    with req.build_env:
        wheel_path = _build_one_inside_env(
            req, output_dir, build_options, global_options, editable
        )
    if wheel_path and verify:
        try:
            _verify_one(req, wheel_path)
        except (InvalidWheelFilename, UnsupportedWheel) as e:
            logger.warning("Built %s for %s is invalid: %s", artifact, req.name, e)
            return None
    return wheel_path


def _build_one_inside_env(
    req: InstallRequirement,
    output_dir: str,
    build_options: list[str],
    global_options: list[str],
    editable: bool,
) -> str | None:
    with TempDirectory(kind="wheel") as temp_dir:
        assert req.name
        if req.use_pep517:
            assert req.metadata_directory
            assert req.pep517_backend
            if global_options:
                logger.warning(
                    "Ignoring --global-option when building %s using PEP 517", req.name
                )
            if build_options:
                logger.warning(
                    "Ignoring --build-option when building %s using PEP 517", req.name
                )
            if editable:
                wheel_path = build_wheel_editable(
                    name=req.name,
                    backend=req.pep517_backend,
                    metadata_directory=req.metadata_directory,
                    tempd=temp_dir.path,
                )
            else:
                wheel_path = build_wheel_pep517(
                    name=req.name,
                    backend=req.pep517_backend,
                    metadata_directory=req.metadata_directory,
                    tempd=temp_dir.path,
                )
        else:
            wheel_path = build_wheel_legacy(
                name=req.name,
                setup_py_path=req.setup_py_path,
                source_dir=req.unpacked_source_directory,
                global_options=global_options,
                build_options=build_options,
                tempd=temp_dir.path,
            )

        if wheel_path is not None:
            wheel_name = os.path.basename(wheel_path)
            dest_path = os.path.join(output_dir, wheel_name)
            try:
                wheel_hash, length = hash_file(wheel_path)
                shutil.move(wheel_path, dest_path)
                logger.info(
                    "Created wheel for %s: filename=%s size=%d sha256=%s",
                    req.name,
                    wheel_name,
                    length,
                    wheel_hash.hexdigest(),
                )
                logger.info("Stored in directory: %s", output_dir)
                return dest_path
            except Exception as e:
                logger.warning(
                    "Building wheel for %s failed: %s",
                    req.name,
                    e,
                )
        # Ignore return, we can't do anything else useful.
        if not req.use_pep517:
            _clean_one_legacy(req, global_options)
        return None


def _clean_one_legacy(req: InstallRequirement, global_options: list[str]) -> bool:
    clean_args = make_setuptools_clean_args(
        req.setup_py_path,
        global_options=global_options,
    )

    logger.info("Running setup.py clean for %s", req.name)
    try:
        call_subprocess(
            clean_args, command_desc="python setup.py clean", cwd=req.source_dir
        )
        return True
    except Exception:
        logger.error("Failed cleaning build dir for %s", req.name)
        return False


def build(
    requirements: Iterable[InstallRequirement],
    wheel_cache: WheelCache,
    verify: bool,
    build_options: list[str],
    global_options: list[str],
) -> BuildResult:
    """Build wheels.

    :return: The list of InstallRequirement that succeeded to build and
        the list of InstallRequirement that failed to build.
    """
    if not requirements:
        return [], []

    # Build the wheels.
    logger.info(
        "Building wheels for collected packages: %s",
        ", ".join(req.name for req in requirements),  # type: ignore
    )

    with indent_log():
        build_successes, build_failures = [], []
        for req in requirements:
            assert req.name
            cache_dir = _get_cache_dir(req, wheel_cache)
            wheel_file = _build_one(
                req,
                cache_dir,
                verify,
                build_options,
                global_options,
                req.editable and req.permit_editable_wheels,
            )
            if wheel_file:
                # Record the download origin in the cache
                if req.download_info is not None:
                    # download_info is guaranteed to be set because when we build an
                    # InstallRequirement it has been through the preparer before, but
                    # let's be cautious.
                    wheel_cache.record_download_origin(cache_dir, req.download_info)
                # Update the link for this.
                req.link = Link(path_to_url(wheel_file))
                req.local_file_path = req.link.file_path
                assert req.link.is_wheel
                build_successes.append(req)
            else:
                build_failures.append(req)

    # notify success/failure
    if build_successes:
        logger.info(
            "Successfully built %s",
            " ".join([req.name for req in build_successes]),  # type: ignore
        )
    if build_failures:
        logger.info(
            "Failed to build %s",
            " ".join([req.name for req in build_failures]),  # type: ignore
        )
    # Return a list of requirements that failed to build
    return build_successes, build_failures

"""Support functions for working with wheel files."""

import logging
from email.message import Message
from email.parser import Parser
from zipfile import BadZipFile, ZipFile

from pip._vendor.packaging.utils import canonicalize_name

from pip._internal.exceptions import UnsupportedWheel

VERSION_COMPATIBLE = (1, 0)


logger = logging.getLogger(__name__)


def parse_wheel(wheel_zip: ZipFile, name: str) -> tuple[str, Message]:
    """Extract information from the provided wheel, ensuring it meets basic
    standards.

    Returns the name of the .dist-info directory and the parsed WHEEL metadata.
    """
    try:
        info_dir = wheel_dist_info_dir(wheel_zip, name)
        metadata = wheel_metadata(wheel_zip, info_dir)
        version = wheel_version(metadata)
    except UnsupportedWheel as e:
        raise UnsupportedWheel(f"{name} has an invalid wheel, {e}")

    check_compatibility(version, name)

    return info_dir, metadata


def wheel_dist_info_dir(source: ZipFile, name: str) -> str:
    """Returns the name of the contained .dist-info directory.

    Raises AssertionError or UnsupportedWheel if not found, >1 found, or
    it doesn't match the provided name.
    """
    # Zip file path separators must be /
    subdirs = {p.split("/", 1)[0] for p in source.namelist()}

    info_dirs = [s for s in subdirs if s.endswith(".dist-info")]

    if not info_dirs:
        raise UnsupportedWheel(".dist-info directory not found")

    if len(info_dirs) > 1:
        raise UnsupportedWheel(
            "multiple .dist-info directories found: {}".format(", ".join(info_dirs))
        )

    info_dir = info_dirs[0]

    info_dir_name = canonicalize_name(info_dir)
    canonical_name = canonicalize_name(name)
    if not info_dir_name.startswith(canonical_name):
        raise UnsupportedWheel(
            f".dist-info directory {info_dir!r} does not start with {canonical_name!r}"
        )

    return info_dir


def read_wheel_metadata_file(source: ZipFile, path: str) -> bytes:
    try:
        return source.read(path)
        # BadZipFile for general corruption, KeyError for missing entry,
        # and RuntimeError for password-protected files
    except (BadZipFile, KeyError, RuntimeError) as e:
        raise UnsupportedWheel(f"could not read {path!r} file: {e!r}")


def wheel_metadata(source: ZipFile, dist_info_dir: str) -> Message:
    """Return the WHEEL metadata of an extracted wheel, if possible.
    Otherwise, raise UnsupportedWheel.
    """
    path = f"{dist_info_dir}/WHEEL"
    # Zip file path separators must be /
    wheel_contents = read_wheel_metadata_file(source, path)

    try:
        wheel_text = wheel_contents.decode()
    except UnicodeDecodeError as e:
        raise UnsupportedWheel(f"error decoding {path!r}: {e!r}")

    # FeedParser (used by Parser) does not raise any exceptions. The returned
    # message may have .defects populated, but for backwards-compatibility we
    # currently ignore them.
    return Parser().parsestr(wheel_text)


def wheel_version(wheel_data: Message) -> tuple[int, ...]:
    """Given WHEEL metadata, return the parsed Wheel-Version.
    Otherwise, raise UnsupportedWheel.
    """
    version_text = wheel_data["Wheel-Version"]
    if version_text is None:
        raise UnsupportedWheel("WHEEL is missing Wheel-Version")

    version = version_text.strip()

    try:
        return tuple(map(int, version.split(".")))
    except ValueError:
        raise UnsupportedWheel(f"invalid Wheel-Version: {version!r}")


def check_compatibility(version: tuple[int, ...], name: str) -> None:
    """Raises errors or warns if called with an incompatible Wheel-Version.

    pip should refuse to install a Wheel-Version that's a major series
    ahead of what it's compatible with (e.g 2.0 > 1.1); and warn when
    installing a version only minor version ahead (e.g 1.2 > 1.1).

    version: a 2-tuple representing a Wheel-Version (Major, Minor)
    name: name of wheel or package to raise exception about

    :raises UnsupportedWheel: when an incompatible Wheel-Version is given
    """
    if version[0] > VERSION_COMPATIBLE[0]:
        raise UnsupportedWheel(
            "{}'s Wheel-Version ({}) is not compatible with this version "
            "of pip".format(name, ".".join(map(str, version)))
        )
    elif version > VERSION_COMPATIBLE:
        logger.warning(
            "Installing from a newer Wheel-Version (%s)",
            ".".join(map(str, version)),
        )

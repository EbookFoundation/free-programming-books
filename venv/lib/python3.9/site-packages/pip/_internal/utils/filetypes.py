"""Filetype information."""

from pip._internal.utils.misc import splitext

WHEEL_EXTENSION = ".whl"
BZ2_EXTENSIONS: tuple[str, ...] = (".tar.bz2", ".tbz")
XZ_EXTENSIONS: tuple[str, ...] = (
    ".tar.xz",
    ".txz",
    ".tlz",
    ".tar.lz",
    ".tar.lzma",
)
ZIP_EXTENSIONS: tuple[str, ...] = (".zip", WHEEL_EXTENSION)
TAR_EXTENSIONS: tuple[str, ...] = (".tar.gz", ".tgz", ".tar")
ARCHIVE_EXTENSIONS = ZIP_EXTENSIONS + BZ2_EXTENSIONS + TAR_EXTENSIONS + XZ_EXTENSIONS


def is_archive_file(name: str) -> bool:
    """Return True if `name` is a considered as an archive file."""
    ext = splitext(name)[1].lower()
    if ext in ARCHIVE_EXTENSIONS:
        return True
    return False

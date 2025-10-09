"""Stuff that differs in different Python versions and platform
distributions."""

import importlib.resources
import logging
import os
import sys
from typing import IO

__all__ = ["get_path_uid", "stdlib_pkgs", "tomllib", "WINDOWS"]


logger = logging.getLogger(__name__)


def has_tls() -> bool:
    try:
        import _ssl  # noqa: F401  # ignore unused

        return True
    except ImportError:
        pass

    from pip._vendor.urllib3.util import IS_PYOPENSSL

    return IS_PYOPENSSL


def get_path_uid(path: str) -> int:
    """
    Return path's uid.

    Does not follow symlinks:
        https://github.com/pypa/pip/pull/935#discussion_r5307003

    Placed this function in compat due to differences on AIX and
    Jython, that should eventually go away.

    :raises OSError: When path is a symlink or can't be read.
    """
    if hasattr(os, "O_NOFOLLOW"):
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        file_uid = os.fstat(fd).st_uid
        os.close(fd)
    else:  # AIX and Jython
        # WARNING: time of check vulnerability, but best we can do w/o NOFOLLOW
        if not os.path.islink(path):
            # older versions of Jython don't have `os.fstat`
            file_uid = os.stat(path).st_uid
        else:
            # raise OSError for parity with os.O_NOFOLLOW above
            raise OSError(f"{path} is a symlink; Will not return uid for symlinks")
    return file_uid


# The importlib.resources.open_text function was deprecated in 3.11 with suggested
# replacement we use below.
if sys.version_info < (3, 11):
    open_text_resource = importlib.resources.open_text
else:

    def open_text_resource(
        package: str, resource: str, encoding: str = "utf-8", errors: str = "strict"
    ) -> IO[str]:
        return (importlib.resources.files(package) / resource).open(
            "r", encoding=encoding, errors=errors
        )


if sys.version_info >= (3, 11):
    import tomllib
else:
    from pip._vendor import tomli as tomllib


# packages in the stdlib that may have installation metadata, but should not be
# considered 'installed'.  this theoretically could be determined based on
# dist.location (py27:`sysconfig.get_paths()['stdlib']`,
# py26:sysconfig.get_config_vars('LIBDEST')), but fear platform variation may
# make this ineffective, so hard-coding
stdlib_pkgs = {"python", "wsgiref", "argparse"}


# windows detection, covers cpython and ironpython
WINDOWS = sys.platform.startswith("win") or (sys.platform == "cli" and os.name == "nt")

from __future__ import annotations

import functools
import os
import site
import sys
import sysconfig

from pip._internal.exceptions import InstallationError
from pip._internal.utils import appdirs
from pip._internal.utils.virtualenv import running_under_virtualenv

# Application Directories
USER_CACHE_DIR = appdirs.user_cache_dir("pip")

# FIXME doesn't account for venv linked to global site-packages
site_packages: str = sysconfig.get_path("purelib")


def get_major_minor_version() -> str:
    """
    Return the major-minor version of the current Python as a string, e.g.
    "3.7" or "3.10".
    """
    return "{}.{}".format(*sys.version_info)


def change_root(new_root: str, pathname: str) -> str:
    """Return 'pathname' with 'new_root' prepended.

    If 'pathname' is relative, this is equivalent to os.path.join(new_root, pathname).
    Otherwise, it requires making 'pathname' relative and then joining the
    two, which is tricky on DOS/Windows and Mac OS.

    This is borrowed from Python's standard library's distutils module.
    """
    if os.name == "posix":
        if not os.path.isabs(pathname):
            return os.path.join(new_root, pathname)
        else:
            return os.path.join(new_root, pathname[1:])

    elif os.name == "nt":
        (drive, path) = os.path.splitdrive(pathname)
        if path[0] == "\\":
            path = path[1:]
        return os.path.join(new_root, path)

    else:
        raise InstallationError(
            f"Unknown platform: {os.name}\n"
            "Can not change root path prefix on unknown platform."
        )


def get_src_prefix() -> str:
    if running_under_virtualenv():
        src_prefix = os.path.join(sys.prefix, "src")
    else:
        # FIXME: keep src in cwd for now (it is not a temporary folder)
        try:
            src_prefix = os.path.join(os.getcwd(), "src")
        except OSError:
            # In case the current working directory has been renamed or deleted
            sys.exit("The folder you are executing pip from can no longer be found.")

    # under macOS + virtualenv sys.prefix is not properly resolved
    # it is something like /path/to/python/bin/..
    return os.path.abspath(src_prefix)


try:
    # Use getusersitepackages if this is present, as it ensures that the
    # value is initialised properly.
    user_site: str | None = site.getusersitepackages()
except AttributeError:
    user_site = site.USER_SITE


@functools.cache
def is_osx_framework() -> bool:
    return bool(sysconfig.get_config_var("PYTHONFRAMEWORK"))

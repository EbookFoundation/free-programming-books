"""Locations where we look for configs, install stuff, etc"""

# The following comment should be removed at some point in the future.
# mypy: strict-optional=False

# If pip's going to use distutils, it should not be using the copy that setuptools
# might have injected into the environment. This is done by removing the injected
# shim, if it's injected.
#
# See https://github.com/pypa/pip/issues/8761 for the original discussion and
# rationale for why this is done within pip.
from __future__ import annotations

try:
    __import__("_distutils_hack").remove_shim()
except (ImportError, AttributeError):
    pass

import logging
import os
import sys
from distutils.cmd import Command as DistutilsCommand
from distutils.command.install import SCHEME_KEYS
from distutils.command.install import install as distutils_install_command
from distutils.sysconfig import get_python_lib

from pip._internal.models.scheme import Scheme
from pip._internal.utils.compat import WINDOWS
from pip._internal.utils.virtualenv import running_under_virtualenv

from .base import get_major_minor_version

logger = logging.getLogger(__name__)


def distutils_scheme(
    dist_name: str,
    user: bool = False,
    home: str | None = None,
    root: str | None = None,
    isolated: bool = False,
    prefix: str | None = None,
    *,
    ignore_config_files: bool = False,
) -> dict[str, str]:
    """
    Return a distutils install scheme
    """
    from distutils.dist import Distribution

    dist_args: dict[str, str | list[str]] = {"name": dist_name}
    if isolated:
        dist_args["script_args"] = ["--no-user-cfg"]

    d = Distribution(dist_args)
    if not ignore_config_files:
        try:
            d.parse_config_files()
        except UnicodeDecodeError:
            paths = d.find_config_files()
            logger.warning(
                "Ignore distutils configs in %s due to encoding errors.",
                ", ".join(os.path.basename(p) for p in paths),
            )
    obj: DistutilsCommand | None = None
    obj = d.get_command_obj("install", create=True)
    assert obj is not None
    i: distutils_install_command = obj
    # NOTE: setting user or home has the side-effect of creating the home dir
    # or user base for installations during finalize_options()
    # ideally, we'd prefer a scheme class that has no side-effects.
    assert not (user and prefix), f"user={user} prefix={prefix}"
    assert not (home and prefix), f"home={home} prefix={prefix}"
    i.user = user or i.user
    if user or home:
        i.prefix = ""
    i.prefix = prefix or i.prefix
    i.home = home or i.home
    i.root = root or i.root
    i.finalize_options()

    scheme: dict[str, str] = {}
    for key in SCHEME_KEYS:
        scheme[key] = getattr(i, "install_" + key)

    # install_lib specified in setup.cfg should install *everything*
    # into there (i.e. it takes precedence over both purelib and
    # platlib).  Note, i.install_lib is *always* set after
    # finalize_options(); we only want to override here if the user
    # has explicitly requested it hence going back to the config
    if "install_lib" in d.get_option_dict("install"):
        scheme.update({"purelib": i.install_lib, "platlib": i.install_lib})

    if running_under_virtualenv():
        if home:
            prefix = home
        elif user:
            prefix = i.install_userbase
        else:
            prefix = i.prefix
        scheme["headers"] = os.path.join(
            prefix,
            "include",
            "site",
            f"python{get_major_minor_version()}",
            dist_name,
        )

        if root is not None:
            path_no_drive = os.path.splitdrive(os.path.abspath(scheme["headers"]))[1]
            scheme["headers"] = os.path.join(root, path_no_drive[1:])

    return scheme


def get_scheme(
    dist_name: str,
    user: bool = False,
    home: str | None = None,
    root: str | None = None,
    isolated: bool = False,
    prefix: str | None = None,
) -> Scheme:
    """
    Get the "scheme" corresponding to the input parameters. The distutils
    documentation provides the context for the available schemes:
    https://docs.python.org/3/install/index.html#alternate-installation

    :param dist_name: the name of the package to retrieve the scheme for, used
        in the headers scheme path
    :param user: indicates to use the "user" scheme
    :param home: indicates to use the "home" scheme and provides the base
        directory for the same
    :param root: root under which other directories are re-based
    :param isolated: equivalent to --no-user-cfg, i.e. do not consider
        ~/.pydistutils.cfg (posix) or ~/pydistutils.cfg (non-posix) for
        scheme paths
    :param prefix: indicates to use the "prefix" scheme and provides the
        base directory for the same
    """
    scheme = distutils_scheme(dist_name, user, home, root, isolated, prefix)
    return Scheme(
        platlib=scheme["platlib"],
        purelib=scheme["purelib"],
        headers=scheme["headers"],
        scripts=scheme["scripts"],
        data=scheme["data"],
    )


def get_bin_prefix() -> str:
    # XXX: In old virtualenv versions, sys.prefix can contain '..' components,
    # so we need to call normpath to eliminate them.
    prefix = os.path.normpath(sys.prefix)
    if WINDOWS:
        bin_py = os.path.join(prefix, "Scripts")
        # buildout uses 'bin' on Windows too?
        if not os.path.exists(bin_py):
            bin_py = os.path.join(prefix, "bin")
        return bin_py
    # Forcing to use /usr/local/bin for standard macOS framework installs
    # Also log to ~/Library/Logs/ for use with the Console.app log viewer
    if sys.platform[:6] == "darwin" and prefix[:16] == "/System/Library/":
        return "/usr/local/bin"
    return os.path.join(prefix, "bin")


def get_purelib() -> str:
    return get_python_lib(plat_specific=False)


def get_platlib() -> str:
    return get_python_lib(plat_specific=True)

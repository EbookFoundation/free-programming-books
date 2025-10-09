from __future__ import annotations

import functools
import logging
import os
import pathlib
import sys
import sysconfig
from typing import Any

from pip._internal.models.scheme import SCHEME_KEYS, Scheme
from pip._internal.utils.compat import WINDOWS
from pip._internal.utils.deprecation import deprecated
from pip._internal.utils.virtualenv import running_under_virtualenv

from . import _sysconfig
from .base import (
    USER_CACHE_DIR,
    get_major_minor_version,
    get_src_prefix,
    is_osx_framework,
    site_packages,
    user_site,
)

__all__ = [
    "USER_CACHE_DIR",
    "get_bin_prefix",
    "get_bin_user",
    "get_major_minor_version",
    "get_platlib",
    "get_purelib",
    "get_scheme",
    "get_src_prefix",
    "site_packages",
    "user_site",
]


logger = logging.getLogger(__name__)


_PLATLIBDIR: str = getattr(sys, "platlibdir", "lib")

_USE_SYSCONFIG_DEFAULT = sys.version_info >= (3, 10)


def _should_use_sysconfig() -> bool:
    """This function determines the value of _USE_SYSCONFIG.

    By default, pip uses sysconfig on Python 3.10+.
    But Python distributors can override this decision by setting:
        sysconfig._PIP_USE_SYSCONFIG = True / False
    Rationale in https://github.com/pypa/pip/issues/10647

    This is a function for testability, but should be constant during any one
    run.
    """
    return bool(getattr(sysconfig, "_PIP_USE_SYSCONFIG", _USE_SYSCONFIG_DEFAULT))


_USE_SYSCONFIG = _should_use_sysconfig()

if not _USE_SYSCONFIG:
    # Import distutils lazily to avoid deprecation warnings,
    # but import it soon enough that it is in memory and available during
    # a pip reinstall.
    from . import _distutils

# Be noisy about incompatibilities if this platforms "should" be using
# sysconfig, but is explicitly opting out and using distutils instead.
if _USE_SYSCONFIG_DEFAULT and not _USE_SYSCONFIG:
    _MISMATCH_LEVEL = logging.WARNING
else:
    _MISMATCH_LEVEL = logging.DEBUG


def _looks_like_bpo_44860() -> bool:
    """The resolution to bpo-44860 will change this incorrect platlib.

    See <https://bugs.python.org/issue44860>.
    """
    from distutils.command.install import INSTALL_SCHEMES

    try:
        unix_user_platlib = INSTALL_SCHEMES["unix_user"]["platlib"]
    except KeyError:
        return False
    return unix_user_platlib == "$usersite"


def _looks_like_red_hat_patched_platlib_purelib(scheme: dict[str, str]) -> bool:
    platlib = scheme["platlib"]
    if "/$platlibdir/" in platlib:
        platlib = platlib.replace("/$platlibdir/", f"/{_PLATLIBDIR}/")
    if "/lib64/" not in platlib:
        return False
    unpatched = platlib.replace("/lib64/", "/lib/")
    return unpatched.replace("$platbase/", "$base/") == scheme["purelib"]


@functools.cache
def _looks_like_red_hat_lib() -> bool:
    """Red Hat patches platlib in unix_prefix and unix_home, but not purelib.

    This is the only way I can see to tell a Red Hat-patched Python.
    """
    from distutils.command.install import INSTALL_SCHEMES

    return all(
        k in INSTALL_SCHEMES
        and _looks_like_red_hat_patched_platlib_purelib(INSTALL_SCHEMES[k])
        for k in ("unix_prefix", "unix_home")
    )


@functools.cache
def _looks_like_debian_scheme() -> bool:
    """Debian adds two additional schemes."""
    from distutils.command.install import INSTALL_SCHEMES

    return "deb_system" in INSTALL_SCHEMES and "unix_local" in INSTALL_SCHEMES


@functools.cache
def _looks_like_red_hat_scheme() -> bool:
    """Red Hat patches ``sys.prefix`` and ``sys.exec_prefix``.

    Red Hat's ``00251-change-user-install-location.patch`` changes the install
    command's ``prefix`` and ``exec_prefix`` to append ``"/local"``. This is
    (fortunately?) done quite unconditionally, so we create a default command
    object without any configuration to detect this.
    """
    from distutils.command.install import install
    from distutils.dist import Distribution

    cmd: Any = install(Distribution())
    cmd.finalize_options()
    return (
        cmd.exec_prefix == f"{os.path.normpath(sys.exec_prefix)}/local"
        and cmd.prefix == f"{os.path.normpath(sys.prefix)}/local"
    )


@functools.cache
def _looks_like_slackware_scheme() -> bool:
    """Slackware patches sysconfig but fails to patch distutils and site.

    Slackware changes sysconfig's user scheme to use ``"lib64"`` for the lib
    path, but does not do the same to the site module.
    """
    if user_site is None:  # User-site not available.
        return False
    try:
        paths = sysconfig.get_paths(scheme="posix_user", expand=False)
    except KeyError:  # User-site not available.
        return False
    return "/lib64/" in paths["purelib"] and "/lib64/" not in user_site


@functools.cache
def _looks_like_msys2_mingw_scheme() -> bool:
    """MSYS2 patches distutils and sysconfig to use a UNIX-like scheme.

    However, MSYS2 incorrectly patches sysconfig ``nt`` scheme. The fix is
    likely going to be included in their 3.10 release, so we ignore the warning.
    See msys2/MINGW-packages#9319.

    MSYS2 MINGW's patch uses lowercase ``"lib"`` instead of the usual uppercase,
    and is missing the final ``"site-packages"``.
    """
    paths = sysconfig.get_paths("nt", expand=False)
    return all(
        "Lib" not in p and "lib" in p and not p.endswith("site-packages")
        for p in (paths[key] for key in ("platlib", "purelib"))
    )


@functools.cache
def _warn_mismatched(old: pathlib.Path, new: pathlib.Path, *, key: str) -> None:
    issue_url = "https://github.com/pypa/pip/issues/10151"
    message = (
        "Value for %s does not match. Please report this to <%s>"
        "\ndistutils: %s"
        "\nsysconfig: %s"
    )
    logger.log(_MISMATCH_LEVEL, message, key, issue_url, old, new)


def _warn_if_mismatch(old: pathlib.Path, new: pathlib.Path, *, key: str) -> bool:
    if old == new:
        return False
    _warn_mismatched(old, new, key=key)
    return True


@functools.cache
def _log_context(
    *,
    user: bool = False,
    home: str | None = None,
    root: str | None = None,
    prefix: str | None = None,
) -> None:
    parts = [
        "Additional context:",
        "user = %r",
        "home = %r",
        "root = %r",
        "prefix = %r",
    ]

    logger.log(_MISMATCH_LEVEL, "\n".join(parts), user, home, root, prefix)


def get_scheme(
    dist_name: str,
    user: bool = False,
    home: str | None = None,
    root: str | None = None,
    isolated: bool = False,
    prefix: str | None = None,
) -> Scheme:
    new = _sysconfig.get_scheme(
        dist_name,
        user=user,
        home=home,
        root=root,
        isolated=isolated,
        prefix=prefix,
    )
    if _USE_SYSCONFIG:
        return new

    old = _distutils.get_scheme(
        dist_name,
        user=user,
        home=home,
        root=root,
        isolated=isolated,
        prefix=prefix,
    )

    warning_contexts = []
    for k in SCHEME_KEYS:
        old_v = pathlib.Path(getattr(old, k))
        new_v = pathlib.Path(getattr(new, k))

        if old_v == new_v:
            continue

        # distutils incorrectly put PyPy packages under ``site-packages/python``
        # in the ``posix_home`` scheme, but PyPy devs said they expect the
        # directory name to be ``pypy`` instead. So we treat this as a bug fix
        # and not warn about it. See bpo-43307 and python/cpython#24628.
        skip_pypy_special_case = (
            sys.implementation.name == "pypy"
            and home is not None
            and k in ("platlib", "purelib")
            and old_v.parent == new_v.parent
            and old_v.name.startswith("python")
            and new_v.name.startswith("pypy")
        )
        if skip_pypy_special_case:
            continue

        # sysconfig's ``osx_framework_user`` does not include ``pythonX.Y`` in
        # the ``include`` value, but distutils's ``headers`` does. We'll let
        # CPython decide whether this is a bug or feature. See bpo-43948.
        skip_osx_framework_user_special_case = (
            user
            and is_osx_framework()
            and k == "headers"
            and old_v.parent.parent == new_v.parent
            and old_v.parent.name.startswith("python")
        )
        if skip_osx_framework_user_special_case:
            continue

        # On Red Hat and derived Linux distributions, distutils is patched to
        # use "lib64" instead of "lib" for platlib.
        if k == "platlib" and _looks_like_red_hat_lib():
            continue

        # On Python 3.9+, sysconfig's posix_user scheme sets platlib against
        # sys.platlibdir, but distutils's unix_user incorrectly continues
        # using the same $usersite for both platlib and purelib. This creates a
        # mismatch when sys.platlibdir is not "lib".
        skip_bpo_44860 = (
            user
            and k == "platlib"
            and not WINDOWS
            and _PLATLIBDIR != "lib"
            and _looks_like_bpo_44860()
        )
        if skip_bpo_44860:
            continue

        # Slackware incorrectly patches posix_user to use lib64 instead of lib,
        # but not usersite to match the location.
        skip_slackware_user_scheme = (
            user
            and k in ("platlib", "purelib")
            and not WINDOWS
            and _looks_like_slackware_scheme()
        )
        if skip_slackware_user_scheme:
            continue

        # Both Debian and Red Hat patch Python to place the system site under
        # /usr/local instead of /usr. Debian also places lib in dist-packages
        # instead of site-packages, but the /usr/local check should cover it.
        skip_linux_system_special_case = (
            not (user or home or prefix or running_under_virtualenv())
            and old_v.parts[1:3] == ("usr", "local")
            and len(new_v.parts) > 1
            and new_v.parts[1] == "usr"
            and (len(new_v.parts) < 3 or new_v.parts[2] != "local")
            and (_looks_like_red_hat_scheme() or _looks_like_debian_scheme())
        )
        if skip_linux_system_special_case:
            continue

        # MSYS2 MINGW's sysconfig patch does not include the "site-packages"
        # part of the path. This is incorrect and will be fixed in MSYS.
        skip_msys2_mingw_bug = (
            WINDOWS and k in ("platlib", "purelib") and _looks_like_msys2_mingw_scheme()
        )
        if skip_msys2_mingw_bug:
            continue

        # CPython's POSIX install script invokes pip (via ensurepip) against the
        # interpreter located in the source tree, not the install site. This
        # triggers special logic in sysconfig that's not present in distutils.
        # https://github.com/python/cpython/blob/8c21941ddaf/Lib/sysconfig.py#L178-L194
        skip_cpython_build = (
            sysconfig.is_python_build(check_home=True)
            and not WINDOWS
            and k in ("headers", "include", "platinclude")
        )
        if skip_cpython_build:
            continue

        warning_contexts.append((old_v, new_v, f"scheme.{k}"))

    if not warning_contexts:
        return old

    # Check if this path mismatch is caused by distutils config files. Those
    # files will no longer work once we switch to sysconfig, so this raises a
    # deprecation message for them.
    default_old = _distutils.distutils_scheme(
        dist_name,
        user,
        home,
        root,
        isolated,
        prefix,
        ignore_config_files=True,
    )
    if any(default_old[k] != getattr(old, k) for k in SCHEME_KEYS):
        deprecated(
            reason=(
                "Configuring installation scheme with distutils config files "
                "is deprecated and will no longer work in the near future. If you "
                "are using a Homebrew or Linuxbrew Python, please see discussion "
                "at https://github.com/Homebrew/homebrew-core/issues/76621"
            ),
            replacement=None,
            gone_in=None,
        )
        return old

    # Post warnings about this mismatch so user can report them back.
    for old_v, new_v, key in warning_contexts:
        _warn_mismatched(old_v, new_v, key=key)
    _log_context(user=user, home=home, root=root, prefix=prefix)

    return old


def get_bin_prefix() -> str:
    new = _sysconfig.get_bin_prefix()
    if _USE_SYSCONFIG:
        return new

    old = _distutils.get_bin_prefix()
    if _warn_if_mismatch(pathlib.Path(old), pathlib.Path(new), key="bin_prefix"):
        _log_context()
    return old


def get_bin_user() -> str:
    return _sysconfig.get_scheme("", user=True).scripts


def _looks_like_deb_system_dist_packages(value: str) -> bool:
    """Check if the value is Debian's APT-controlled dist-packages.

    Debian's ``distutils.sysconfig.get_python_lib()`` implementation returns the
    default package path controlled by APT, but does not patch ``sysconfig`` to
    do the same. This is similar to the bug worked around in ``get_scheme()``,
    but here the default is ``deb_system`` instead of ``unix_local``. Ultimately
    we can't do anything about this Debian bug, and this detection allows us to
    skip the warning when needed.
    """
    if not _looks_like_debian_scheme():
        return False
    if value == "/usr/lib/python3/dist-packages":
        return True
    return False


def get_purelib() -> str:
    """Return the default pure-Python lib location."""
    new = _sysconfig.get_purelib()
    if _USE_SYSCONFIG:
        return new

    old = _distutils.get_purelib()
    if _looks_like_deb_system_dist_packages(old):
        return old
    if _warn_if_mismatch(pathlib.Path(old), pathlib.Path(new), key="purelib"):
        _log_context()
    return old


def get_platlib() -> str:
    """Return the default platform-shared lib location."""
    new = _sysconfig.get_platlib()
    if _USE_SYSCONFIG:
        return new

    from . import _distutils

    old = _distutils.get_platlib()
    if _looks_like_deb_system_dist_packages(old):
        return old
    if _warn_if_mismatch(pathlib.Path(old), pathlib.Path(new), key="platlib"):
        _log_context()
    return old

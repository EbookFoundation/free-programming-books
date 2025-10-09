#!/usr/bin/env python
# Copyright 2015-2021 Nir Cohen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The ``distro`` package (``distro`` stands for Linux Distribution) provides
information about the Linux distribution it runs on, such as a reliable
machine-readable distro ID, or version information.

It is the recommended replacement for Python's original
:py:func:`platform.linux_distribution` function, but it provides much more
functionality. An alternative implementation became necessary because Python
3.5 deprecated this function, and Python 3.8 removed it altogether. Its
predecessor function :py:func:`platform.dist` was already deprecated since
Python 2.6 and removed in Python 3.8. Still, there are many cases in which
access to OS distribution information is needed. See `Python issue 1322
<https://bugs.python.org/issue1322>`_ for more information.
"""

import argparse
import json
import logging
import os
import re
import shlex
import subprocess
import sys
import warnings
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Optional,
    Sequence,
    TextIO,
    Tuple,
    Type,
)

try:
    from typing import TypedDict
except ImportError:
    # Python 3.7
    TypedDict = dict

__version__ = "1.9.0"


class VersionDict(TypedDict):
    major: str
    minor: str
    build_number: str


class InfoDict(TypedDict):
    id: str
    version: str
    version_parts: VersionDict
    like: str
    codename: str


_UNIXCONFDIR = os.environ.get("UNIXCONFDIR", "/etc")
_UNIXUSRLIBDIR = os.environ.get("UNIXUSRLIBDIR", "/usr/lib")
_OS_RELEASE_BASENAME = "os-release"

#: Translation table for normalizing the "ID" attribute defined in os-release
#: files, for use by the :func:`distro.id` method.
#:
#: * Key: Value as defined in the os-release file, translated to lower case,
#:   with blanks translated to underscores.
#:
#: * Value: Normalized value.
NORMALIZED_OS_ID = {
    "ol": "oracle",  # Oracle Linux
    "opensuse-leap": "opensuse",  # Newer versions of OpenSuSE report as opensuse-leap
}

#: Translation table for normalizing the "Distributor ID" attribute returned by
#: the lsb_release command, for use by the :func:`distro.id` method.
#:
#: * Key: Value as returned by the lsb_release command, translated to lower
#:   case, with blanks translated to underscores.
#:
#: * Value: Normalized value.
NORMALIZED_LSB_ID = {
    "enterpriseenterpriseas": "oracle",  # Oracle Enterprise Linux 4
    "enterpriseenterpriseserver": "oracle",  # Oracle Linux 5
    "redhatenterpriseworkstation": "rhel",  # RHEL 6, 7 Workstation
    "redhatenterpriseserver": "rhel",  # RHEL 6, 7 Server
    "redhatenterprisecomputenode": "rhel",  # RHEL 6 ComputeNode
}

#: Translation table for normalizing the distro ID derived from the file name
#: of distro release files, for use by the :func:`distro.id` method.
#:
#: * Key: Value as derived from the file name of a distro release file,
#:   translated to lower case, with blanks translated to underscores.
#:
#: * Value: Normalized value.
NORMALIZED_DISTRO_ID = {
    "redhat": "rhel",  # RHEL 6.x, 7.x
}

# Pattern for content of distro release file (reversed)
_DISTRO_RELEASE_CONTENT_REVERSED_PATTERN = re.compile(
    r"(?:[^)]*\)(.*)\()? *(?:STL )?([\d.+\-a-z]*\d) *(?:esaeler *)?(.+)"
)

# Pattern for base file name of distro release file
_DISTRO_RELEASE_BASENAME_PATTERN = re.compile(r"(\w+)[-_](release|version)$")

# Base file names to be looked up for if _UNIXCONFDIR is not readable.
_DISTRO_RELEASE_BASENAMES = [
    "SuSE-release",
    "altlinux-release",
    "arch-release",
    "base-release",
    "centos-release",
    "fedora-release",
    "gentoo-release",
    "mageia-release",
    "mandrake-release",
    "mandriva-release",
    "mandrivalinux-release",
    "manjaro-release",
    "oracle-release",
    "redhat-release",
    "rocky-release",
    "sl-release",
    "slackware-version",
]

# Base file names to be ignored when searching for distro release file
_DISTRO_RELEASE_IGNORE_BASENAMES = (
    "debian_version",
    "lsb-release",
    "oem-release",
    _OS_RELEASE_BASENAME,
    "system-release",
    "plesk-release",
    "iredmail-release",
    "board-release",
    "ec2_version",
)


def linux_distribution(full_distribution_name: bool = True) -> Tuple[str, str, str]:
    """
    .. deprecated:: 1.6.0

        :func:`distro.linux_distribution()` is deprecated. It should only be
        used as a compatibility shim with Python's
        :py:func:`platform.linux_distribution()`. Please use :func:`distro.id`,
        :func:`distro.version` and :func:`distro.name` instead.

    Return information about the current OS distribution as a tuple
    ``(id_name, version, codename)`` with items as follows:

    * ``id_name``:  If *full_distribution_name* is false, the result of
      :func:`distro.id`. Otherwise, the result of :func:`distro.name`.

    * ``version``:  The result of :func:`distro.version`.

    * ``codename``:  The extra item (usually in parentheses) after the
      os-release version number, or the result of :func:`distro.codename`.

    The interface of this function is compatible with the original
    :py:func:`platform.linux_distribution` function, supporting a subset of
    its parameters.

    The data it returns may not exactly be the same, because it uses more data
    sources than the original function, and that may lead to different data if
    the OS distribution is not consistent across multiple data sources it
    provides (there are indeed such distributions ...).

    Another reason for differences is the fact that the :func:`distro.id`
    method normalizes the distro ID string to a reliable machine-readable value
    for a number of popular OS distributions.
    """
    warnings.warn(
        "distro.linux_distribution() is deprecated. It should only be used as a "
        "compatibility shim with Python's platform.linux_distribution(). Please use "
        "distro.id(), distro.version() and distro.name() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _distro.linux_distribution(full_distribution_name)


def id() -> str:
    """
    Return the distro ID of the current distribution, as a
    machine-readable string.

    For a number of OS distributions, the returned distro ID value is
    *reliable*, in the sense that it is documented and that it does not change
    across releases of the distribution.

    This package maintains the following reliable distro ID values:

    ==============  =========================================
    Distro ID       Distribution
    ==============  =========================================
    "ubuntu"        Ubuntu
    "debian"        Debian
    "rhel"          RedHat Enterprise Linux
    "centos"        CentOS
    "fedora"        Fedora
    "sles"          SUSE Linux Enterprise Server
    "opensuse"      openSUSE
    "amzn"          Amazon Linux
    "arch"          Arch Linux
    "buildroot"     Buildroot
    "cloudlinux"    CloudLinux OS
    "exherbo"       Exherbo Linux
    "gentoo"        GenToo Linux
    "ibm_powerkvm"  IBM PowerKVM
    "kvmibm"        KVM for IBM z Systems
    "linuxmint"     Linux Mint
    "mageia"        Mageia
    "mandriva"      Mandriva Linux
    "parallels"     Parallels
    "pidora"        Pidora
    "raspbian"      Raspbian
    "oracle"        Oracle Linux (and Oracle Enterprise Linux)
    "scientific"    Scientific Linux
    "slackware"     Slackware
    "xenserver"     XenServer
    "openbsd"       OpenBSD
    "netbsd"        NetBSD
    "freebsd"       FreeBSD
    "midnightbsd"   MidnightBSD
    "rocky"         Rocky Linux
    "aix"           AIX
    "guix"          Guix System
    "altlinux"      ALT Linux
    ==============  =========================================

    If you have a need to get distros for reliable IDs added into this set,
    or if you find that the :func:`distro.id` function returns a different
    distro ID for one of the listed distros, please create an issue in the
    `distro issue tracker`_.

    **Lookup hierarchy and transformations:**

    First, the ID is obtained from the following sources, in the specified
    order. The first available and non-empty value is used:

    * the value of the "ID" attribute of the os-release file,

    * the value of the "Distributor ID" attribute returned by the lsb_release
      command,

    * the first part of the file name of the distro release file,

    The so determined ID value then passes the following transformations,
    before it is returned by this method:

    * it is translated to lower case,

    * blanks (which should not be there anyway) are translated to underscores,

    * a normalization of the ID is performed, based upon
      `normalization tables`_. The purpose of this normalization is to ensure
      that the ID is as reliable as possible, even across incompatible changes
      in the OS distributions. A common reason for an incompatible change is
      the addition of an os-release file, or the addition of the lsb_release
      command, with ID values that differ from what was previously determined
      from the distro release file name.
    """
    return _distro.id()


def name(pretty: bool = False) -> str:
    """
    Return the name of the current OS distribution, as a human-readable
    string.

    If *pretty* is false, the name is returned without version or codename.
    (e.g. "CentOS Linux")

    If *pretty* is true, the version and codename are appended.
    (e.g. "CentOS Linux 7.1.1503 (Core)")

    **Lookup hierarchy:**

    The name is obtained from the following sources, in the specified order.
    The first available and non-empty value is used:

    * If *pretty* is false:

      - the value of the "NAME" attribute of the os-release file,

      - the value of the "Distributor ID" attribute returned by the lsb_release
        command,

      - the value of the "<name>" field of the distro release file.

    * If *pretty* is true:

      - the value of the "PRETTY_NAME" attribute of the os-release file,

      - the value of the "Description" attribute returned by the lsb_release
        command,

      - the value of the "<name>" field of the distro release file, appended
        with the value of the pretty version ("<version_id>" and "<codename>"
        fields) of the distro release file, if available.
    """
    return _distro.name(pretty)


def version(pretty: bool = False, best: bool = False) -> str:
    """
    Return the version of the current OS distribution, as a human-readable
    string.

    If *pretty* is false, the version is returned without codename (e.g.
    "7.0").

    If *pretty* is true, the codename in parenthesis is appended, if the
    codename is non-empty (e.g. "7.0 (Maipo)").

    Some distributions provide version numbers with different precisions in
    the different sources of distribution information. Examining the different
    sources in a fixed priority order does not always yield the most precise
    version (e.g. for Debian 8.2, or CentOS 7.1).

    Some other distributions may not provide this kind of information. In these
    cases, an empty string would be returned. This behavior can be observed
    with rolling releases distributions (e.g. Arch Linux).

    The *best* parameter can be used to control the approach for the returned
    version:

    If *best* is false, the first non-empty version number in priority order of
    the examined sources is returned.

    If *best* is true, the most precise version number out of all examined
    sources is returned.

    **Lookup hierarchy:**

    In all cases, the version number is obtained from the following sources.
    If *best* is false, this order represents the priority order:

    * the value of the "VERSION_ID" attribute of the os-release file,
    * the value of the "Release" attribute returned by the lsb_release
      command,
    * the version number parsed from the "<version_id>" field of the first line
      of the distro release file,
    * the version number parsed from the "PRETTY_NAME" attribute of the
      os-release file, if it follows the format of the distro release files.
    * the version number parsed from the "Description" attribute returned by
      the lsb_release command, if it follows the format of the distro release
      files.
    """
    return _distro.version(pretty, best)


def version_parts(best: bool = False) -> Tuple[str, str, str]:
    """
    Return the version of the current OS distribution as a tuple
    ``(major, minor, build_number)`` with items as follows:

    * ``major``:  The result of :func:`distro.major_version`.

    * ``minor``:  The result of :func:`distro.minor_version`.

    * ``build_number``:  The result of :func:`distro.build_number`.

    For a description of the *best* parameter, see the :func:`distro.version`
    method.
    """
    return _distro.version_parts(best)


def major_version(best: bool = False) -> str:
    """
    Return the major version of the current OS distribution, as a string,
    if provided.
    Otherwise, the empty string is returned. The major version is the first
    part of the dot-separated version string.

    For a description of the *best* parameter, see the :func:`distro.version`
    method.
    """
    return _distro.major_version(best)


def minor_version(best: bool = False) -> str:
    """
    Return the minor version of the current OS distribution, as a string,
    if provided.
    Otherwise, the empty string is returned. The minor version is the second
    part of the dot-separated version string.

    For a description of the *best* parameter, see the :func:`distro.version`
    method.
    """
    return _distro.minor_version(best)


def build_number(best: bool = False) -> str:
    """
    Return the build number of the current OS distribution, as a string,
    if provided.
    Otherwise, the empty string is returned. The build number is the third part
    of the dot-separated version string.

    For a description of the *best* parameter, see the :func:`distro.version`
    method.
    """
    return _distro.build_number(best)


def like() -> str:
    """
    Return a space-separated list of distro IDs of distributions that are
    closely related to the current OS distribution in regards to packaging
    and programming interfaces, for example distributions the current
    distribution is a derivative from.

    **Lookup hierarchy:**

    This information item is only provided by the os-release file.
    For details, see the description of the "ID_LIKE" attribute in the
    `os-release man page
    <http://www.freedesktop.org/software/systemd/man/os-release.html>`_.
    """
    return _distro.like()


def codename() -> str:
    """
    Return the codename for the release of the current OS distribution,
    as a string.

    If the distribution does not have a codename, an empty string is returned.

    Note that the returned codename is not always really a codename. For
    example, openSUSE returns "x86_64". This function does not handle such
    cases in any special way and just returns the string it finds, if any.

    **Lookup hierarchy:**

    * the codename within the "VERSION" attribute of the os-release file, if
      provided,

    * the value of the "Codename" attribute returned by the lsb_release
      command,

    * the value of the "<codename>" field of the distro release file.
    """
    return _distro.codename()


def info(pretty: bool = False, best: bool = False) -> InfoDict:
    """
    Return certain machine-readable information items about the current OS
    distribution in a dictionary, as shown in the following example:

    .. sourcecode:: python

        {
            'id': 'rhel',
            'version': '7.0',
            'version_parts': {
                'major': '7',
                'minor': '0',
                'build_number': ''
            },
            'like': 'fedora',
            'codename': 'Maipo'
        }

    The dictionary structure and keys are always the same, regardless of which
    information items are available in the underlying data sources. The values
    for the various keys are as follows:

    * ``id``:  The result of :func:`distro.id`.

    * ``version``:  The result of :func:`distro.version`.

    * ``version_parts -> major``:  The result of :func:`distro.major_version`.

    * ``version_parts -> minor``:  The result of :func:`distro.minor_version`.

    * ``version_parts -> build_number``:  The result of
      :func:`distro.build_number`.

    * ``like``:  The result of :func:`distro.like`.

    * ``codename``:  The result of :func:`distro.codename`.

    For a description of the *pretty* and *best* parameters, see the
    :func:`distro.version` method.
    """
    return _distro.info(pretty, best)


def os_release_info() -> Dict[str, str]:
    """
    Return a dictionary containing key-value pairs for the information items
    from the os-release file data source of the current OS distribution.

    See `os-release file`_ for details about these information items.
    """
    return _distro.os_release_info()


def lsb_release_info() -> Dict[str, str]:
    """
    Return a dictionary containing key-value pairs for the information items
    from the lsb_release command data source of the current OS distribution.

    See `lsb_release command output`_ for details about these information
    items.
    """
    return _distro.lsb_release_info()


def distro_release_info() -> Dict[str, str]:
    """
    Return a dictionary containing key-value pairs for the information items
    from the distro release file data source of the current OS distribution.

    See `distro release file`_ for details about these information items.
    """
    return _distro.distro_release_info()


def uname_info() -> Dict[str, str]:
    """
    Return a dictionary containing key-value pairs for the information items
    from the distro release file data source of the current OS distribution.
    """
    return _distro.uname_info()


def os_release_attr(attribute: str) -> str:
    """
    Return a single named information item from the os-release file data source
    of the current OS distribution.

    Parameters:

    * ``attribute`` (string): Key of the information item.

    Returns:

    * (string): Value of the information item, if the item exists.
      The empty string, if the item does not exist.

    See `os-release file`_ for details about these information items.
    """
    return _distro.os_release_attr(attribute)


def lsb_release_attr(attribute: str) -> str:
    """
    Return a single named information item from the lsb_release command output
    data source of the current OS distribution.

    Parameters:

    * ``attribute`` (string): Key of the information item.

    Returns:

    * (string): Value of the information item, if the item exists.
      The empty string, if the item does not exist.

    See `lsb_release command output`_ for details about these information
    items.
    """
    return _distro.lsb_release_attr(attribute)


def distro_release_attr(attribute: str) -> str:
    """
    Return a single named information item from the distro release file
    data source of the current OS distribution.

    Parameters:

    * ``attribute`` (string): Key of the information item.

    Returns:

    * (string): Value of the information item, if the item exists.
      The empty string, if the item does not exist.

    See `distro release file`_ for details about these information items.
    """
    return _distro.distro_release_attr(attribute)


def uname_attr(attribute: str) -> str:
    """
    Return a single named information item from the distro release file
    data source of the current OS distribution.

    Parameters:

    * ``attribute`` (string): Key of the information item.

    Returns:

    * (string): Value of the information item, if the item exists.
                The empty string, if the item does not exist.
    """
    return _distro.uname_attr(attribute)


try:
    from functools import cached_property
except ImportError:
    # Python < 3.8
    class cached_property:  # type: ignore
        """A version of @property which caches the value.  On access, it calls the
        underlying function and sets the value in `__dict__` so future accesses
        will not re-call the property.
        """

        def __init__(self, f: Callable[[Any], Any]) -> None:
            self._fname = f.__name__
            self._f = f

        def __get__(self, obj: Any, owner: Type[Any]) -> Any:
            assert obj is not None, f"call {self._fname} on an instance"
            ret = obj.__dict__[self._fname] = self._f(obj)
            return ret


class LinuxDistribution:
    """
    Provides information about a OS distribution.

    This package creates a private module-global instance of this class with
    default initialization arguments, that is used by the
    `consolidated accessor functions`_ and `single source accessor functions`_.
    By using default initialization arguments, that module-global instance
    returns data about the current OS distribution (i.e. the distro this
    package runs on).

    Normally, it is not necessary to create additional instances of this class.
    However, in situations where control is needed over the exact data sources
    that are used, instances of this class can be created with a specific
    distro release file, or a specific os-release file, or without invoking the
    lsb_release command.
    """

    def __init__(
        self,
        include_lsb: Optional[bool] = None,
        os_release_file: str = "",
        distro_release_file: str = "",
        include_uname: Optional[bool] = None,
        root_dir: Optional[str] = None,
        include_oslevel: Optional[bool] = None,
    ) -> None:
        """
        The initialization method of this class gathers information from the
        available data sources, and stores that in private instance attributes.
        Subsequent access to the information items uses these private instance
        attributes, so that the data sources are read only once.

        Parameters:

        * ``include_lsb`` (bool): Controls whether the
          `lsb_release command output`_ is included as a data source.

          If the lsb_release command is not available in the program execution
          path, the data source for the lsb_release command will be empty.

        * ``os_release_file`` (string): The path name of the
          `os-release file`_ that is to be used as a data source.

          An empty string (the default) will cause the default path name to
          be used (see `os-release file`_ for details).

          If the specified or defaulted os-release file does not exist, the
          data source for the os-release file will be empty.

        * ``distro_release_file`` (string): The path name of the
          `distro release file`_ that is to be used as a data source.

          An empty string (the default) will cause a default search algorithm
          to be used (see `distro release file`_ for details).

          If the specified distro release file does not exist, or if no default
          distro release file can be found, the data source for the distro
          release file will be empty.

        * ``include_uname`` (bool): Controls whether uname command output is
          included as a data source. If the uname command is not available in
          the program execution path the data source for the uname command will
          be empty.

        * ``root_dir`` (string): The absolute path to the root directory to use
          to find distro-related information files. Note that ``include_*``
          parameters must not be enabled in combination with ``root_dir``.

        * ``include_oslevel`` (bool): Controls whether (AIX) oslevel command
          output is included as a data source. If the oslevel command is not
          available in the program execution path the data source will be
          empty.

        Public instance attributes:

        * ``os_release_file`` (string): The path name of the
          `os-release file`_ that is actually used as a data source. The
          empty string if no distro release file is used as a data source.

        * ``distro_release_file`` (string): The path name of the
          `distro release file`_ that is actually used as a data source. The
          empty string if no distro release file is used as a data source.

        * ``include_lsb`` (bool): The result of the ``include_lsb`` parameter.
          This controls whether the lsb information will be loaded.

        * ``include_uname`` (bool): The result of the ``include_uname``
          parameter. This controls whether the uname information will
          be loaded.

        * ``include_oslevel`` (bool): The result of the ``include_oslevel``
          parameter. This controls whether (AIX) oslevel information will be
          loaded.

        * ``root_dir`` (string): The result of the ``root_dir`` parameter.
          The absolute path to the root directory to use to find distro-related
          information files.

        Raises:

        * :py:exc:`ValueError`: Initialization parameters combination is not
           supported.

        * :py:exc:`OSError`: Some I/O issue with an os-release file or distro
          release file.

        * :py:exc:`UnicodeError`: A data source has unexpected characters or
          uses an unexpected encoding.
        """
        self.root_dir = root_dir
        self.etc_dir = os.path.join(root_dir, "etc") if root_dir else _UNIXCONFDIR
        self.usr_lib_dir = (
            os.path.join(root_dir, "usr/lib") if root_dir else _UNIXUSRLIBDIR
        )

        if os_release_file:
            self.os_release_file = os_release_file
        else:
            etc_dir_os_release_file = os.path.join(self.etc_dir, _OS_RELEASE_BASENAME)
            usr_lib_os_release_file = os.path.join(
                self.usr_lib_dir, _OS_RELEASE_BASENAME
            )

            # NOTE: The idea is to respect order **and** have it set
            #       at all times for API backwards compatibility.
            if os.path.isfile(etc_dir_os_release_file) or not os.path.isfile(
                usr_lib_os_release_file
            ):
                self.os_release_file = etc_dir_os_release_file
            else:
                self.os_release_file = usr_lib_os_release_file

        self.distro_release_file = distro_release_file or ""  # updated later

        is_root_dir_defined = root_dir is not None
        if is_root_dir_defined and (include_lsb or include_uname or include_oslevel):
            raise ValueError(
                "Including subprocess data sources from specific root_dir is disallowed"
                " to prevent false information"
            )
        self.include_lsb = (
            include_lsb if include_lsb is not None else not is_root_dir_defined
        )
        self.include_uname = (
            include_uname if include_uname is not None else not is_root_dir_defined
        )
        self.include_oslevel = (
            include_oslevel if include_oslevel is not None else not is_root_dir_defined
        )

    def __repr__(self) -> str:
        """Return repr of all info"""
        return (
            "LinuxDistribution("
            "os_release_file={self.os_release_file!r}, "
            "distro_release_file={self.distro_release_file!r}, "
            "include_lsb={self.include_lsb!r}, "
            "include_uname={self.include_uname!r}, "
            "include_oslevel={self.include_oslevel!r}, "
            "root_dir={self.root_dir!r}, "
            "_os_release_info={self._os_release_info!r}, "
            "_lsb_release_info={self._lsb_release_info!r}, "
            "_distro_release_info={self._distro_release_info!r}, "
            "_uname_info={self._uname_info!r}, "
            "_oslevel_info={self._oslevel_info!r})".format(self=self)
        )

    def linux_distribution(
        self, full_distribution_name: bool = True
    ) -> Tuple[str, str, str]:
        """
        Return information about the OS distribution that is compatible
        with Python's :func:`platform.linux_distribution`, supporting a subset
        of its parameters.

        For details, see :func:`distro.linux_distribution`.
        """
        return (
            self.name() if full_distribution_name else self.id(),
            self.version(),
            self._os_release_info.get("release_codename") or self.codename(),
        )

    def id(self) -> str:
        """Return the distro ID of the OS distribution, as a string.

        For details, see :func:`distro.id`.
        """

        def normalize(distro_id: str, table: Dict[str, str]) -> str:
            distro_id = distro_id.lower().replace(" ", "_")
            return table.get(distro_id, distro_id)

        distro_id = self.os_release_attr("id")
        if distro_id:
            return normalize(distro_id, NORMALIZED_OS_ID)

        distro_id = self.lsb_release_attr("distributor_id")
        if distro_id:
            return normalize(distro_id, NORMALIZED_LSB_ID)

        distro_id = self.distro_release_attr("id")
        if distro_id:
            return normalize(distro_id, NORMALIZED_DISTRO_ID)

        distro_id = self.uname_attr("id")
        if distro_id:
            return normalize(distro_id, NORMALIZED_DISTRO_ID)

        return ""

    def name(self, pretty: bool = False) -> str:
        """
        Return the name of the OS distribution, as a string.

        For details, see :func:`distro.name`.
        """
        name = (
            self.os_release_attr("name")
            or self.lsb_release_attr("distributor_id")
            or self.distro_release_attr("name")
            or self.uname_attr("name")
        )
        if pretty:
            name = self.os_release_attr("pretty_name") or self.lsb_release_attr(
                "description"
            )
            if not name:
                name = self.distro_release_attr("name") or self.uname_attr("name")
                version = self.version(pretty=True)
                if version:
                    name = f"{name} {version}"
        return name or ""

    def version(self, pretty: bool = False, best: bool = False) -> str:
        """
        Return the version of the OS distribution, as a string.

        For details, see :func:`distro.version`.
        """
        versions = [
            self.os_release_attr("version_id"),
            self.lsb_release_attr("release"),
            self.distro_release_attr("version_id"),
            self._parse_distro_release_content(self.os_release_attr("pretty_name")).get(
                "version_id", ""
            ),
            self._parse_distro_release_content(
                self.lsb_release_attr("description")
            ).get("version_id", ""),
            self.uname_attr("release"),
        ]
        if self.uname_attr("id").startswith("aix"):
            # On AIX platforms, prefer oslevel command output.
            versions.insert(0, self.oslevel_info())
        elif self.id() == "debian" or "debian" in self.like().split():
            # On Debian-like, add debian_version file content to candidates list.
            versions.append(self._debian_version)
        version = ""
        if best:
            # This algorithm uses the last version in priority order that has
            # the best precision. If the versions are not in conflict, that
            # does not matter; otherwise, using the last one instead of the
            # first one might be considered a surprise.
            for v in versions:
                if v.count(".") > version.count(".") or version == "":
                    version = v
        else:
            for v in versions:
                if v != "":
                    version = v
                    break
        if pretty and version and self.codename():
            version = f"{version} ({self.codename()})"
        return version

    def version_parts(self, best: bool = False) -> Tuple[str, str, str]:
        """
        Return the version of the OS distribution, as a tuple of version
        numbers.

        For details, see :func:`distro.version_parts`.
        """
        version_str = self.version(best=best)
        if version_str:
            version_regex = re.compile(r"(\d+)\.?(\d+)?\.?(\d+)?")
            matches = version_regex.match(version_str)
            if matches:
                major, minor, build_number = matches.groups()
                return major, minor or "", build_number or ""
        return "", "", ""

    def major_version(self, best: bool = False) -> str:
        """
        Return the major version number of the current distribution.

        For details, see :func:`distro.major_version`.
        """
        return self.version_parts(best)[0]

    def minor_version(self, best: bool = False) -> str:
        """
        Return the minor version number of the current distribution.

        For details, see :func:`distro.minor_version`.
        """
        return self.version_parts(best)[1]

    def build_number(self, best: bool = False) -> str:
        """
        Return the build number of the current distribution.

        For details, see :func:`distro.build_number`.
        """
        return self.version_parts(best)[2]

    def like(self) -> str:
        """
        Return the IDs of distributions that are like the OS distribution.

        For details, see :func:`distro.like`.
        """
        return self.os_release_attr("id_like") or ""

    def codename(self) -> str:
        """
        Return the codename of the OS distribution.

        For details, see :func:`distro.codename`.
        """
        try:
            # Handle os_release specially since distros might purposefully set
            # this to empty string to have no codename
            return self._os_release_info["codename"]
        except KeyError:
            return (
                self.lsb_release_attr("codename")
                or self.distro_release_attr("codename")
                or ""
            )

    def info(self, pretty: bool = False, best: bool = False) -> InfoDict:
        """
        Return certain machine-readable information about the OS
        distribution.

        For details, see :func:`distro.info`.
        """
        return InfoDict(
            id=self.id(),
            version=self.version(pretty, best),
            version_parts=VersionDict(
                major=self.major_version(best),
                minor=self.minor_version(best),
                build_number=self.build_number(best),
            ),
            like=self.like(),
            codename=self.codename(),
        )

    def os_release_info(self) -> Dict[str, str]:
        """
        Return a dictionary containing key-value pairs for the information
        items from the os-release file data source of the OS distribution.

        For details, see :func:`distro.os_release_info`.
        """
        return self._os_release_info

    def lsb_release_info(self) -> Dict[str, str]:
        """
        Return a dictionary containing key-value pairs for the information
        items from the lsb_release command data source of the OS
        distribution.

        For details, see :func:`distro.lsb_release_info`.
        """
        return self._lsb_release_info

    def distro_release_info(self) -> Dict[str, str]:
        """
        Return a dictionary containing key-value pairs for the information
        items from the distro release file data source of the OS
        distribution.

        For details, see :func:`distro.distro_release_info`.
        """
        return self._distro_release_info

    def uname_info(self) -> Dict[str, str]:
        """
        Return a dictionary containing key-value pairs for the information
        items from the uname command data source of the OS distribution.

        For details, see :func:`distro.uname_info`.
        """
        return self._uname_info

    def oslevel_info(self) -> str:
        """
        Return AIX' oslevel command output.
        """
        return self._oslevel_info

    def os_release_attr(self, attribute: str) -> str:
        """
        Return a single named information item from the os-release file data
        source of the OS distribution.

        For details, see :func:`distro.os_release_attr`.
        """
        return self._os_release_info.get(attribute, "")

    def lsb_release_attr(self, attribute: str) -> str:
        """
        Return a single named information item from the lsb_release command
        output data source of the OS distribution.

        For details, see :func:`distro.lsb_release_attr`.
        """
        return self._lsb_release_info.get(attribute, "")

    def distro_release_attr(self, attribute: str) -> str:
        """
        Return a single named information item from the distro release file
        data source of the OS distribution.

        For details, see :func:`distro.distro_release_attr`.
        """
        return self._distro_release_info.get(attribute, "")

    def uname_attr(self, attribute: str) -> str:
        """
        Return a single named information item from the uname command
        output data source of the OS distribution.

        For details, see :func:`distro.uname_attr`.
        """
        return self._uname_info.get(attribute, "")

    @cached_property
    def _os_release_info(self) -> Dict[str, str]:
        """
        Get the information items from the specified os-release file.

        Returns:
            A dictionary containing all information items.
        """
        if os.path.isfile(self.os_release_file):
            with open(self.os_release_file, encoding="utf-8") as release_file:
                return self._parse_os_release_content(release_file)
        return {}

    @staticmethod
    def _parse_os_release_content(lines: TextIO) -> Dict[str, str]:
        """
        Parse the lines of an os-release file.

        Parameters:

        * lines: Iterable through the lines in the os-release file.
                 Each line must be a unicode string or a UTF-8 encoded byte
                 string.

        Returns:
            A dictionary containing all information items.
        """
        props = {}
        lexer = shlex.shlex(lines, posix=True)
        lexer.whitespace_split = True

        tokens = list(lexer)
        for token in tokens:
            # At this point, all shell-like parsing has been done (i.e.
            # comments processed, quotes and backslash escape sequences
            # processed, multi-line values assembled, trailing newlines
            # stripped, etc.), so the tokens are now either:
            # * variable assignments: var=value
            # * commands or their arguments (not allowed in os-release)
            # Ignore any tokens that are not variable assignments
            if "=" in token:
                k, v = token.split("=", 1)
                props[k.lower()] = v

        if "version" in props:
            # extract release codename (if any) from version attribute
            match = re.search(r"\((\D+)\)|,\s*(\D+)", props["version"])
            if match:
                release_codename = match.group(1) or match.group(2)
                props["codename"] = props["release_codename"] = release_codename

        if "version_codename" in props:
            # os-release added a version_codename field.  Use that in
            # preference to anything else Note that some distros purposefully
            # do not have code names.  They should be setting
            # version_codename=""
            props["codename"] = props["version_codename"]
        elif "ubuntu_codename" in props:
            # Same as above but a non-standard field name used on older Ubuntus
            props["codename"] = props["ubuntu_codename"]

        return props

    @cached_property
    def _lsb_release_info(self) -> Dict[str, str]:
        """
        Get the information items from the lsb_release command output.

        Returns:
            A dictionary containing all information items.
        """
        if not self.include_lsb:
            return {}
        try:
            cmd = ("lsb_release", "-a")
            stdout = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        # Command not found or lsb_release returned error
        except (OSError, subprocess.CalledProcessError):
            return {}
        content = self._to_str(stdout).splitlines()
        return self._parse_lsb_release_content(content)

    @staticmethod
    def _parse_lsb_release_content(lines: Iterable[str]) -> Dict[str, str]:
        """
        Parse the output of the lsb_release command.

        Parameters:

        * lines: Iterable through the lines of the lsb_release output.
                 Each line must be a unicode string or a UTF-8 encoded byte
                 string.

        Returns:
            A dictionary containing all information items.
        """
        props = {}
        for line in lines:
            kv = line.strip("\n").split(":", 1)
            if len(kv) != 2:
                # Ignore lines without colon.
                continue
            k, v = kv
            props.update({k.replace(" ", "_").lower(): v.strip()})
        return props

    @cached_property
    def _uname_info(self) -> Dict[str, str]:
        if not self.include_uname:
            return {}
        try:
            cmd = ("uname", "-rs")
            stdout = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        except OSError:
            return {}
        content = self._to_str(stdout).splitlines()
        return self._parse_uname_content(content)

    @cached_property
    def _oslevel_info(self) -> str:
        if not self.include_oslevel:
            return ""
        try:
            stdout = subprocess.check_output("oslevel", stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError):
            return ""
        return self._to_str(stdout).strip()

    @cached_property
    def _debian_version(self) -> str:
        try:
            with open(
                os.path.join(self.etc_dir, "debian_version"), encoding="ascii"
            ) as fp:
                return fp.readline().rstrip()
        except FileNotFoundError:
            return ""

    @staticmethod
    def _parse_uname_content(lines: Sequence[str]) -> Dict[str, str]:
        if not lines:
            return {}
        props = {}
        match = re.search(r"^([^\s]+)\s+([\d\.]+)", lines[0].strip())
        if match:
            name, version = match.groups()

            # This is to prevent the Linux kernel version from
            # appearing as the 'best' version on otherwise
            # identifiable distributions.
            if name == "Linux":
                return {}
            props["id"] = name.lower()
            props["name"] = name
            props["release"] = version
        return props

    @staticmethod
    def _to_str(bytestring: bytes) -> str:
        encoding = sys.getfilesystemencoding()
        return bytestring.decode(encoding)

    @cached_property
    def _distro_release_info(self) -> Dict[str, str]:
        """
        Get the information items from the specified distro release file.

        Returns:
            A dictionary containing all information items.
        """
        if self.distro_release_file:
            # If it was specified, we use it and parse what we can, even if
            # its file name or content does not match the expected pattern.
            distro_info = self._parse_distro_release_file(self.distro_release_file)
            basename = os.path.basename(self.distro_release_file)
            # The file name pattern for user-specified distro release files
            # is somewhat more tolerant (compared to when searching for the
            # file), because we want to use what was specified as best as
            # possible.
            match = _DISTRO_RELEASE_BASENAME_PATTERN.match(basename)
        else:
            try:
                basenames = [
                    basename
                    for basename in os.listdir(self.etc_dir)
                    if basename not in _DISTRO_RELEASE_IGNORE_BASENAMES
                    and os.path.isfile(os.path.join(self.etc_dir, basename))
                ]
                # We sort for repeatability in cases where there are multiple
                # distro specific files; e.g. CentOS, Oracle, Enterprise all
                # containing `redhat-release` on top of their own.
                basenames.sort()
            except OSError:
                # This may occur when /etc is not readable but we can't be
                # sure about the *-release files. Check common entries of
                # /etc for information. If they turn out to not be there the
                # error is handled in `_parse_distro_release_file()`.
                basenames = _DISTRO_RELEASE_BASENAMES
            for basename in basenames:
                match = _DISTRO_RELEASE_BASENAME_PATTERN.match(basename)
                if match is None:
                    continue
                filepath = os.path.join(self.etc_dir, basename)
                distro_info = self._parse_distro_release_file(filepath)
                # The name is always present if the pattern matches.
                if "name" not in distro_info:
                    continue
                self.distro_release_file = filepath
                break
            else:  # the loop didn't "break": no candidate.
                return {}

        if match is not None:
            distro_info["id"] = match.group(1)

        # CloudLinux < 7: manually enrich info with proper id.
        if "cloudlinux" in distro_info.get("name", "").lower():
            distro_info["id"] = "cloudlinux"

        return distro_info

    def _parse_distro_release_file(self, filepath: str) -> Dict[str, str]:
        """
        Parse a distro release file.

        Parameters:

        * filepath: Path name of the distro release file.

        Returns:
            A dictionary containing all information items.
        """
        try:
            with open(filepath, encoding="utf-8") as fp:
                # Only parse the first line. For instance, on SLES there
                # are multiple lines. We don't want them...
                return self._parse_distro_release_content(fp.readline())
        except OSError:
            # Ignore not being able to read a specific, seemingly version
            # related file.
            # See https://github.com/python-distro/distro/issues/162
            return {}

    @staticmethod
    def _parse_distro_release_content(line: str) -> Dict[str, str]:
        """
        Parse a line from a distro release file.

        Parameters:
        * line: Line from the distro release file. Must be a unicode string
                or a UTF-8 encoded byte string.

        Returns:
            A dictionary containing all information items.
        """
        matches = _DISTRO_RELEASE_CONTENT_REVERSED_PATTERN.match(line.strip()[::-1])
        distro_info = {}
        if matches:
            # regexp ensures non-None
            distro_info["name"] = matches.group(3)[::-1]
            if matches.group(2):
                distro_info["version_id"] = matches.group(2)[::-1]
            if matches.group(1):
                distro_info["codename"] = matches.group(1)[::-1]
        elif line:
            distro_info["name"] = line.strip()
        return distro_info


_distro = LinuxDistribution()


def main() -> None:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    parser = argparse.ArgumentParser(description="OS distro info tool")
    parser.add_argument(
        "--json", "-j", help="Output in machine readable format", action="store_true"
    )

    parser.add_argument(
        "--root-dir",
        "-r",
        type=str,
        dest="root_dir",
        help="Path to the root filesystem directory (defaults to /)",
    )

    args = parser.parse_args()

    if args.root_dir:
        dist = LinuxDistribution(
            include_lsb=False,
            include_uname=False,
            include_oslevel=False,
            root_dir=args.root_dir,
        )
    else:
        dist = _distro

    if args.json:
        logger.info(json.dumps(dist.info(), indent=4, sort_keys=True))
    else:
        logger.info("Name: %s", dist.name(pretty=True))
        distribution_version = dist.version(pretty=True)
        logger.info("Version: %s", distribution_version)
        distribution_codename = dist.codename()
        logger.info("Codename: %s", distribution_codename)


if __name__ == "__main__":
    main()

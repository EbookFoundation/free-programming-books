# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

from __future__ import absolute_import

import distutils.util

try:
    from importlib.machinery import EXTENSION_SUFFIXES
except ImportError:  # pragma: no cover
    import imp

    EXTENSION_SUFFIXES = [x[0] for x in imp.get_suffixes()]
    del imp
import logging
import os
import platform
import re
import struct
import sys
import sysconfig
import warnings

from ._typing import TYPE_CHECKING, cast

if TYPE_CHECKING:  # pragma: no cover
    from typing import (
        Dict,
        FrozenSet,
        IO,
        Iterable,
        Iterator,
        List,
        Optional,
        Sequence,
        Tuple,
        Union,
    )

    PythonVersion = Sequence[int]
    MacVersion = Tuple[int, int]
    GlibcVersion = Tuple[int, int]


logger = logging.getLogger(__name__)

INTERPRETER_SHORT_NAMES = {
    "python": "py",  # Generic.
    "cpython": "cp",
    "pypy": "pp",
    "ironpython": "ip",
    "jython": "jy",
}  # type: Dict[str, str]


_32_BIT_INTERPRETER = sys.maxsize <= 2 ** 32


class Tag(object):
    """
    A representation of the tag triple for a wheel.

    Instances are considered immutable and thus are hashable. Equality checking
    is also supported.
    """

    __slots__ = ["_interpreter", "_abi", "_platform"]

    def __init__(self, interpreter, abi, platform):
        # type: (str, str, str) -> None
        self._interpreter = interpreter.lower()
        self._abi = abi.lower()
        self._platform = platform.lower()

    @property
    def interpreter(self):
        # type: () -> str
        return self._interpreter

    @property
    def abi(self):
        # type: () -> str
        return self._abi

    @property
    def platform(self):
        # type: () -> str
        return self._platform

    def __eq__(self, other):
        # type: (object) -> bool
        if not isinstance(other, Tag):
            return NotImplemented

        return (
            (self.platform == other.platform)
            and (self.abi == other.abi)
            and (self.interpreter == other.interpreter)
        )

    def __hash__(self):
        # type: () -> int
        return hash((self._interpreter, self._abi, self._platform))

    def __str__(self):
        # type: () -> str
        return "{}-{}-{}".format(self._interpreter, self._abi, self._platform)

    def __repr__(self):
        # type: () -> str
        return "<{self} @ {self_id}>".format(self=self, self_id=id(self))


def parse_tag(tag):
    # type: (str) -> FrozenSet[Tag]
    """
    Parses the provided tag (e.g. `py3-none-any`) into a frozenset of Tag instances.

    Returning a set is required due to the possibility that the tag is a
    compressed tag set.
    """
    tags = set()
    interpreters, abis, platforms = tag.split("-")
    for interpreter in interpreters.split("."):
        for abi in abis.split("."):
            for platform_ in platforms.split("."):
                tags.add(Tag(interpreter, abi, platform_))
    return frozenset(tags)


def _warn_keyword_parameter(func_name, kwargs):
    # type: (str, Dict[str, bool]) -> bool
    """
    Backwards-compatibility with Python 2.7 to allow treating 'warn' as keyword-only.
    """
    if not kwargs:
        return False
    elif len(kwargs) > 1 or "warn" not in kwargs:
        kwargs.pop("warn", None)
        arg = next(iter(kwargs.keys()))
        raise TypeError(
            "{}() got an unexpected keyword argument {!r}".format(func_name, arg)
        )
    return kwargs["warn"]


def _get_config_var(name, warn=False):
    # type: (str, bool) -> Union[int, str, None]
    value = sysconfig.get_config_var(name)
    if value is None and warn:
        logger.debug(
            "Config variable '%s' is unset, Python ABI tag may be incorrect", name
        )
    return value


def _normalize_string(string):
    # type: (str) -> str
    return string.replace(".", "_").replace("-", "_")


def _abi3_applies(python_version):
    # type: (PythonVersion) -> bool
    """
    Determine if the Python version supports abi3.

    PEP 384 was first implemented in Python 3.2.
    """
    return len(python_version) > 1 and tuple(python_version) >= (3, 2)


def _cpython_abis(py_version, warn=False):
    # type: (PythonVersion, bool) -> List[str]
    py_version = tuple(py_version)  # To allow for version comparison.
    abis = []
    version = _version_nodot(py_version[:2])
    debug = pymalloc = ucs4 = ""
    with_debug = _get_config_var("Py_DEBUG", warn)
    has_refcount = hasattr(sys, "gettotalrefcount")
    # Windows doesn't set Py_DEBUG, so checking for support of debug-compiled
    # extension modules is the best option.
    # https://github.com/pypa/pip/issues/3383#issuecomment-173267692
    has_ext = "_d.pyd" in EXTENSION_SUFFIXES
    if with_debug or (with_debug is None and (has_refcount or has_ext)):
        debug = "d"
    if py_version < (3, 8):
        with_pymalloc = _get_config_var("WITH_PYMALLOC", warn)
        if with_pymalloc or with_pymalloc is None:
            pymalloc = "m"
        if py_version < (3, 3):
            unicode_size = _get_config_var("Py_UNICODE_SIZE", warn)
            if unicode_size == 4 or (
                unicode_size is None and sys.maxunicode == 0x10FFFF
            ):
                ucs4 = "u"
    elif debug:
        # Debug builds can also load "normal" extension modules.
        # We can also assume no UCS-4 or pymalloc requirement.
        abis.append("cp{version}".format(version=version))
    abis.insert(
        0,
        "cp{version}{debug}{pymalloc}{ucs4}".format(
            version=version, debug=debug, pymalloc=pymalloc, ucs4=ucs4
        ),
    )
    return abis


def cpython_tags(
    python_version=None,  # type: Optional[PythonVersion]
    abis=None,  # type: Optional[Iterable[str]]
    platforms=None,  # type: Optional[Iterable[str]]
    **kwargs  # type: bool
):
    # type: (...) -> Iterator[Tag]
    """
    Yields the tags for a CPython interpreter.

    The tags consist of:
    - cp<python_version>-<abi>-<platform>
    - cp<python_version>-abi3-<platform>
    - cp<python_version>-none-<platform>
    - cp<less than python_version>-abi3-<platform>  # Older Python versions down to 3.2.

    If python_version only specifies a major version then user-provided ABIs and
    the 'none' ABItag will be used.

    If 'abi3' or 'none' are specified in 'abis' then they will be yielded at
    their normal position and not at the beginning.
    """
    warn = _warn_keyword_parameter("cpython_tags", kwargs)
    if not python_version:
        python_version = sys.version_info[:2]

    interpreter = "cp{}".format(_version_nodot(python_version[:2]))

    if abis is None:
        if len(python_version) > 1:
            abis = _cpython_abis(python_version, warn)
        else:
            abis = []
    abis = list(abis)
    # 'abi3' and 'none' are explicitly handled later.
    for explicit_abi in ("abi3", "none"):
        try:
            abis.remove(explicit_abi)
        except ValueError:
            pass

    platforms = list(platforms or _platform_tags())
    for abi in abis:
        for platform_ in platforms:
            yield Tag(interpreter, abi, platform_)
    if _abi3_applies(python_version):
        for tag in (Tag(interpreter, "abi3", platform_) for platform_ in platforms):
            yield tag
    for tag in (Tag(interpreter, "none", platform_) for platform_ in platforms):
        yield tag

    if _abi3_applies(python_version):
        for minor_version in range(python_version[1] - 1, 1, -1):
            for platform_ in platforms:
                interpreter = "cp{version}".format(
                    version=_version_nodot((python_version[0], minor_version))
                )
                yield Tag(interpreter, "abi3", platform_)


def _generic_abi():
    # type: () -> Iterator[str]
    abi = sysconfig.get_config_var("SOABI")
    if abi:
        yield _normalize_string(abi)


def generic_tags(
    interpreter=None,  # type: Optional[str]
    abis=None,  # type: Optional[Iterable[str]]
    platforms=None,  # type: Optional[Iterable[str]]
    **kwargs  # type: bool
):
    # type: (...) -> Iterator[Tag]
    """
    Yields the tags for a generic interpreter.

    The tags consist of:
    - <interpreter>-<abi>-<platform>

    The "none" ABI will be added if it was not explicitly provided.
    """
    warn = _warn_keyword_parameter("generic_tags", kwargs)
    if not interpreter:
        interp_name = interpreter_name()
        interp_version = interpreter_version(warn=warn)
        interpreter = "".join([interp_name, interp_version])
    if abis is None:
        abis = _generic_abi()
    platforms = list(platforms or _platform_tags())
    abis = list(abis)
    if "none" not in abis:
        abis.append("none")
    for abi in abis:
        for platform_ in platforms:
            yield Tag(interpreter, abi, platform_)


def _py_interpreter_range(py_version):
    # type: (PythonVersion) -> Iterator[str]
    """
    Yields Python versions in descending order.

    After the latest version, the major-only version will be yielded, and then
    all previous versions of that major version.
    """
    if len(py_version) > 1:
        yield "py{version}".format(version=_version_nodot(py_version[:2]))
    yield "py{major}".format(major=py_version[0])
    if len(py_version) > 1:
        for minor in range(py_version[1] - 1, -1, -1):
            yield "py{version}".format(version=_version_nodot((py_version[0], minor)))


def compatible_tags(
    python_version=None,  # type: Optional[PythonVersion]
    interpreter=None,  # type: Optional[str]
    platforms=None,  # type: Optional[Iterable[str]]
):
    # type: (...) -> Iterator[Tag]
    """
    Yields the sequence of tags that are compatible with a specific version of Python.

    The tags consist of:
    - py*-none-<platform>
    - <interpreter>-none-any  # ... if `interpreter` is provided.
    - py*-none-any
    """
    if not python_version:
        python_version = sys.version_info[:2]
    platforms = list(platforms or _platform_tags())
    for version in _py_interpreter_range(python_version):
        for platform_ in platforms:
            yield Tag(version, "none", platform_)
    if interpreter:
        yield Tag(interpreter, "none", "any")
    for version in _py_interpreter_range(python_version):
        yield Tag(version, "none", "any")


def _mac_arch(arch, is_32bit=_32_BIT_INTERPRETER):
    # type: (str, bool) -> str
    if not is_32bit:
        return arch

    if arch.startswith("ppc"):
        return "ppc"

    return "i386"


def _mac_binary_formats(version, cpu_arch):
    # type: (MacVersion, str) -> List[str]
    formats = [cpu_arch]
    if cpu_arch == "x86_64":
        if version < (10, 4):
            return []
        formats.extend(["intel", "fat64", "fat32"])

    elif cpu_arch == "i386":
        if version < (10, 4):
            return []
        formats.extend(["intel", "fat32", "fat"])

    elif cpu_arch == "ppc64":
        # TODO: Need to care about 32-bit PPC for ppc64 through 10.2?
        if version > (10, 5) or version < (10, 4):
            return []
        formats.append("fat64")

    elif cpu_arch == "ppc":
        if version > (10, 6):
            return []
        formats.extend(["fat32", "fat"])

    formats.append("universal")
    return formats


def mac_platforms(version=None, arch=None):
    # type: (Optional[MacVersion], Optional[str]) -> Iterator[str]
    """
    Yields the platform tags for a macOS system.

    The `version` parameter is a two-item tuple specifying the macOS version to
    generate platform tags for. The `arch` parameter is the CPU architecture to
    generate platform tags for. Both parameters default to the appropriate value
    for the current system.
    """
    version_str, _, cpu_arch = platform.mac_ver()  # type: ignore
    if version is None:
        version = cast("MacVersion", tuple(map(int, version_str.split(".")[:2])))
    else:
        version = version
    if arch is None:
        arch = _mac_arch(cpu_arch)
    else:
        arch = arch
    for minor_version in range(version[1], -1, -1):
        compat_version = version[0], minor_version
        binary_formats = _mac_binary_formats(compat_version, arch)
        for binary_format in binary_formats:
            yield "macosx_{major}_{minor}_{binary_format}".format(
                major=compat_version[0],
                minor=compat_version[1],
                binary_format=binary_format,
            )


# From PEP 513.
def _is_manylinux_compatible(name, glibc_version):
    # type: (str, GlibcVersion) -> bool
    # Check for presence of _manylinux module.
    try:
        import _manylinux  # noqa

        return bool(getattr(_manylinux, name + "_compatible"))
    except (ImportError, AttributeError):
        # Fall through to heuristic check below.
        pass

    return _have_compatible_glibc(*glibc_version)


def _glibc_version_string():
    # type: () -> Optional[str]
    # Returns glibc version string, or None if not using glibc.
    return _glibc_version_string_confstr() or _glibc_version_string_ctypes()


def _glibc_version_string_confstr():
    # type: () -> Optional[str]
    """
    Primary implementation of glibc_version_string using os.confstr.
    """
    # os.confstr is quite a bit faster than ctypes.DLL. It's also less likely
    # to be broken or missing. This strategy is used in the standard library
    # platform module.
    # https://github.com/python/cpython/blob/fcf1d003bf4f0100c9d0921ff3d70e1127ca1b71/Lib/platform.py#L175-L183
    try:
        # os.confstr("CS_GNU_LIBC_VERSION") returns a string like "glibc 2.17".
        version_string = os.confstr(  # type: ignore[attr-defined] # noqa: F821
            "CS_GNU_LIBC_VERSION"
        )
        assert version_string is not None
        _, version = version_string.split()  # type: Tuple[str, str]
    except (AssertionError, AttributeError, OSError, ValueError):
        # os.confstr() or CS_GNU_LIBC_VERSION not available (or a bad value)...
        return None
    return version


def _glibc_version_string_ctypes():
    # type: () -> Optional[str]
    """
    Fallback implementation of glibc_version_string using ctypes.
    """
    try:
        import ctypes
    except ImportError:
        return None

    # ctypes.CDLL(None) internally calls dlopen(NULL), and as the dlopen
    # manpage says, "If filename is NULL, then the returned handle is for the
    # main program". This way we can let the linker do the work to figure out
    # which libc our process is actually using.
    #
    # Note: typeshed is wrong here so we are ignoring this line.
    process_namespace = ctypes.CDLL(None)  # type: ignore
    try:
        gnu_get_libc_version = process_namespace.gnu_get_libc_version
    except AttributeError:
        # Symbol doesn't exist -> therefore, we are not linked to
        # glibc.
        return None

    # Call gnu_get_libc_version, which returns a string like "2.5"
    gnu_get_libc_version.restype = ctypes.c_char_p
    version_str = gnu_get_libc_version()  # type: str
    # py2 / py3 compatibility:
    if not isinstance(version_str, str):
        version_str = version_str.decode("ascii")

    return version_str


# Separated out from have_compatible_glibc for easier unit testing.
def _check_glibc_version(version_str, required_major, minimum_minor):
    # type: (str, int, int) -> bool
    # Parse string and check against requested version.
    #
    # We use a regexp instead of str.split because we want to discard any
    # random junk that might come after the minor version -- this might happen
    # in patched/forked versions of glibc (e.g. Linaro's version of glibc
    # uses version strings like "2.20-2014.11"). See gh-3588.
    m = re.match(r"(?P<major>[0-9]+)\.(?P<minor>[0-9]+)", version_str)
    if not m:
        warnings.warn(
            "Expected glibc version with 2 components major.minor,"
            " got: %s" % version_str,
            RuntimeWarning,
        )
        return False
    return (
        int(m.group("major")) == required_major
        and int(m.group("minor")) >= minimum_minor
    )


def _have_compatible_glibc(required_major, minimum_minor):
    # type: (int, int) -> bool
    version_str = _glibc_version_string()
    if version_str is None:
        return False
    return _check_glibc_version(version_str, required_major, minimum_minor)


# Python does not provide platform information at sufficient granularity to
# identify the architecture of the running executable in some cases, so we
# determine it dynamically by reading the information from the running
# process. This only applies on Linux, which uses the ELF format.
class _ELFFileHeader(object):
    # https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#File_header
    class _InvalidELFFileHeader(ValueError):
        """
        An invalid ELF file header was found.
        """

    ELF_MAGIC_NUMBER = 0x7F454C46
    ELFCLASS32 = 1
    ELFCLASS64 = 2
    ELFDATA2LSB = 1
    ELFDATA2MSB = 2
    EM_386 = 3
    EM_S390 = 22
    EM_ARM = 40
    EM_X86_64 = 62
    EF_ARM_ABIMASK = 0xFF000000
    EF_ARM_ABI_VER5 = 0x05000000
    EF_ARM_ABI_FLOAT_HARD = 0x00000400

    def __init__(self, file):
        # type: (IO[bytes]) -> None
        def unpack(fmt):
            # type: (str) -> int
            try:
                (result,) = struct.unpack(
                    fmt, file.read(struct.calcsize(fmt))
                )  # type: (int, )
            except struct.error:
                raise _ELFFileHeader._InvalidELFFileHeader()
            return result

        self.e_ident_magic = unpack(">I")
        if self.e_ident_magic != self.ELF_MAGIC_NUMBER:
            raise _ELFFileHeader._InvalidELFFileHeader()
        self.e_ident_class = unpack("B")
        if self.e_ident_class not in {self.ELFCLASS32, self.ELFCLASS64}:
            raise _ELFFileHeader._InvalidELFFileHeader()
        self.e_ident_data = unpack("B")
        if self.e_ident_data not in {self.ELFDATA2LSB, self.ELFDATA2MSB}:
            raise _ELFFileHeader._InvalidELFFileHeader()
        self.e_ident_version = unpack("B")
        self.e_ident_osabi = unpack("B")
        self.e_ident_abiversion = unpack("B")
        self.e_ident_pad = file.read(7)
        format_h = "<H" if self.e_ident_data == self.ELFDATA2LSB else ">H"
        format_i = "<I" if self.e_ident_data == self.ELFDATA2LSB else ">I"
        format_q = "<Q" if self.e_ident_data == self.ELFDATA2LSB else ">Q"
        format_p = format_i if self.e_ident_class == self.ELFCLASS32 else format_q
        self.e_type = unpack(format_h)
        self.e_machine = unpack(format_h)
        self.e_version = unpack(format_i)
        self.e_entry = unpack(format_p)
        self.e_phoff = unpack(format_p)
        self.e_shoff = unpack(format_p)
        self.e_flags = unpack(format_i)
        self.e_ehsize = unpack(format_h)
        self.e_phentsize = unpack(format_h)
        self.e_phnum = unpack(format_h)
        self.e_shentsize = unpack(format_h)
        self.e_shnum = unpack(format_h)
        self.e_shstrndx = unpack(format_h)


def _get_elf_header():
    # type: () -> Optional[_ELFFileHeader]
    try:
        with open(sys.executable, "rb") as f:
            elf_header = _ELFFileHeader(f)
    except (IOError, OSError, TypeError, _ELFFileHeader._InvalidELFFileHeader):
        return None
    return elf_header


def _is_linux_armhf():
    # type: () -> bool
    # hard-float ABI can be detected from the ELF header of the running
    # process
    # https://static.docs.arm.com/ihi0044/g/aaelf32.pdf
    elf_header = _get_elf_header()
    if elf_header is None:
        return False
    result = elf_header.e_ident_class == elf_header.ELFCLASS32
    result &= elf_header.e_ident_data == elf_header.ELFDATA2LSB
    result &= elf_header.e_machine == elf_header.EM_ARM
    result &= (
        elf_header.e_flags & elf_header.EF_ARM_ABIMASK
    ) == elf_header.EF_ARM_ABI_VER5
    result &= (
        elf_header.e_flags & elf_header.EF_ARM_ABI_FLOAT_HARD
    ) == elf_header.EF_ARM_ABI_FLOAT_HARD
    return result


def _is_linux_i686():
    # type: () -> bool
    elf_header = _get_elf_header()
    if elf_header is None:
        return False
    result = elf_header.e_ident_class == elf_header.ELFCLASS32
    result &= elf_header.e_ident_data == elf_header.ELFDATA2LSB
    result &= elf_header.e_machine == elf_header.EM_386
    return result


def _have_compatible_manylinux_abi(arch):
    # type: (str) -> bool
    if arch == "armv7l":
        return _is_linux_armhf()
    if arch == "i686":
        return _is_linux_i686()
    return True


def _linux_platforms(is_32bit=_32_BIT_INTERPRETER):
    # type: (bool) -> Iterator[str]
    linux = _normalize_string(distutils.util.get_platform())
    if is_32bit:
        if linux == "linux_x86_64":
            linux = "linux_i686"
        elif linux == "linux_aarch64":
            linux = "linux_armv7l"
    manylinux_support = []
    _, arch = linux.split("_", 1)
    if _have_compatible_manylinux_abi(arch):
        if arch in {"x86_64", "i686", "aarch64", "armv7l", "ppc64", "ppc64le", "s390x"}:
            manylinux_support.append(
                ("manylinux2014", (2, 17))
            )  # CentOS 7 w/ glibc 2.17 (PEP 599)
        if arch in {"x86_64", "i686"}:
            manylinux_support.append(
                ("manylinux2010", (2, 12))
            )  # CentOS 6 w/ glibc 2.12 (PEP 571)
            manylinux_support.append(
                ("manylinux1", (2, 5))
            )  # CentOS 5 w/ glibc 2.5 (PEP 513)
    manylinux_support_iter = iter(manylinux_support)
    for name, glibc_version in manylinux_support_iter:
        if _is_manylinux_compatible(name, glibc_version):
            yield linux.replace("linux", name)
            break
    # Support for a later manylinux implies support for an earlier version.
    for name, _ in manylinux_support_iter:
        yield linux.replace("linux", name)
    yield linux


def _generic_platforms():
    # type: () -> Iterator[str]
    yield _normalize_string(distutils.util.get_platform())


def _platform_tags():
    # type: () -> Iterator[str]
    """
    Provides the platform tags for this installation.
    """
    if platform.system() == "Darwin":
        return mac_platforms()
    elif platform.system() == "Linux":
        return _linux_platforms()
    else:
        return _generic_platforms()


def interpreter_name():
    # type: () -> str
    """
    Returns the name of the running interpreter.
    """
    try:
        name = sys.implementation.name  # type: ignore
    except AttributeError:  # pragma: no cover
        # Python 2.7 compatibility.
        name = platform.python_implementation().lower()
    return INTERPRETER_SHORT_NAMES.get(name) or name


def interpreter_version(**kwargs):
    # type: (bool) -> str
    """
    Returns the version of the running interpreter.
    """
    warn = _warn_keyword_parameter("interpreter_version", kwargs)
    version = _get_config_var("py_version_nodot", warn=warn)
    if version:
        version = str(version)
    else:
        version = _version_nodot(sys.version_info[:2])
    return version


def _version_nodot(version):
    # type: (PythonVersion) -> str
    if any(v >= 10 for v in version):
        sep = "_"
    else:
        sep = ""
    return sep.join(map(str, version))


def sys_tags(**kwargs):
    # type: (bool) -> Iterator[Tag]
    """
    Returns the sequence of tag triples for the running interpreter.

    The order of the sequence corresponds to priority order for the
    interpreter, from most to least important.
    """
    warn = _warn_keyword_parameter("sys_tags", kwargs)

    interp_name = interpreter_name()
    if interp_name == "cp":
        for tag in cpython_tags(warn=warn):
            yield tag
    else:
        for tag in generic_tags():
            yield tag

    for tag in compatible_tags():
        yield tag

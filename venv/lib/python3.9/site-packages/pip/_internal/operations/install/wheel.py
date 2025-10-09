"""Support for installing and building the "wheel" binary package format."""

from __future__ import annotations

import collections
import compileall
import contextlib
import csv
import importlib
import logging
import os.path
import re
import shutil
import sys
import textwrap
import warnings
from base64 import urlsafe_b64encode
from collections.abc import Generator, Iterable, Iterator, Sequence
from email.message import Message
from itertools import chain, filterfalse, starmap
from typing import (
    IO,
    Any,
    BinaryIO,
    Callable,
    NewType,
    Protocol,
    Union,
    cast,
)
from zipfile import ZipFile, ZipInfo

from pip._vendor.distlib.scripts import ScriptMaker
from pip._vendor.distlib.util import get_export_entry
from pip._vendor.packaging.utils import canonicalize_name

from pip._internal.exceptions import InstallationError
from pip._internal.locations import get_major_minor_version
from pip._internal.metadata import (
    BaseDistribution,
    FilesystemWheel,
    get_wheel_distribution,
)
from pip._internal.models.direct_url import DIRECT_URL_METADATA_NAME, DirectUrl
from pip._internal.models.scheme import SCHEME_KEYS, Scheme
from pip._internal.utils.filesystem import adjacent_tmp_file, replace
from pip._internal.utils.misc import StreamWrapper, ensure_dir, hash_file, partition
from pip._internal.utils.unpacking import (
    current_umask,
    is_within_directory,
    set_extracted_file_to_default_mode_plus_executable,
    zip_item_is_executable,
)
from pip._internal.utils.wheel import parse_wheel


class File(Protocol):
    src_record_path: RecordPath
    dest_path: str
    changed: bool

    def save(self) -> None:
        pass


logger = logging.getLogger(__name__)

RecordPath = NewType("RecordPath", str)
InstalledCSVRow = tuple[RecordPath, str, Union[int, str]]


def rehash(path: str, blocksize: int = 1 << 20) -> tuple[str, str]:
    """Return (encoded_digest, length) for path using hashlib.sha256()"""
    h, length = hash_file(path, blocksize)
    digest = "sha256=" + urlsafe_b64encode(h.digest()).decode("latin1").rstrip("=")
    return (digest, str(length))


def csv_io_kwargs(mode: str) -> dict[str, Any]:
    """Return keyword arguments to properly open a CSV file
    in the given mode.
    """
    return {"mode": mode, "newline": "", "encoding": "utf-8"}


def fix_script(path: str) -> bool:
    """Replace #!python with #!/path/to/python
    Return True if file was changed.
    """
    # XXX RECORD hashes will need to be updated
    assert os.path.isfile(path)

    with open(path, "rb") as script:
        firstline = script.readline()
        if not firstline.startswith(b"#!python"):
            return False
        exename = sys.executable.encode(sys.getfilesystemencoding())
        firstline = b"#!" + exename + os.linesep.encode("ascii")
        rest = script.read()
    with open(path, "wb") as script:
        script.write(firstline)
        script.write(rest)
    return True


def wheel_root_is_purelib(metadata: Message) -> bool:
    return metadata.get("Root-Is-Purelib", "").lower() == "true"


def get_entrypoints(dist: BaseDistribution) -> tuple[dict[str, str], dict[str, str]]:
    console_scripts = {}
    gui_scripts = {}
    for entry_point in dist.iter_entry_points():
        if entry_point.group == "console_scripts":
            console_scripts[entry_point.name] = entry_point.value
        elif entry_point.group == "gui_scripts":
            gui_scripts[entry_point.name] = entry_point.value
    return console_scripts, gui_scripts


def message_about_scripts_not_on_PATH(scripts: Sequence[str]) -> str | None:
    """Determine if any scripts are not on PATH and format a warning.
    Returns a warning message if one or more scripts are not on PATH,
    otherwise None.
    """
    if not scripts:
        return None

    # Group scripts by the path they were installed in
    grouped_by_dir: dict[str, set[str]] = collections.defaultdict(set)
    for destfile in scripts:
        parent_dir = os.path.dirname(destfile)
        script_name = os.path.basename(destfile)
        grouped_by_dir[parent_dir].add(script_name)

    # We don't want to warn for directories that are on PATH.
    not_warn_dirs = [
        os.path.normcase(os.path.normpath(i)).rstrip(os.sep)
        for i in os.environ.get("PATH", "").split(os.pathsep)
    ]
    # If an executable sits with sys.executable, we don't warn for it.
    #     This covers the case of venv invocations without activating the venv.
    not_warn_dirs.append(
        os.path.normcase(os.path.normpath(os.path.dirname(sys.executable)))
    )
    warn_for: dict[str, set[str]] = {
        parent_dir: scripts
        for parent_dir, scripts in grouped_by_dir.items()
        if os.path.normcase(os.path.normpath(parent_dir)) not in not_warn_dirs
    }
    if not warn_for:
        return None

    # Format a message
    msg_lines = []
    for parent_dir, dir_scripts in warn_for.items():
        sorted_scripts: list[str] = sorted(dir_scripts)
        if len(sorted_scripts) == 1:
            start_text = f"script {sorted_scripts[0]} is"
        else:
            start_text = "scripts {} are".format(
                ", ".join(sorted_scripts[:-1]) + " and " + sorted_scripts[-1]
            )

        msg_lines.append(
            f"The {start_text} installed in '{parent_dir}' which is not on PATH."
        )

    last_line_fmt = (
        "Consider adding {} to PATH or, if you prefer "
        "to suppress this warning, use --no-warn-script-location."
    )
    if len(msg_lines) == 1:
        msg_lines.append(last_line_fmt.format("this directory"))
    else:
        msg_lines.append(last_line_fmt.format("these directories"))

    # Add a note if any directory starts with ~
    warn_for_tilde = any(
        i[0] == "~" for i in os.environ.get("PATH", "").split(os.pathsep) if i
    )
    if warn_for_tilde:
        tilde_warning_msg = (
            "NOTE: The current PATH contains path(s) starting with `~`, "
            "which may not be expanded by all applications."
        )
        msg_lines.append(tilde_warning_msg)

    # Returns the formatted multiline message
    return "\n".join(msg_lines)


def _normalized_outrows(
    outrows: Iterable[InstalledCSVRow],
) -> list[tuple[str, str, str]]:
    """Normalize the given rows of a RECORD file.

    Items in each row are converted into str. Rows are then sorted to make
    the value more predictable for tests.

    Each row is a 3-tuple (path, hash, size) and corresponds to a record of
    a RECORD file (see PEP 376 and PEP 427 for details).  For the rows
    passed to this function, the size can be an integer as an int or string,
    or the empty string.
    """
    # Normally, there should only be one row per path, in which case the
    # second and third elements don't come into play when sorting.
    # However, in cases in the wild where a path might happen to occur twice,
    # we don't want the sort operation to trigger an error (but still want
    # determinism).  Since the third element can be an int or string, we
    # coerce each element to a string to avoid a TypeError in this case.
    # For additional background, see--
    # https://github.com/pypa/pip/issues/5868
    return sorted(
        (record_path, hash_, str(size)) for record_path, hash_, size in outrows
    )


def _record_to_fs_path(record_path: RecordPath, lib_dir: str) -> str:
    return os.path.join(lib_dir, record_path)


def _fs_to_record_path(path: str, lib_dir: str) -> RecordPath:
    # On Windows, do not handle relative paths if they belong to different
    # logical disks
    if os.path.splitdrive(path)[0].lower() == os.path.splitdrive(lib_dir)[0].lower():
        path = os.path.relpath(path, lib_dir)

    path = path.replace(os.path.sep, "/")
    return cast("RecordPath", path)


def get_csv_rows_for_installed(
    old_csv_rows: list[list[str]],
    installed: dict[RecordPath, RecordPath],
    changed: set[RecordPath],
    generated: list[str],
    lib_dir: str,
) -> list[InstalledCSVRow]:
    """
    :param installed: A map from archive RECORD path to installation RECORD
        path.
    """
    installed_rows: list[InstalledCSVRow] = []
    for row in old_csv_rows:
        if len(row) > 3:
            logger.warning("RECORD line has more than three elements: %s", row)
        old_record_path = cast("RecordPath", row[0])
        new_record_path = installed.pop(old_record_path, old_record_path)
        if new_record_path in changed:
            digest, length = rehash(_record_to_fs_path(new_record_path, lib_dir))
        else:
            digest = row[1] if len(row) > 1 else ""
            length = row[2] if len(row) > 2 else ""
        installed_rows.append((new_record_path, digest, length))
    for f in generated:
        path = _fs_to_record_path(f, lib_dir)
        digest, length = rehash(f)
        installed_rows.append((path, digest, length))
    return installed_rows + [
        (installed_record_path, "", "") for installed_record_path in installed.values()
    ]


def get_console_script_specs(console: dict[str, str]) -> list[str]:
    """
    Given the mapping from entrypoint name to callable, return the relevant
    console script specs.
    """
    # Don't mutate caller's version
    console = console.copy()

    scripts_to_generate = []

    # Special case pip and setuptools to generate versioned wrappers
    #
    # The issue is that some projects (specifically, pip and setuptools) use
    # code in setup.py to create "versioned" entry points - pip2.7 on Python
    # 2.7, pip3.3 on Python 3.3, etc. But these entry points are baked into
    # the wheel metadata at build time, and so if the wheel is installed with
    # a *different* version of Python the entry points will be wrong. The
    # correct fix for this is to enhance the metadata to be able to describe
    # such versioned entry points.
    # Currently, projects using versioned entry points will either have
    # incorrect versioned entry points, or they will not be able to distribute
    # "universal" wheels (i.e., they will need a wheel per Python version).
    #
    # Because setuptools and pip are bundled with _ensurepip and virtualenv,
    # we need to use universal wheels. As a workaround, we
    # override the versioned entry points in the wheel and generate the
    # correct ones.
    #
    # To add the level of hack in this section of code, in order to support
    # ensurepip this code will look for an ``ENSUREPIP_OPTIONS`` environment
    # variable which will control which version scripts get installed.
    #
    # ENSUREPIP_OPTIONS=altinstall
    #   - Only pipX.Y and easy_install-X.Y will be generated and installed
    # ENSUREPIP_OPTIONS=install
    #   - pipX.Y, pipX, easy_install-X.Y will be generated and installed. Note
    #     that this option is technically if ENSUREPIP_OPTIONS is set and is
    #     not altinstall
    # DEFAULT
    #   - The default behavior is to install pip, pipX, pipX.Y, easy_install
    #     and easy_install-X.Y.
    pip_script = console.pop("pip", None)
    if pip_script:
        if "ENSUREPIP_OPTIONS" not in os.environ:
            scripts_to_generate.append("pip = " + pip_script)

        if os.environ.get("ENSUREPIP_OPTIONS", "") != "altinstall":
            scripts_to_generate.append(f"pip{sys.version_info[0]} = {pip_script}")

        scripts_to_generate.append(f"pip{get_major_minor_version()} = {pip_script}")
        # Delete any other versioned pip entry points
        pip_ep = [k for k in console if re.match(r"pip(\d+(\.\d+)?)?$", k)]
        for k in pip_ep:
            del console[k]
    easy_install_script = console.pop("easy_install", None)
    if easy_install_script:
        if "ENSUREPIP_OPTIONS" not in os.environ:
            scripts_to_generate.append("easy_install = " + easy_install_script)

        scripts_to_generate.append(
            f"easy_install-{get_major_minor_version()} = {easy_install_script}"
        )
        # Delete any other versioned easy_install entry points
        easy_install_ep = [
            k for k in console if re.match(r"easy_install(-\d+\.\d+)?$", k)
        ]
        for k in easy_install_ep:
            del console[k]

    # Generate the console entry points specified in the wheel
    scripts_to_generate.extend(starmap("{} = {}".format, console.items()))

    return scripts_to_generate


class ZipBackedFile:
    def __init__(
        self, src_record_path: RecordPath, dest_path: str, zip_file: ZipFile
    ) -> None:
        self.src_record_path = src_record_path
        self.dest_path = dest_path
        self._zip_file = zip_file
        self.changed = False

    def _getinfo(self) -> ZipInfo:
        return self._zip_file.getinfo(self.src_record_path)

    def save(self) -> None:
        # When we open the output file below, any existing file is truncated
        # before we start writing the new contents. This is fine in most
        # cases, but can cause a segfault if pip has loaded a shared
        # object (e.g. from pyopenssl through its vendored urllib3)
        # Since the shared object is mmap'd an attempt to call a
        # symbol in it will then cause a segfault. Unlinking the file
        # allows writing of new contents while allowing the process to
        # continue to use the old copy.
        if os.path.exists(self.dest_path):
            os.unlink(self.dest_path)

        zipinfo = self._getinfo()

        # optimization: the file is created by open(),
        # skip the decompression when there is 0 bytes to decompress.
        with open(self.dest_path, "wb") as dest:
            if zipinfo.file_size > 0:
                with self._zip_file.open(zipinfo) as f:
                    blocksize = min(zipinfo.file_size, 1024 * 1024)
                    shutil.copyfileobj(f, dest, blocksize)

        if zip_item_is_executable(zipinfo):
            set_extracted_file_to_default_mode_plus_executable(self.dest_path)


class ScriptFile:
    def __init__(self, file: File) -> None:
        self._file = file
        self.src_record_path = self._file.src_record_path
        self.dest_path = self._file.dest_path
        self.changed = False

    def save(self) -> None:
        self._file.save()
        self.changed = fix_script(self.dest_path)


class MissingCallableSuffix(InstallationError):
    def __init__(self, entry_point: str) -> None:
        super().__init__(
            f"Invalid script entry point: {entry_point} - A callable "
            "suffix is required. See https://packaging.python.org/"
            "specifications/entry-points/#use-for-scripts for more "
            "information."
        )


def _raise_for_invalid_entrypoint(specification: str) -> None:
    entry = get_export_entry(specification)
    if entry is not None and entry.suffix is None:
        raise MissingCallableSuffix(str(entry))


class PipScriptMaker(ScriptMaker):
    # Override distlib's default script template with one that
    # doesn't import `re` module, allowing scripts to load faster.
    script_template = textwrap.dedent(
        """\
        import sys
        from %(module)s import %(import_name)s
        if __name__ == '__main__':
            if sys.argv[0].endswith('.exe'):
                sys.argv[0] = sys.argv[0][:-4]
            sys.exit(%(func)s())
"""
    )

    def make(
        self, specification: str, options: dict[str, Any] | None = None
    ) -> list[str]:
        _raise_for_invalid_entrypoint(specification)
        return super().make(specification, options)


def _install_wheel(  # noqa: C901, PLR0915 function is too long
    name: str,
    wheel_zip: ZipFile,
    wheel_path: str,
    scheme: Scheme,
    pycompile: bool = True,
    warn_script_location: bool = True,
    direct_url: DirectUrl | None = None,
    requested: bool = False,
) -> None:
    """Install a wheel.

    :param name: Name of the project to install
    :param wheel_zip: open ZipFile for wheel being installed
    :param scheme: Distutils scheme dictating the install directories
    :param req_description: String used in place of the requirement, for
        logging
    :param pycompile: Whether to byte-compile installed Python files
    :param warn_script_location: Whether to check that scripts are installed
        into a directory on PATH
    :raises UnsupportedWheel:
        * when the directory holds an unpacked wheel with incompatible
          Wheel-Version
        * when the .dist-info dir does not match the wheel
    """
    info_dir, metadata = parse_wheel(wheel_zip, name)

    if wheel_root_is_purelib(metadata):
        lib_dir = scheme.purelib
    else:
        lib_dir = scheme.platlib

    # Record details of the files moved
    #   installed = files copied from the wheel to the destination
    #   changed = files changed while installing (scripts #! line typically)
    #   generated = files newly generated during the install (script wrappers)
    installed: dict[RecordPath, RecordPath] = {}
    changed: set[RecordPath] = set()
    generated: list[str] = []

    def record_installed(
        srcfile: RecordPath, destfile: str, modified: bool = False
    ) -> None:
        """Map archive RECORD paths to installation RECORD paths."""
        newpath = _fs_to_record_path(destfile, lib_dir)
        installed[srcfile] = newpath
        if modified:
            changed.add(newpath)

    def is_dir_path(path: RecordPath) -> bool:
        return path.endswith("/")

    def assert_no_path_traversal(dest_dir_path: str, target_path: str) -> None:
        if not is_within_directory(dest_dir_path, target_path):
            message = (
                "The wheel {!r} has a file {!r} trying to install"
                " outside the target directory {!r}"
            )
            raise InstallationError(
                message.format(wheel_path, target_path, dest_dir_path)
            )

    def root_scheme_file_maker(
        zip_file: ZipFile, dest: str
    ) -> Callable[[RecordPath], File]:
        def make_root_scheme_file(record_path: RecordPath) -> File:
            normed_path = os.path.normpath(record_path)
            dest_path = os.path.join(dest, normed_path)
            assert_no_path_traversal(dest, dest_path)
            return ZipBackedFile(record_path, dest_path, zip_file)

        return make_root_scheme_file

    def data_scheme_file_maker(
        zip_file: ZipFile, scheme: Scheme
    ) -> Callable[[RecordPath], File]:
        scheme_paths = {key: getattr(scheme, key) for key in SCHEME_KEYS}

        def make_data_scheme_file(record_path: RecordPath) -> File:
            normed_path = os.path.normpath(record_path)
            try:
                _, scheme_key, dest_subpath = normed_path.split(os.path.sep, 2)
            except ValueError:
                message = (
                    f"Unexpected file in {wheel_path}: {record_path!r}. .data directory"
                    " contents should be named like: '<scheme key>/<path>'."
                )
                raise InstallationError(message)

            try:
                scheme_path = scheme_paths[scheme_key]
            except KeyError:
                valid_scheme_keys = ", ".join(sorted(scheme_paths))
                message = (
                    f"Unknown scheme key used in {wheel_path}: {scheme_key} "
                    f"(for file {record_path!r}). .data directory contents "
                    f"should be in subdirectories named with a valid scheme "
                    f"key ({valid_scheme_keys})"
                )
                raise InstallationError(message)

            dest_path = os.path.join(scheme_path, dest_subpath)
            assert_no_path_traversal(scheme_path, dest_path)
            return ZipBackedFile(record_path, dest_path, zip_file)

        return make_data_scheme_file

    def is_data_scheme_path(path: RecordPath) -> bool:
        return path.split("/", 1)[0].endswith(".data")

    paths = cast(list[RecordPath], wheel_zip.namelist())
    file_paths = filterfalse(is_dir_path, paths)
    root_scheme_paths, data_scheme_paths = partition(is_data_scheme_path, file_paths)

    make_root_scheme_file = root_scheme_file_maker(wheel_zip, lib_dir)
    files: Iterator[File] = map(make_root_scheme_file, root_scheme_paths)

    def is_script_scheme_path(path: RecordPath) -> bool:
        parts = path.split("/", 2)
        return len(parts) > 2 and parts[0].endswith(".data") and parts[1] == "scripts"

    other_scheme_paths, script_scheme_paths = partition(
        is_script_scheme_path, data_scheme_paths
    )

    make_data_scheme_file = data_scheme_file_maker(wheel_zip, scheme)
    other_scheme_files = map(make_data_scheme_file, other_scheme_paths)
    files = chain(files, other_scheme_files)

    # Get the defined entry points
    distribution = get_wheel_distribution(
        FilesystemWheel(wheel_path),
        canonicalize_name(name),
    )
    console, gui = get_entrypoints(distribution)

    def is_entrypoint_wrapper(file: File) -> bool:
        # EP, EP.exe and EP-script.py are scripts generated for
        # entry point EP by setuptools
        path = file.dest_path
        name = os.path.basename(path)
        if name.lower().endswith(".exe"):
            matchname = name[:-4]
        elif name.lower().endswith("-script.py"):
            matchname = name[:-10]
        elif name.lower().endswith(".pya"):
            matchname = name[:-4]
        else:
            matchname = name
        # Ignore setuptools-generated scripts
        return matchname in console or matchname in gui

    script_scheme_files: Iterator[File] = map(
        make_data_scheme_file, script_scheme_paths
    )
    script_scheme_files = filterfalse(is_entrypoint_wrapper, script_scheme_files)
    script_scheme_files = map(ScriptFile, script_scheme_files)
    files = chain(files, script_scheme_files)

    existing_parents = set()
    for file in files:
        # directory creation is lazy and after file filtering
        # to ensure we don't install empty dirs; empty dirs can't be
        # uninstalled.
        parent_dir = os.path.dirname(file.dest_path)
        if parent_dir not in existing_parents:
            ensure_dir(parent_dir)
            existing_parents.add(parent_dir)
        file.save()
        record_installed(file.src_record_path, file.dest_path, file.changed)

    def pyc_source_file_paths() -> Generator[str, None, None]:
        # We de-duplicate installation paths, since there can be overlap (e.g.
        # file in .data maps to same location as file in wheel root).
        # Sorting installation paths makes it easier to reproduce and debug
        # issues related to permissions on existing files.
        for installed_path in sorted(set(installed.values())):
            full_installed_path = os.path.join(lib_dir, installed_path)
            if not os.path.isfile(full_installed_path):
                continue
            if not full_installed_path.endswith(".py"):
                continue
            yield full_installed_path

    def pyc_output_path(path: str) -> str:
        """Return the path the pyc file would have been written to."""
        return importlib.util.cache_from_source(path)

    # Compile all of the pyc files for the installed files
    if pycompile:
        with contextlib.redirect_stdout(
            StreamWrapper.from_stream(sys.stdout)
        ) as stdout:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore")
                for path in pyc_source_file_paths():
                    success = compileall.compile_file(path, force=True, quiet=True)
                    if success:
                        pyc_path = pyc_output_path(path)
                        assert os.path.exists(pyc_path)
                        pyc_record_path = cast(
                            "RecordPath", pyc_path.replace(os.path.sep, "/")
                        )
                        record_installed(pyc_record_path, pyc_path)
        logger.debug(stdout.getvalue())

    maker = PipScriptMaker(None, scheme.scripts)

    # Ensure old scripts are overwritten.
    # See https://github.com/pypa/pip/issues/1800
    maker.clobber = True

    # Ensure we don't generate any variants for scripts because this is almost
    # never what somebody wants.
    # See https://bitbucket.org/pypa/distlib/issue/35/
    maker.variants = {""}

    # This is required because otherwise distlib creates scripts that are not
    # executable.
    # See https://bitbucket.org/pypa/distlib/issue/32/
    maker.set_mode = True

    # Generate the console and GUI entry points specified in the wheel
    scripts_to_generate = get_console_script_specs(console)

    gui_scripts_to_generate = list(starmap("{} = {}".format, gui.items()))

    generated_console_scripts = maker.make_multiple(scripts_to_generate)
    generated.extend(generated_console_scripts)

    generated.extend(maker.make_multiple(gui_scripts_to_generate, {"gui": True}))

    if warn_script_location:
        msg = message_about_scripts_not_on_PATH(generated_console_scripts)
        if msg is not None:
            logger.warning(msg)

    generated_file_mode = 0o666 & ~current_umask()

    @contextlib.contextmanager
    def _generate_file(path: str, **kwargs: Any) -> Generator[BinaryIO, None, None]:
        with adjacent_tmp_file(path, **kwargs) as f:
            yield f
        os.chmod(f.name, generated_file_mode)
        replace(f.name, path)

    dest_info_dir = os.path.join(lib_dir, info_dir)

    # Record pip as the installer
    installer_path = os.path.join(dest_info_dir, "INSTALLER")
    with _generate_file(installer_path) as installer_file:
        installer_file.write(b"pip\n")
    generated.append(installer_path)

    # Record the PEP 610 direct URL reference
    if direct_url is not None:
        direct_url_path = os.path.join(dest_info_dir, DIRECT_URL_METADATA_NAME)
        with _generate_file(direct_url_path) as direct_url_file:
            direct_url_file.write(direct_url.to_json().encode("utf-8"))
        generated.append(direct_url_path)

    # Record the REQUESTED file
    if requested:
        requested_path = os.path.join(dest_info_dir, "REQUESTED")
        with open(requested_path, "wb"):
            pass
        generated.append(requested_path)

    record_text = distribution.read_text("RECORD")
    record_rows = list(csv.reader(record_text.splitlines()))

    rows = get_csv_rows_for_installed(
        record_rows,
        installed=installed,
        changed=changed,
        generated=generated,
        lib_dir=lib_dir,
    )

    # Record details of all files installed
    record_path = os.path.join(dest_info_dir, "RECORD")

    with _generate_file(record_path, **csv_io_kwargs("w")) as record_file:
        # Explicitly cast to typing.IO[str] as a workaround for the mypy error:
        # "writer" has incompatible type "BinaryIO"; expected "_Writer"
        writer = csv.writer(cast("IO[str]", record_file))
        writer.writerows(_normalized_outrows(rows))


@contextlib.contextmanager
def req_error_context(req_description: str) -> Generator[None, None, None]:
    try:
        yield
    except InstallationError as e:
        message = f"For req: {req_description}. {e.args[0]}"
        raise InstallationError(message) from e


def install_wheel(
    name: str,
    wheel_path: str,
    scheme: Scheme,
    req_description: str,
    pycompile: bool = True,
    warn_script_location: bool = True,
    direct_url: DirectUrl | None = None,
    requested: bool = False,
) -> None:
    with ZipFile(wheel_path, allowZip64=True) as z:
        with req_error_context(req_description):
            _install_wheel(
                name=name,
                wheel_zip=z,
                wheel_path=wheel_path,
                scheme=scheme,
                pycompile=pycompile,
                warn_script_location=warn_script_location,
                direct_url=direct_url,
                requested=requested,
            )

"""
Requirements file parsing
"""

from __future__ import annotations

import codecs
import locale
import logging
import optparse
import os
import re
import shlex
import sys
import urllib.parse
from collections.abc import Generator, Iterable
from dataclasses import dataclass
from optparse import Values
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    NoReturn,
)

from pip._internal.cli import cmdoptions
from pip._internal.exceptions import InstallationError, RequirementsFileParseError
from pip._internal.models.search_scope import SearchScope

if TYPE_CHECKING:
    from pip._internal.index.package_finder import PackageFinder
    from pip._internal.network.session import PipSession

__all__ = ["parse_requirements"]

ReqFileLines = Iterable[tuple[int, str]]

LineParser = Callable[[str], tuple[str, Values]]

SCHEME_RE = re.compile(r"^(http|https|file):", re.I)
COMMENT_RE = re.compile(r"(^|\s+)#.*$")

# Matches environment variable-style values in '${MY_VARIABLE_1}' with the
# variable name consisting of only uppercase letters, digits or the '_'
# (underscore). This follows the POSIX standard defined in IEEE Std 1003.1,
# 2013 Edition.
ENV_VAR_RE = re.compile(r"(?P<var>\$\{(?P<name>[A-Z0-9_]+)\})")

SUPPORTED_OPTIONS: list[Callable[..., optparse.Option]] = [
    cmdoptions.index_url,
    cmdoptions.extra_index_url,
    cmdoptions.no_index,
    cmdoptions.constraints,
    cmdoptions.requirements,
    cmdoptions.editable,
    cmdoptions.find_links,
    cmdoptions.no_binary,
    cmdoptions.only_binary,
    cmdoptions.prefer_binary,
    cmdoptions.require_hashes,
    cmdoptions.pre,
    cmdoptions.trusted_host,
    cmdoptions.use_new_feature,
]

# options to be passed to requirements
SUPPORTED_OPTIONS_REQ: list[Callable[..., optparse.Option]] = [
    cmdoptions.global_options,
    cmdoptions.hash,
    cmdoptions.config_settings,
]

SUPPORTED_OPTIONS_EDITABLE_REQ: list[Callable[..., optparse.Option]] = [
    cmdoptions.config_settings,
]


# the 'dest' string values
SUPPORTED_OPTIONS_REQ_DEST = [str(o().dest) for o in SUPPORTED_OPTIONS_REQ]
SUPPORTED_OPTIONS_EDITABLE_REQ_DEST = [
    str(o().dest) for o in SUPPORTED_OPTIONS_EDITABLE_REQ
]

# order of BOMS is important: codecs.BOM_UTF16_LE is a prefix of codecs.BOM_UTF32_LE
# so data.startswith(BOM_UTF16_LE) would be true for UTF32_LE data
BOMS: list[tuple[bytes, str]] = [
    (codecs.BOM_UTF8, "utf-8"),
    (codecs.BOM_UTF32, "utf-32"),
    (codecs.BOM_UTF32_BE, "utf-32-be"),
    (codecs.BOM_UTF32_LE, "utf-32-le"),
    (codecs.BOM_UTF16, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16-be"),
    (codecs.BOM_UTF16_LE, "utf-16-le"),
]

PEP263_ENCODING_RE = re.compile(rb"coding[:=]\s*([-\w.]+)")
DEFAULT_ENCODING = "utf-8"

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedRequirement:
    # TODO: replace this with slots=True when dropping Python 3.9 support.
    __slots__ = (
        "requirement",
        "is_editable",
        "comes_from",
        "constraint",
        "options",
        "line_source",
    )

    requirement: str
    is_editable: bool
    comes_from: str
    constraint: bool
    options: dict[str, Any] | None
    line_source: str | None


@dataclass(frozen=True)
class ParsedLine:
    __slots__ = ("filename", "lineno", "args", "opts", "constraint")

    filename: str
    lineno: int
    args: str
    opts: Values
    constraint: bool

    @property
    def is_editable(self) -> bool:
        return bool(self.opts.editables)

    @property
    def requirement(self) -> str | None:
        if self.args:
            return self.args
        elif self.is_editable:
            # We don't support multiple -e on one line
            return self.opts.editables[0]
        return None


def parse_requirements(
    filename: str,
    session: PipSession,
    finder: PackageFinder | None = None,
    options: optparse.Values | None = None,
    constraint: bool = False,
) -> Generator[ParsedRequirement, None, None]:
    """Parse a requirements file and yield ParsedRequirement instances.

    :param filename:    Path or url of requirements file.
    :param session:     PipSession instance.
    :param finder:      Instance of pip.index.PackageFinder.
    :param options:     cli options.
    :param constraint:  If true, parsing a constraint file rather than
        requirements file.
    """
    line_parser = get_line_parser(finder)
    parser = RequirementsFileParser(session, line_parser)

    for parsed_line in parser.parse(filename, constraint):
        parsed_req = handle_line(
            parsed_line, options=options, finder=finder, session=session
        )
        if parsed_req is not None:
            yield parsed_req


def preprocess(content: str) -> ReqFileLines:
    """Split, filter, and join lines, and return a line iterator

    :param content: the content of the requirements file
    """
    lines_enum: ReqFileLines = enumerate(content.splitlines(), start=1)
    lines_enum = join_lines(lines_enum)
    lines_enum = ignore_comments(lines_enum)
    lines_enum = expand_env_variables(lines_enum)
    return lines_enum


def handle_requirement_line(
    line: ParsedLine,
    options: optparse.Values | None = None,
) -> ParsedRequirement:
    # preserve for the nested code path
    line_comes_from = "{} {} (line {})".format(
        "-c" if line.constraint else "-r",
        line.filename,
        line.lineno,
    )

    assert line.requirement is not None

    # get the options that apply to requirements
    if line.is_editable:
        supported_dest = SUPPORTED_OPTIONS_EDITABLE_REQ_DEST
    else:
        supported_dest = SUPPORTED_OPTIONS_REQ_DEST
    req_options = {}
    for dest in supported_dest:
        if dest in line.opts.__dict__ and line.opts.__dict__[dest]:
            req_options[dest] = line.opts.__dict__[dest]

    line_source = f"line {line.lineno} of {line.filename}"
    return ParsedRequirement(
        requirement=line.requirement,
        is_editable=line.is_editable,
        comes_from=line_comes_from,
        constraint=line.constraint,
        options=req_options,
        line_source=line_source,
    )


def handle_option_line(
    opts: Values,
    filename: str,
    lineno: int,
    finder: PackageFinder | None = None,
    options: optparse.Values | None = None,
    session: PipSession | None = None,
) -> None:
    if opts.hashes:
        logger.warning(
            "%s line %s has --hash but no requirement, and will be ignored.",
            filename,
            lineno,
        )

    if options:
        # percolate options upward
        if opts.require_hashes:
            options.require_hashes = opts.require_hashes
        if opts.features_enabled:
            options.features_enabled.extend(
                f for f in opts.features_enabled if f not in options.features_enabled
            )

    # set finder options
    if finder:
        find_links = finder.find_links
        index_urls = finder.index_urls
        no_index = finder.search_scope.no_index
        if opts.no_index is True:
            no_index = True
            index_urls = []
        if opts.index_url and not no_index:
            index_urls = [opts.index_url]
        if opts.extra_index_urls and not no_index:
            index_urls.extend(opts.extra_index_urls)
        if opts.find_links:
            # FIXME: it would be nice to keep track of the source
            # of the find_links: support a find-links local path
            # relative to a requirements file.
            value = opts.find_links[0]
            req_dir = os.path.dirname(os.path.abspath(filename))
            relative_to_reqs_file = os.path.join(req_dir, value)
            if os.path.exists(relative_to_reqs_file):
                value = relative_to_reqs_file
            find_links.append(value)

        if session:
            # We need to update the auth urls in session
            session.update_index_urls(index_urls)

        search_scope = SearchScope(
            find_links=find_links,
            index_urls=index_urls,
            no_index=no_index,
        )
        finder.search_scope = search_scope

        if opts.pre:
            finder.set_allow_all_prereleases()

        if opts.prefer_binary:
            finder.set_prefer_binary()

        if session:
            for host in opts.trusted_hosts or []:
                source = f"line {lineno} of {filename}"
                session.add_trusted_host(host, source=source)


def handle_line(
    line: ParsedLine,
    options: optparse.Values | None = None,
    finder: PackageFinder | None = None,
    session: PipSession | None = None,
) -> ParsedRequirement | None:
    """Handle a single parsed requirements line; This can result in
    creating/yielding requirements, or updating the finder.

    :param line:        The parsed line to be processed.
    :param options:     CLI options.
    :param finder:      The finder - updated by non-requirement lines.
    :param session:     The session - updated by non-requirement lines.

    Returns a ParsedRequirement object if the line is a requirement line,
    otherwise returns None.

    For lines that contain requirements, the only options that have an effect
    are from SUPPORTED_OPTIONS_REQ, and they are scoped to the
    requirement. Other options from SUPPORTED_OPTIONS may be present, but are
    ignored.

    For lines that do not contain requirements, the only options that have an
    effect are from SUPPORTED_OPTIONS. Options from SUPPORTED_OPTIONS_REQ may
    be present, but are ignored. These lines may contain multiple options
    (although our docs imply only one is supported), and all our parsed and
    affect the finder.
    """

    if line.requirement is not None:
        parsed_req = handle_requirement_line(line, options)
        return parsed_req
    else:
        handle_option_line(
            line.opts,
            line.filename,
            line.lineno,
            finder,
            options,
            session,
        )
        return None


class RequirementsFileParser:
    def __init__(
        self,
        session: PipSession,
        line_parser: LineParser,
    ) -> None:
        self._session = session
        self._line_parser = line_parser

    def parse(
        self, filename: str, constraint: bool
    ) -> Generator[ParsedLine, None, None]:
        """Parse a given file, yielding parsed lines."""
        yield from self._parse_and_recurse(
            filename, constraint, [{os.path.abspath(filename): None}]
        )

    def _parse_and_recurse(
        self,
        filename: str,
        constraint: bool,
        parsed_files_stack: list[dict[str, str | None]],
    ) -> Generator[ParsedLine, None, None]:
        for line in self._parse_file(filename, constraint):
            if line.requirement is None and (
                line.opts.requirements or line.opts.constraints
            ):
                # parse a nested requirements file
                if line.opts.requirements:
                    req_path = line.opts.requirements[0]
                    nested_constraint = False
                else:
                    req_path = line.opts.constraints[0]
                    nested_constraint = True

                # original file is over http
                if SCHEME_RE.search(filename):
                    # do a url join so relative paths work
                    req_path = urllib.parse.urljoin(filename, req_path)
                # original file and nested file are paths
                elif not SCHEME_RE.search(req_path):
                    # do a join so relative paths work
                    # and then abspath so that we can identify recursive references
                    req_path = os.path.abspath(
                        os.path.join(
                            os.path.dirname(filename),
                            req_path,
                        )
                    )
                parsed_files = parsed_files_stack[0]
                if req_path in parsed_files:
                    initial_file = parsed_files[req_path]
                    tail = (
                        f" and again in {initial_file}"
                        if initial_file is not None
                        else ""
                    )
                    raise RequirementsFileParseError(
                        f"{req_path} recursively references itself in {filename}{tail}"
                    )
                # Keeping a track where was each file first included in
                new_parsed_files = parsed_files.copy()
                new_parsed_files[req_path] = filename
                yield from self._parse_and_recurse(
                    req_path, nested_constraint, [new_parsed_files, *parsed_files_stack]
                )
            else:
                yield line

    def _parse_file(
        self, filename: str, constraint: bool
    ) -> Generator[ParsedLine, None, None]:
        _, content = get_file_content(filename, self._session)

        lines_enum = preprocess(content)

        for line_number, line in lines_enum:
            try:
                args_str, opts = self._line_parser(line)
            except OptionParsingError as e:
                # add offending line
                msg = f"Invalid requirement: {line}\n{e.msg}"
                raise RequirementsFileParseError(msg)

            yield ParsedLine(
                filename,
                line_number,
                args_str,
                opts,
                constraint,
            )


def get_line_parser(finder: PackageFinder | None) -> LineParser:
    def parse_line(line: str) -> tuple[str, Values]:
        # Build new parser for each line since it accumulates appendable
        # options.
        parser = build_parser()
        defaults = parser.get_default_values()
        defaults.index_url = None
        if finder:
            defaults.format_control = finder.format_control

        args_str, options_str = break_args_options(line)

        try:
            options = shlex.split(options_str)
        except ValueError as e:
            raise OptionParsingError(f"Could not split options: {options_str}") from e

        opts, _ = parser.parse_args(options, defaults)

        return args_str, opts

    return parse_line


def break_args_options(line: str) -> tuple[str, str]:
    """Break up the line into an args and options string.  We only want to shlex
    (and then optparse) the options, not the args.  args can contain markers
    which are corrupted by shlex.
    """
    tokens = line.split(" ")
    args = []
    options = tokens[:]
    for token in tokens:
        if token.startswith(("-", "--")):
            break
        else:
            args.append(token)
            options.pop(0)
    return " ".join(args), " ".join(options)


class OptionParsingError(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg


def build_parser() -> optparse.OptionParser:
    """
    Return a parser for parsing requirement lines
    """
    parser = optparse.OptionParser(add_help_option=False)

    option_factories = SUPPORTED_OPTIONS + SUPPORTED_OPTIONS_REQ
    for option_factory in option_factories:
        option = option_factory()
        parser.add_option(option)

    # By default optparse sys.exits on parsing errors. We want to wrap
    # that in our own exception.
    def parser_exit(self: Any, msg: str) -> NoReturn:
        raise OptionParsingError(msg)

    # NOTE: mypy disallows assigning to a method
    #       https://github.com/python/mypy/issues/2427
    parser.exit = parser_exit  # type: ignore

    return parser


def join_lines(lines_enum: ReqFileLines) -> ReqFileLines:
    """Joins a line ending in '\' with the previous line (except when following
    comments).  The joined line takes on the index of the first line.
    """
    primary_line_number = None
    new_line: list[str] = []
    for line_number, line in lines_enum:
        if not line.endswith("\\") or COMMENT_RE.match(line):
            if COMMENT_RE.match(line):
                # this ensures comments are always matched later
                line = " " + line
            if new_line:
                new_line.append(line)
                assert primary_line_number is not None
                yield primary_line_number, "".join(new_line)
                new_line = []
            else:
                yield line_number, line
        else:
            if not new_line:
                primary_line_number = line_number
            new_line.append(line.strip("\\"))

    # last line contains \
    if new_line:
        assert primary_line_number is not None
        yield primary_line_number, "".join(new_line)

    # TODO: handle space after '\'.


def ignore_comments(lines_enum: ReqFileLines) -> ReqFileLines:
    """
    Strips comments and filter empty lines.
    """
    for line_number, line in lines_enum:
        line = COMMENT_RE.sub("", line)
        line = line.strip()
        if line:
            yield line_number, line


def expand_env_variables(lines_enum: ReqFileLines) -> ReqFileLines:
    """Replace all environment variables that can be retrieved via `os.getenv`.

    The only allowed format for environment variables defined in the
    requirement file is `${MY_VARIABLE_1}` to ensure two things:

    1. Strings that contain a `$` aren't accidentally (partially) expanded.
    2. Ensure consistency across platforms for requirement files.

    These points are the result of a discussion on the `github pull
    request #3514 <https://github.com/pypa/pip/pull/3514>`_.

    Valid characters in variable names follow the `POSIX standard
    <http://pubs.opengroup.org/onlinepubs/9699919799/>`_ and are limited
    to uppercase letter, digits and the `_` (underscore).
    """
    for line_number, line in lines_enum:
        for env_var, var_name in ENV_VAR_RE.findall(line):
            value = os.getenv(var_name)
            if not value:
                continue

            line = line.replace(env_var, value)

        yield line_number, line


def get_file_content(url: str, session: PipSession) -> tuple[str, str]:
    """Gets the content of a file; it may be a filename, file: URL, or
    http: URL.  Returns (location, content).  Content is unicode.
    Respects # -*- coding: declarations on the retrieved files.

    :param url:         File path or url.
    :param session:     PipSession instance.
    """
    scheme = urllib.parse.urlsplit(url).scheme
    # Pip has special support for file:// URLs (LocalFSAdapter).
    if scheme in ["http", "https", "file"]:
        # Delay importing heavy network modules until absolutely necessary.
        from pip._internal.network.utils import raise_for_status

        resp = session.get(url)
        raise_for_status(resp)
        return resp.url, resp.text

    # Assume this is a bare path.
    try:
        with open(url, "rb") as f:
            raw_content = f.read()
    except OSError as exc:
        raise InstallationError(f"Could not open requirements file: {exc}")

    content = _decode_req_file(raw_content, url)

    return url, content


def _decode_req_file(data: bytes, url: str) -> str:
    for bom, encoding in BOMS:
        if data.startswith(bom):
            return data[len(bom) :].decode(encoding)

    for line in data.split(b"\n")[:2]:
        if line[0:1] == b"#":
            result = PEP263_ENCODING_RE.search(line)
            if result is not None:
                encoding = result.groups()[0].decode("ascii")
                return data.decode(encoding)

    try:
        return data.decode(DEFAULT_ENCODING)
    except UnicodeDecodeError:
        locale_encoding = locale.getpreferredencoding(False) or sys.getdefaultencoding()
        logging.warning(
            "unable to decode data from %s with default encoding %s, "
            "falling back to encoding from locale: %s. "
            "If this is intentional you should specify the encoding with a "
            "PEP-263 style comment, e.g. '# -*- coding: %s -*-'",
            url,
            DEFAULT_ENCODING,
            locale_encoding,
            locale_encoding,
        )
        return data.decode(locale_encoding)

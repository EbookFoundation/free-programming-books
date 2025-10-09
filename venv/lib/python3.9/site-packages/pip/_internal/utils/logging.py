from __future__ import annotations

import contextlib
import errno
import logging
import logging.handlers
import os
import sys
import threading
from collections.abc import Generator
from dataclasses import dataclass
from io import TextIOWrapper
from logging import Filter
from typing import Any, ClassVar

from pip._vendor.rich.console import (
    Console,
    ConsoleOptions,
    ConsoleRenderable,
    RenderableType,
    RenderResult,
    RichCast,
)
from pip._vendor.rich.highlighter import NullHighlighter
from pip._vendor.rich.logging import RichHandler
from pip._vendor.rich.segment import Segment
from pip._vendor.rich.style import Style

from pip._internal.utils._log import VERBOSE, getLogger
from pip._internal.utils.compat import WINDOWS
from pip._internal.utils.deprecation import DEPRECATION_MSG_PREFIX
from pip._internal.utils.misc import ensure_dir

_log_state = threading.local()
_stdout_console = None
_stderr_console = None
subprocess_logger = getLogger("pip.subprocessor")


class BrokenStdoutLoggingError(Exception):
    """
    Raised if BrokenPipeError occurs for the stdout stream while logging.
    """


def _is_broken_pipe_error(exc_class: type[BaseException], exc: BaseException) -> bool:
    if exc_class is BrokenPipeError:
        return True

    # On Windows, a broken pipe can show up as EINVAL rather than EPIPE:
    # https://bugs.python.org/issue19612
    # https://bugs.python.org/issue30418
    if not WINDOWS:
        return False

    return isinstance(exc, OSError) and exc.errno in (errno.EINVAL, errno.EPIPE)


@contextlib.contextmanager
def indent_log(num: int = 2) -> Generator[None, None, None]:
    """
    A context manager which will cause the log output to be indented for any
    log messages emitted inside it.
    """
    # For thread-safety
    _log_state.indentation = get_indentation()
    _log_state.indentation += num
    try:
        yield
    finally:
        _log_state.indentation -= num


def get_indentation() -> int:
    return getattr(_log_state, "indentation", 0)


class IndentingFormatter(logging.Formatter):
    default_time_format = "%Y-%m-%dT%H:%M:%S"

    def __init__(
        self,
        *args: Any,
        add_timestamp: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        A logging.Formatter that obeys the indent_log() context manager.

        :param add_timestamp: A bool indicating output lines should be prefixed
            with their record's timestamp.
        """
        self.add_timestamp = add_timestamp
        super().__init__(*args, **kwargs)

    def get_message_start(self, formatted: str, levelno: int) -> str:
        """
        Return the start of the formatted log message (not counting the
        prefix to add to each line).
        """
        if levelno < logging.WARNING:
            return ""
        if formatted.startswith(DEPRECATION_MSG_PREFIX):
            # Then the message already has a prefix.  We don't want it to
            # look like "WARNING: DEPRECATION: ...."
            return ""
        if levelno < logging.ERROR:
            return "WARNING: "

        return "ERROR: "

    def format(self, record: logging.LogRecord) -> str:
        """
        Calls the standard formatter, but will indent all of the log message
        lines by our current indentation level.
        """
        formatted = super().format(record)
        message_start = self.get_message_start(formatted, record.levelno)
        formatted = message_start + formatted

        prefix = ""
        if self.add_timestamp:
            prefix = f"{self.formatTime(record)} "
        prefix += " " * get_indentation()
        formatted = "".join([prefix + line for line in formatted.splitlines(True)])
        return formatted


@dataclass
class IndentedRenderable:
    renderable: RenderableType
    indent: int

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        segments = console.render(self.renderable, options)
        lines = Segment.split_lines(segments)
        for line in lines:
            yield Segment(" " * self.indent)
            yield from line
            yield Segment("\n")


class PipConsole(Console):
    def on_broken_pipe(self) -> None:
        # Reraise the original exception, rich 13.8.0+ exits by default
        # instead, preventing our handler from firing.
        raise BrokenPipeError() from None


def get_console(*, stderr: bool = False) -> Console:
    if stderr:
        assert _stderr_console is not None, "stderr rich console is missing!"
        return _stderr_console
    else:
        assert _stdout_console is not None, "stdout rich console is missing!"
        return _stdout_console


class RichPipStreamHandler(RichHandler):
    KEYWORDS: ClassVar[list[str] | None] = []

    def __init__(self, console: Console) -> None:
        super().__init__(
            console=console,
            show_time=False,
            show_level=False,
            show_path=False,
            highlighter=NullHighlighter(),
        )

    # Our custom override on Rich's logger, to make things work as we need them to.
    def emit(self, record: logging.LogRecord) -> None:
        style: Style | None = None

        # If we are given a diagnostic error to present, present it with indentation.
        if getattr(record, "rich", False):
            assert isinstance(record.args, tuple)
            (rich_renderable,) = record.args
            assert isinstance(
                rich_renderable, (ConsoleRenderable, RichCast, str)
            ), f"{rich_renderable} is not rich-console-renderable"

            renderable: RenderableType = IndentedRenderable(
                rich_renderable, indent=get_indentation()
            )
        else:
            message = self.format(record)
            renderable = self.render_message(record, message)
            if record.levelno is not None:
                if record.levelno >= logging.ERROR:
                    style = Style(color="red")
                elif record.levelno >= logging.WARNING:
                    style = Style(color="yellow")

        try:
            self.console.print(renderable, overflow="ignore", crop=False, style=style)
        except Exception:
            self.handleError(record)

    def handleError(self, record: logging.LogRecord) -> None:
        """Called when logging is unable to log some output."""

        exc_class, exc = sys.exc_info()[:2]
        # If a broken pipe occurred while calling write() or flush() on the
        # stdout stream in logging's Handler.emit(), then raise our special
        # exception so we can handle it in main() instead of logging the
        # broken pipe error and continuing.
        if (
            exc_class
            and exc
            and self.console.file is sys.stdout
            and _is_broken_pipe_error(exc_class, exc)
        ):
            raise BrokenStdoutLoggingError()

        return super().handleError(record)


class BetterRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def _open(self) -> TextIOWrapper:
        ensure_dir(os.path.dirname(self.baseFilename))
        return super()._open()


class MaxLevelFilter(Filter):
    def __init__(self, level: int) -> None:
        self.level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno < self.level


class ExcludeLoggerFilter(Filter):
    """
    A logging Filter that excludes records from a logger (or its children).
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # The base Filter class allows only records from a logger (or its
        # children).
        return not super().filter(record)


def setup_logging(verbosity: int, no_color: bool, user_log_file: str | None) -> int:
    """Configures and sets up all of the logging

    Returns the requested logging level, as its integer value.
    """

    # Determine the level to be logging at.
    if verbosity >= 2:
        level_number = logging.DEBUG
    elif verbosity == 1:
        level_number = VERBOSE
    elif verbosity == -1:
        level_number = logging.WARNING
    elif verbosity == -2:
        level_number = logging.ERROR
    elif verbosity <= -3:
        level_number = logging.CRITICAL
    else:
        level_number = logging.INFO

    level = logging.getLevelName(level_number)

    # The "root" logger should match the "console" level *unless* we also need
    # to log to a user log file.
    include_user_log = user_log_file is not None
    if include_user_log:
        additional_log_file = user_log_file
        root_level = "DEBUG"
    else:
        additional_log_file = "/dev/null"
        root_level = level

    # Disable any logging besides WARNING unless we have DEBUG level logging
    # enabled for vendored libraries.
    vendored_log_level = "WARNING" if level in ["INFO", "ERROR"] else "DEBUG"

    # Shorthands for clarity
    handler_classes = {
        "stream": "pip._internal.utils.logging.RichPipStreamHandler",
        "file": "pip._internal.utils.logging.BetterRotatingFileHandler",
    }
    handlers = ["console", "console_errors", "console_subprocess"] + (
        ["user_log"] if include_user_log else []
    )
    global _stdout_console, stderr_console
    _stdout_console = PipConsole(file=sys.stdout, no_color=no_color, soft_wrap=True)
    _stderr_console = PipConsole(file=sys.stderr, no_color=no_color, soft_wrap=True)

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "exclude_warnings": {
                    "()": "pip._internal.utils.logging.MaxLevelFilter",
                    "level": logging.WARNING,
                },
                "restrict_to_subprocess": {
                    "()": "logging.Filter",
                    "name": subprocess_logger.name,
                },
                "exclude_subprocess": {
                    "()": "pip._internal.utils.logging.ExcludeLoggerFilter",
                    "name": subprocess_logger.name,
                },
            },
            "formatters": {
                "indent": {
                    "()": IndentingFormatter,
                    "format": "%(message)s",
                },
                "indent_with_timestamp": {
                    "()": IndentingFormatter,
                    "format": "%(message)s",
                    "add_timestamp": True,
                },
            },
            "handlers": {
                "console": {
                    "level": level,
                    "class": handler_classes["stream"],
                    "console": _stdout_console,
                    "filters": ["exclude_subprocess", "exclude_warnings"],
                    "formatter": "indent",
                },
                "console_errors": {
                    "level": "WARNING",
                    "class": handler_classes["stream"],
                    "console": _stderr_console,
                    "filters": ["exclude_subprocess"],
                    "formatter": "indent",
                },
                # A handler responsible for logging to the console messages
                # from the "subprocessor" logger.
                "console_subprocess": {
                    "level": level,
                    "class": handler_classes["stream"],
                    "console": _stderr_console,
                    "filters": ["restrict_to_subprocess"],
                    "formatter": "indent",
                },
                "user_log": {
                    "level": "DEBUG",
                    "class": handler_classes["file"],
                    "filename": additional_log_file,
                    "encoding": "utf-8",
                    "delay": True,
                    "formatter": "indent_with_timestamp",
                },
            },
            "root": {
                "level": root_level,
                "handlers": handlers,
            },
            "loggers": {"pip._vendor": {"level": vendored_log_level}},
        }
    )

    return level_number

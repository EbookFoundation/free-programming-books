import inspect
import os
import sys
import threading
import zlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from getpass import getpass
from html import escape
from inspect import isclass
from itertools import islice
from math import ceil
from time import monotonic
from types import FrameType, ModuleType, TracebackType
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Mapping,
    NamedTuple,
    Optional,
    Protocol,
    TextIO,
    Tuple,
    Type,
    Union,
    cast,
    runtime_checkable,
)

from pip._vendor.rich._null_file import NULL_FILE

from . import errors, themes
from ._emoji_replace import _emoji_replace
from ._export_format import CONSOLE_HTML_FORMAT, CONSOLE_SVG_FORMAT
from ._fileno import get_fileno
from ._log_render import FormatTimeCallable, LogRender
from .align import Align, AlignMethod
from .color import ColorSystem, blend_rgb
from .control import Control
from .emoji import EmojiVariant
from .highlighter import NullHighlighter, ReprHighlighter
from .markup import render as render_markup
from .measure import Measurement, measure_renderables
from .pager import Pager, SystemPager
from .pretty import Pretty, is_expandable
from .protocol import rich_cast
from .region import Region
from .scope import render_scope
from .screen import Screen
from .segment import Segment
from .style import Style, StyleType
from .styled import Styled
from .terminal_theme import DEFAULT_TERMINAL_THEME, SVG_EXPORT_THEME, TerminalTheme
from .text import Text, TextType
from .theme import Theme, ThemeStack

if TYPE_CHECKING:
    from ._windows import WindowsConsoleFeatures
    from .live import Live
    from .status import Status

JUPYTER_DEFAULT_COLUMNS = 115
JUPYTER_DEFAULT_LINES = 100
WINDOWS = sys.platform == "win32"

HighlighterType = Callable[[Union[str, "Text"]], "Text"]
JustifyMethod = Literal["default", "left", "center", "right", "full"]
OverflowMethod = Literal["fold", "crop", "ellipsis", "ignore"]


class NoChange:
    pass


NO_CHANGE = NoChange()

try:
    _STDIN_FILENO = sys.__stdin__.fileno()  # type: ignore[union-attr]
except Exception:
    _STDIN_FILENO = 0
try:
    _STDOUT_FILENO = sys.__stdout__.fileno()  # type: ignore[union-attr]
except Exception:
    _STDOUT_FILENO = 1
try:
    _STDERR_FILENO = sys.__stderr__.fileno()  # type: ignore[union-attr]
except Exception:
    _STDERR_FILENO = 2

_STD_STREAMS = (_STDIN_FILENO, _STDOUT_FILENO, _STDERR_FILENO)
_STD_STREAMS_OUTPUT = (_STDOUT_FILENO, _STDERR_FILENO)


_TERM_COLORS = {
    "kitty": ColorSystem.EIGHT_BIT,
    "256color": ColorSystem.EIGHT_BIT,
    "16color": ColorSystem.STANDARD,
}


class ConsoleDimensions(NamedTuple):
    """Size of the terminal."""

    width: int
    """The width of the console in 'cells'."""
    height: int
    """The height of the console in lines."""


@dataclass
class ConsoleOptions:
    """Options for __rich_console__ method."""

    size: ConsoleDimensions
    """Size of console."""
    legacy_windows: bool
    """legacy_windows: flag for legacy windows."""
    min_width: int
    """Minimum width of renderable."""
    max_width: int
    """Maximum width of renderable."""
    is_terminal: bool
    """True if the target is a terminal, otherwise False."""
    encoding: str
    """Encoding of terminal."""
    max_height: int
    """Height of container (starts as terminal)"""
    justify: Optional[JustifyMethod] = None
    """Justify value override for renderable."""
    overflow: Optional[OverflowMethod] = None
    """Overflow value override for renderable."""
    no_wrap: Optional[bool] = False
    """Disable wrapping for text."""
    highlight: Optional[bool] = None
    """Highlight override for render_str."""
    markup: Optional[bool] = None
    """Enable markup when rendering strings."""
    height: Optional[int] = None

    @property
    def ascii_only(self) -> bool:
        """Check if renderables should use ascii only."""
        return not self.encoding.startswith("utf")

    def copy(self) -> "ConsoleOptions":
        """Return a copy of the options.

        Returns:
            ConsoleOptions: a copy of self.
        """
        options: ConsoleOptions = ConsoleOptions.__new__(ConsoleOptions)
        options.__dict__ = self.__dict__.copy()
        return options

    def update(
        self,
        *,
        width: Union[int, NoChange] = NO_CHANGE,
        min_width: Union[int, NoChange] = NO_CHANGE,
        max_width: Union[int, NoChange] = NO_CHANGE,
        justify: Union[Optional[JustifyMethod], NoChange] = NO_CHANGE,
        overflow: Union[Optional[OverflowMethod], NoChange] = NO_CHANGE,
        no_wrap: Union[Optional[bool], NoChange] = NO_CHANGE,
        highlight: Union[Optional[bool], NoChange] = NO_CHANGE,
        markup: Union[Optional[bool], NoChange] = NO_CHANGE,
        height: Union[Optional[int], NoChange] = NO_CHANGE,
    ) -> "ConsoleOptions":
        """Update values, return a copy."""
        options = self.copy()
        if not isinstance(width, NoChange):
            options.min_width = options.max_width = max(0, width)
        if not isinstance(min_width, NoChange):
            options.min_width = min_width
        if not isinstance(max_width, NoChange):
            options.max_width = max_width
        if not isinstance(justify, NoChange):
            options.justify = justify
        if not isinstance(overflow, NoChange):
            options.overflow = overflow
        if not isinstance(no_wrap, NoChange):
            options.no_wrap = no_wrap
        if not isinstance(highlight, NoChange):
            options.highlight = highlight
        if not isinstance(markup, NoChange):
            options.markup = markup
        if not isinstance(height, NoChange):
            if height is not None:
                options.max_height = height
            options.height = None if height is None else max(0, height)
        return options

    def update_width(self, width: int) -> "ConsoleOptions":
        """Update just the width, return a copy.

        Args:
            width (int): New width (sets both min_width and max_width)

        Returns:
            ~ConsoleOptions: New console options instance.
        """
        options = self.copy()
        options.min_width = options.max_width = max(0, width)
        return options

    def update_height(self, height: int) -> "ConsoleOptions":
        """Update the height, and return a copy.

        Args:
            height (int): New height

        Returns:
            ~ConsoleOptions: New Console options instance.
        """
        options = self.copy()
        options.max_height = options.height = height
        return options

    def reset_height(self) -> "ConsoleOptions":
        """Return a copy of the options with height set to ``None``.

        Returns:
            ~ConsoleOptions: New console options instance.
        """
        options = self.copy()
        options.height = None
        return options

    def update_dimensions(self, width: int, height: int) -> "ConsoleOptions":
        """Update the width and height, and return a copy.

        Args:
            width (int): New width (sets both min_width and max_width).
            height (int): New height.

        Returns:
            ~ConsoleOptions: New console options instance.
        """
        options = self.copy()
        options.min_width = options.max_width = max(0, width)
        options.height = options.max_height = height
        return options


@runtime_checkable
class RichCast(Protocol):
    """An object that may be 'cast' to a console renderable."""

    def __rich__(
        self,
    ) -> Union["ConsoleRenderable", "RichCast", str]:  # pragma: no cover
        ...


@runtime_checkable
class ConsoleRenderable(Protocol):
    """An object that supports the console protocol."""

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> "RenderResult":  # pragma: no cover
        ...


# A type that may be rendered by Console.
RenderableType = Union[ConsoleRenderable, RichCast, str]
"""A string or any object that may be rendered by Rich."""

# The result of calling a __rich_console__ method.
RenderResult = Iterable[Union[RenderableType, Segment]]

_null_highlighter = NullHighlighter()


class CaptureError(Exception):
    """An error in the Capture context manager."""


class NewLine:
    """A renderable to generate new line(s)"""

    def __init__(self, count: int = 1) -> None:
        self.count = count

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> Iterable[Segment]:
        yield Segment("\n" * self.count)


class ScreenUpdate:
    """Render a list of lines at a given offset."""

    def __init__(self, lines: List[List[Segment]], x: int, y: int) -> None:
        self._lines = lines
        self.x = x
        self.y = y

    def __rich_console__(
        self, console: "Console", options: ConsoleOptions
    ) -> RenderResult:
        x = self.x
        move_to = Control.move_to
        for offset, line in enumerate(self._lines, self.y):
            yield move_to(x, offset)
            yield from line


class Capture:
    """Context manager to capture the result of printing to the console.
    See :meth:`~rich.console.Console.capture` for how to use.

    Args:
        console (Console): A console instance to capture output.
    """

    def __init__(self, console: "Console") -> None:
        self._console = console
        self._result: Optional[str] = None

    def __enter__(self) -> "Capture":
        self._console.begin_capture()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self._result = self._console.end_capture()

    def get(self) -> str:
        """Get the result of the capture."""
        if self._result is None:
            raise CaptureError(
                "Capture result is not available until context manager exits."
            )
        return self._result


class ThemeContext:
    """A context manager to use a temporary theme. See :meth:`~rich.console.Console.use_theme` for usage."""

    def __init__(self, console: "Console", theme: Theme, inherit: bool = True) -> None:
        self.console = console
        self.theme = theme
        self.inherit = inherit

    def __enter__(self) -> "ThemeContext":
        self.console.push_theme(self.theme)
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.console.pop_theme()


class PagerContext:
    """A context manager that 'pages' content. See :meth:`~rich.console.Console.pager` for usage."""

    def __init__(
        self,
        console: "Console",
        pager: Optional[Pager] = None,
        styles: bool = False,
        links: bool = False,
    ) -> None:
        self._console = console
        self.pager = SystemPager() if pager is None else pager
        self.styles = styles
        self.links = links

    def __enter__(self) -> "PagerContext":
        self._console._enter_buffer()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if exc_type is None:
            with self._console._lock:
                buffer: List[Segment] = self._console._buffer[:]
                del self._console._buffer[:]
                segments: Iterable[Segment] = buffer
                if not self.styles:
                    segments = Segment.strip_styles(segments)
                elif not self.links:
                    segments = Segment.strip_links(segments)
                content = self._console._render_buffer(segments)
            self.pager.show(content)
        self._console._exit_buffer()


class ScreenContext:
    """A context manager that enables an alternative screen. See :meth:`~rich.console.Console.screen` for usage."""

    def __init__(
        self, console: "Console", hide_cursor: bool, style: StyleType = ""
    ) -> None:
        self.console = console
        self.hide_cursor = hide_cursor
        self.screen = Screen(style=style)
        self._changed = False

    def update(
        self, *renderables: RenderableType, style: Optional[StyleType] = None
    ) -> None:
        """Update the screen.

        Args:
            renderable (RenderableType, optional): Optional renderable to replace current renderable,
                or None for no change. Defaults to None.
            style: (Style, optional): Replacement style, or None for no change. Defaults to None.
        """
        if renderables:
            self.screen.renderable = (
                Group(*renderables) if len(renderables) > 1 else renderables[0]
            )
        if style is not None:
            self.screen.style = style
        self.console.print(self.screen, end="")

    def __enter__(self) -> "ScreenContext":
        self._changed = self.console.set_alt_screen(True)
        if self._changed and self.hide_cursor:
            self.console.show_cursor(False)
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self._changed:
            self.console.set_alt_screen(False)
            if self.hide_cursor:
                self.console.show_cursor(True)


class Group:
    """Takes a group of renderables and returns a renderable object that renders the group.

    Args:
        renderables (Iterable[RenderableType]): An iterable of renderable objects.
        fit (bool, optional): Fit dimension of group to contents, or fill available space. Defaults to True.
    """

    def __init__(self, *renderables: "RenderableType", fit: bool = True) -> None:
        self._renderables = renderables
        self.fit = fit
        self._render: Optional[List[RenderableType]] = None

    @property
    def renderables(self) -> List["RenderableType"]:
        if self._render is None:
            self._render = list(self._renderables)
        return self._render

    def __rich_measure__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> "Measurement":
        if self.fit:
            return measure_renderables(console, options, self.renderables)
        else:
            return Measurement(options.max_width, options.max_width)

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> RenderResult:
        yield from self.renderables


def group(fit: bool = True) -> Callable[..., Callable[..., Group]]:
    """A decorator that turns an iterable of renderables in to a group.

    Args:
        fit (bool, optional): Fit dimension of group to contents, or fill available space. Defaults to True.
    """

    def decorator(
        method: Callable[..., Iterable[RenderableType]],
    ) -> Callable[..., Group]:
        """Convert a method that returns an iterable of renderables in to a Group."""

        @wraps(method)
        def _replace(*args: Any, **kwargs: Any) -> Group:
            renderables = method(*args, **kwargs)
            return Group(*renderables, fit=fit)

        return _replace

    return decorator


def _is_jupyter() -> bool:  # pragma: no cover
    """Check if we're running in a Jupyter notebook."""
    try:
        get_ipython  # type: ignore[name-defined]
    except NameError:
        return False
    ipython = get_ipython()  # type: ignore[name-defined]
    shell = ipython.__class__.__name__
    if (
        "google.colab" in str(ipython.__class__)
        or os.getenv("DATABRICKS_RUNTIME_VERSION")
        or shell == "ZMQInteractiveShell"
    ):
        return True  # Jupyter notebook or qtconsole
    elif shell == "TerminalInteractiveShell":
        return False  # Terminal running IPython
    else:
        return False  # Other type (?)


COLOR_SYSTEMS = {
    "standard": ColorSystem.STANDARD,
    "256": ColorSystem.EIGHT_BIT,
    "truecolor": ColorSystem.TRUECOLOR,
    "windows": ColorSystem.WINDOWS,
}

_COLOR_SYSTEMS_NAMES = {system: name for name, system in COLOR_SYSTEMS.items()}


@dataclass
class ConsoleThreadLocals(threading.local):
    """Thread local values for Console context."""

    theme_stack: ThemeStack
    buffer: List[Segment] = field(default_factory=list)
    buffer_index: int = 0


class RenderHook(ABC):
    """Provides hooks in to the render process."""

    @abstractmethod
    def process_renderables(
        self, renderables: List[ConsoleRenderable]
    ) -> List[ConsoleRenderable]:
        """Called with a list of objects to render.

        This method can return a new list of renderables, or modify and return the same list.

        Args:
            renderables (List[ConsoleRenderable]): A number of renderable objects.

        Returns:
            List[ConsoleRenderable]: A replacement list of renderables.
        """


_windows_console_features: Optional["WindowsConsoleFeatures"] = None


def get_windows_console_features() -> "WindowsConsoleFeatures":  # pragma: no cover
    global _windows_console_features
    if _windows_console_features is not None:
        return _windows_console_features
    from ._windows import get_windows_console_features

    _windows_console_features = get_windows_console_features()
    return _windows_console_features


def detect_legacy_windows() -> bool:
    """Detect legacy Windows."""
    return WINDOWS and not get_windows_console_features().vt


class Console:
    """A high level console interface.

    Args:
        color_system (str, optional): The color system supported by your terminal,
            either ``"standard"``, ``"256"`` or ``"truecolor"``. Leave as ``"auto"`` to autodetect.
        force_terminal (Optional[bool], optional): Enable/disable terminal control codes, or None to auto-detect terminal. Defaults to None.
        force_jupyter (Optional[bool], optional): Enable/disable Jupyter rendering, or None to auto-detect Jupyter. Defaults to None.
        force_interactive (Optional[bool], optional): Enable/disable interactive mode, or None to auto detect. Defaults to None.
        soft_wrap (Optional[bool], optional): Set soft wrap default on print method. Defaults to False.
        theme (Theme, optional): An optional style theme object, or ``None`` for default theme.
        stderr (bool, optional): Use stderr rather than stdout if ``file`` is not specified. Defaults to False.
        file (IO, optional): A file object where the console should write to. Defaults to stdout.
        quiet (bool, Optional): Boolean to suppress all output. Defaults to False.
        width (int, optional): The width of the terminal. Leave as default to auto-detect width.
        height (int, optional): The height of the terminal. Leave as default to auto-detect height.
        style (StyleType, optional): Style to apply to all output, or None for no style. Defaults to None.
        no_color (Optional[bool], optional): Enabled no color mode, or None to auto detect. Defaults to None.
        tab_size (int, optional): Number of spaces used to replace a tab character. Defaults to 8.
        record (bool, optional): Boolean to enable recording of terminal output,
            required to call :meth:`export_html`, :meth:`export_svg`, and :meth:`export_text`. Defaults to False.
        markup (bool, optional): Boolean to enable :ref:`console_markup`. Defaults to True.
        emoji (bool, optional): Enable emoji code. Defaults to True.
        emoji_variant (str, optional): Optional emoji variant, either "text" or "emoji". Defaults to None.
        highlight (bool, optional): Enable automatic highlighting. Defaults to True.
        log_time (bool, optional): Boolean to enable logging of time by :meth:`log` methods. Defaults to True.
        log_path (bool, optional): Boolean to enable the logging of the caller by :meth:`log`. Defaults to True.
        log_time_format (Union[str, TimeFormatterCallable], optional): If ``log_time`` is enabled, either string for strftime or callable that formats the time. Defaults to "[%X] ".
        highlighter (HighlighterType, optional): Default highlighter.
        legacy_windows (bool, optional): Enable legacy Windows mode, or ``None`` to auto detect. Defaults to ``None``.
        safe_box (bool, optional): Restrict box options that don't render on legacy Windows.
        get_datetime (Callable[[], datetime], optional): Callable that gets the current time as a datetime.datetime object (used by Console.log),
            or None for datetime.now.
        get_time (Callable[[], time], optional): Callable that gets the current time in seconds, default uses time.monotonic.
    """

    _environ: Mapping[str, str] = os.environ

    def __init__(
        self,
        *,
        color_system: Optional[
            Literal["auto", "standard", "256", "truecolor", "windows"]
        ] = "auto",
        force_terminal: Optional[bool] = None,
        force_jupyter: Optional[bool] = None,
        force_interactive: Optional[bool] = None,
        soft_wrap: bool = False,
        theme: Optional[Theme] = None,
        stderr: bool = False,
        file: Optional[IO[str]] = None,
        quiet: bool = False,
        width: Optional[int] = None,
        height: Optional[int] = None,
        style: Optional[StyleType] = None,
        no_color: Optional[bool] = None,
        tab_size: int = 8,
        record: bool = False,
        markup: bool = True,
        emoji: bool = True,
        emoji_variant: Optional[EmojiVariant] = None,
        highlight: bool = True,
        log_time: bool = True,
        log_path: bool = True,
        log_time_format: Union[str, FormatTimeCallable] = "[%X]",
        highlighter: Optional["HighlighterType"] = ReprHighlighter(),
        legacy_windows: Optional[bool] = None,
        safe_box: bool = True,
        get_datetime: Optional[Callable[[], datetime]] = None,
        get_time: Optional[Callable[[], float]] = None,
        _environ: Optional[Mapping[str, str]] = None,
    ):
        # Copy of os.environ allows us to replace it for testing
        if _environ is not None:
            self._environ = _environ

        self.is_jupyter = _is_jupyter() if force_jupyter is None else force_jupyter
        if self.is_jupyter:
            if width is None:
                jupyter_columns = self._environ.get("JUPYTER_COLUMNS")
                if jupyter_columns is not None and jupyter_columns.isdigit():
                    width = int(jupyter_columns)
                else:
                    width = JUPYTER_DEFAULT_COLUMNS
            if height is None:
                jupyter_lines = self._environ.get("JUPYTER_LINES")
                if jupyter_lines is not None and jupyter_lines.isdigit():
                    height = int(jupyter_lines)
                else:
                    height = JUPYTER_DEFAULT_LINES

        self.tab_size = tab_size
        self.record = record
        self._markup = markup
        self._emoji = emoji
        self._emoji_variant: Optional[EmojiVariant] = emoji_variant
        self._highlight = highlight
        self.legacy_windows: bool = (
            (detect_legacy_windows() and not self.is_jupyter)
            if legacy_windows is None
            else legacy_windows
        )

        if width is None:
            columns = self._environ.get("COLUMNS")
            if columns is not None and columns.isdigit():
                width = int(columns) - self.legacy_windows
        if height is None:
            lines = self._environ.get("LINES")
            if lines is not None and lines.isdigit():
                height = int(lines)

        self.soft_wrap = soft_wrap
        self._width = width
        self._height = height

        self._color_system: Optional[ColorSystem]

        self._force_terminal = None
        if force_terminal is not None:
            self._force_terminal = force_terminal

        self._file = file
        self.quiet = quiet
        self.stderr = stderr

        if color_system is None:
            self._color_system = None
        elif color_system == "auto":
            self._color_system = self._detect_color_system()
        else:
            self._color_system = COLOR_SYSTEMS[color_system]

        self._lock = threading.RLock()
        self._log_render = LogRender(
            show_time=log_time,
            show_path=log_path,
            time_format=log_time_format,
        )
        self.highlighter: HighlighterType = highlighter or _null_highlighter
        self.safe_box = safe_box
        self.get_datetime = get_datetime or datetime.now
        self.get_time = get_time or monotonic
        self.style = style
        self.no_color = (
            no_color
            if no_color is not None
            else self._environ.get("NO_COLOR", "") != ""
        )
        if force_interactive is None:
            tty_interactive = self._environ.get("TTY_INTERACTIVE", None)
            if tty_interactive is not None:
                if tty_interactive == "0":
                    force_interactive = False
                elif tty_interactive == "1":
                    force_interactive = True

        self.is_interactive = (
            (self.is_terminal and not self.is_dumb_terminal)
            if force_interactive is None
            else force_interactive
        )

        self._record_buffer_lock = threading.RLock()
        self._thread_locals = ConsoleThreadLocals(
            theme_stack=ThemeStack(themes.DEFAULT if theme is None else theme)
        )
        self._record_buffer: List[Segment] = []
        self._render_hooks: List[RenderHook] = []
        self._live_stack: List[Live] = []
        self._is_alt_screen = False

    def __repr__(self) -> str:
        return f"<console width={self.width} {self._color_system!s}>"

    @property
    def file(self) -> IO[str]:
        """Get the file object to write to."""
        file = self._file or (sys.stderr if self.stderr else sys.stdout)
        file = getattr(file, "rich_proxied_file", file)
        if file is None:
            file = NULL_FILE
        return file

    @file.setter
    def file(self, new_file: IO[str]) -> None:
        """Set a new file object."""
        self._file = new_file

    @property
    def _buffer(self) -> List[Segment]:
        """Get a thread local buffer."""
        return self._thread_locals.buffer

    @property
    def _buffer_index(self) -> int:
        """Get a thread local buffer."""
        return self._thread_locals.buffer_index

    @_buffer_index.setter
    def _buffer_index(self, value: int) -> None:
        self._thread_locals.buffer_index = value

    @property
    def _theme_stack(self) -> ThemeStack:
        """Get the thread local theme stack."""
        return self._thread_locals.theme_stack

    def _detect_color_system(self) -> Optional[ColorSystem]:
        """Detect color system from env vars."""
        if self.is_jupyter:
            return ColorSystem.TRUECOLOR
        if not self.is_terminal or self.is_dumb_terminal:
            return None
        if WINDOWS:  # pragma: no cover
            if self.legacy_windows:  # pragma: no cover
                return ColorSystem.WINDOWS
            windows_console_features = get_windows_console_features()
            return (
                ColorSystem.TRUECOLOR
                if windows_console_features.truecolor
                else ColorSystem.EIGHT_BIT
            )
        else:
            color_term = self._environ.get("COLORTERM", "").strip().lower()
            if color_term in ("truecolor", "24bit"):
                return ColorSystem.TRUECOLOR
            term = self._environ.get("TERM", "").strip().lower()
            _term_name, _hyphen, colors = term.rpartition("-")
            color_system = _TERM_COLORS.get(colors, ColorSystem.STANDARD)
            return color_system

    def _enter_buffer(self) -> None:
        """Enter in to a buffer context, and buffer all output."""
        self._buffer_index += 1

    def _exit_buffer(self) -> None:
        """Leave buffer context, and render content if required."""
        self._buffer_index -= 1
        self._check_buffer()

    def set_live(self, live: "Live") -> bool:
        """Set Live instance. Used by Live context manager (no need to call directly).

        Args:
            live (Live): Live instance using this Console.

        Returns:
            Boolean that indicates if the live is the topmost of the stack.

        Raises:
            errors.LiveError: If this Console has a Live context currently active.
        """
        with self._lock:
            self._live_stack.append(live)
            return len(self._live_stack) == 1

    def clear_live(self) -> None:
        """Clear the Live instance. Used by the Live context manager (no need to call directly)."""
        with self._lock:
            self._live_stack.pop()

    def push_render_hook(self, hook: RenderHook) -> None:
        """Add a new render hook to the stack.

        Args:
            hook (RenderHook): Render hook instance.
        """
        with self._lock:
            self._render_hooks.append(hook)

    def pop_render_hook(self) -> None:
        """Pop the last renderhook from the stack."""
        with self._lock:
            self._render_hooks.pop()

    def __enter__(self) -> "Console":
        """Own context manager to enter buffer context."""
        self._enter_buffer()
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Exit buffer context."""
        self._exit_buffer()

    def begin_capture(self) -> None:
        """Begin capturing console output. Call :meth:`end_capture` to exit capture mode and return output."""
        self._enter_buffer()

    def end_capture(self) -> str:
        """End capture mode and return captured string.

        Returns:
            str: Console output.
        """
        render_result = self._render_buffer(self._buffer)
        del self._buffer[:]
        self._exit_buffer()
        return render_result

    def push_theme(self, theme: Theme, *, inherit: bool = True) -> None:
        """Push a new theme on to the top of the stack, replacing the styles from the previous theme.
        Generally speaking, you should call :meth:`~rich.console.Console.use_theme` to get a context manager, rather
        than calling this method directly.

        Args:
            theme (Theme): A theme instance.
            inherit (bool, optional): Inherit existing styles. Defaults to True.
        """
        self._theme_stack.push_theme(theme, inherit=inherit)

    def pop_theme(self) -> None:
        """Remove theme from top of stack, restoring previous theme."""
        self._theme_stack.pop_theme()

    def use_theme(self, theme: Theme, *, inherit: bool = True) -> ThemeContext:
        """Use a different theme for the duration of the context manager.

        Args:
            theme (Theme): Theme instance to user.
            inherit (bool, optional): Inherit existing console styles. Defaults to True.

        Returns:
            ThemeContext: [description]
        """
        return ThemeContext(self, theme, inherit)

    @property
    def color_system(self) -> Optional[str]:
        """Get color system string.

        Returns:
            Optional[str]: "standard", "256" or "truecolor".
        """

        if self._color_system is not None:
            return _COLOR_SYSTEMS_NAMES[self._color_system]
        else:
            return None

    @property
    def encoding(self) -> str:
        """Get the encoding of the console file, e.g. ``"utf-8"``.

        Returns:
            str: A standard encoding string.
        """
        return (getattr(self.file, "encoding", "utf-8") or "utf-8").lower()

    @property
    def is_terminal(self) -> bool:
        """Check if the console is writing to a terminal.

        Returns:
            bool: True if the console writing to a device capable of
                understanding escape sequences, otherwise False.
        """
        # If dev has explicitly set this value, return it
        if self._force_terminal is not None:
            return self._force_terminal

        # Fudge for Idle
        if hasattr(sys.stdin, "__module__") and sys.stdin.__module__.startswith(
            "idlelib"
        ):
            # Return False for Idle which claims to be a tty but can't handle ansi codes
            return False

        if self.is_jupyter:
            # return False for Jupyter, which may have FORCE_COLOR set
            return False

        environ = self._environ

        tty_compatible = environ.get("TTY_COMPATIBLE", "")
        # 0 indicates device is not tty compatible
        if tty_compatible == "0":
            return False
        # 1 indicates device is tty compatible
        if tty_compatible == "1":
            return True

        # https://force-color.org/
        force_color = environ.get("FORCE_COLOR")
        if force_color is not None:
            return force_color != ""

        # Any other value defaults to auto detect
        isatty: Optional[Callable[[], bool]] = getattr(self.file, "isatty", None)
        try:
            return False if isatty is None else isatty()
        except ValueError:
            # in some situation (at the end of a pytest run for example) isatty() can raise
            # ValueError: I/O operation on closed file
            # return False because we aren't in a terminal anymore
            return False

    @property
    def is_dumb_terminal(self) -> bool:
        """Detect dumb terminal.

        Returns:
            bool: True if writing to a dumb terminal, otherwise False.

        """
        _term = self._environ.get("TERM", "")
        is_dumb = _term.lower() in ("dumb", "unknown")
        return self.is_terminal and is_dumb

    @property
    def options(self) -> ConsoleOptions:
        """Get default console options."""
        size = self.size
        return ConsoleOptions(
            max_height=size.height,
            size=size,
            legacy_windows=self.legacy_windows,
            min_width=1,
            max_width=size.width,
            encoding=self.encoding,
            is_terminal=self.is_terminal,
        )

    @property
    def size(self) -> ConsoleDimensions:
        """Get the size of the console.

        Returns:
            ConsoleDimensions: A named tuple containing the dimensions.
        """

        if self._width is not None and self._height is not None:
            return ConsoleDimensions(self._width - self.legacy_windows, self._height)

        if self.is_dumb_terminal:
            return ConsoleDimensions(80, 25)

        width: Optional[int] = None
        height: Optional[int] = None

        streams = _STD_STREAMS_OUTPUT if WINDOWS else _STD_STREAMS
        for file_descriptor in streams:
            try:
                width, height = os.get_terminal_size(file_descriptor)
            except (AttributeError, ValueError, OSError):  # Probably not a terminal
                pass
            else:
                break

        columns = self._environ.get("COLUMNS")
        if columns is not None and columns.isdigit():
            width = int(columns)
        lines = self._environ.get("LINES")
        if lines is not None and lines.isdigit():
            height = int(lines)

        # get_terminal_size can report 0, 0 if run from pseudo-terminal
        width = width or 80
        height = height or 25
        return ConsoleDimensions(
            width - self.legacy_windows if self._width is None else self._width,
            height if self._height is None else self._height,
        )

    @size.setter
    def size(self, new_size: Tuple[int, int]) -> None:
        """Set a new size for the terminal.

        Args:
            new_size (Tuple[int, int]): New width and height.
        """
        width, height = new_size
        self._width = width
        self._height = height

    @property
    def width(self) -> int:
        """Get the width of the console.

        Returns:
            int: The width (in characters) of the console.
        """
        return self.size.width

    @width.setter
    def width(self, width: int) -> None:
        """Set width.

        Args:
            width (int): New width.
        """
        self._width = width

    @property
    def height(self) -> int:
        """Get the height of the console.

        Returns:
            int: The height (in lines) of the console.
        """
        return self.size.height

    @height.setter
    def height(self, height: int) -> None:
        """Set height.

        Args:
            height (int): new height.
        """
        self._height = height

    def bell(self) -> None:
        """Play a 'bell' sound (if supported by the terminal)."""
        self.control(Control.bell())

    def capture(self) -> Capture:
        """A context manager to *capture* the result of print() or log() in a string,
        rather than writing it to the console.

        Example:
            >>> from rich.console import Console
            >>> console = Console()
            >>> with console.capture() as capture:
            ...     console.print("[bold magenta]Hello World[/]")
            >>> print(capture.get())

        Returns:
            Capture: Context manager with disables writing to the terminal.
        """
        capture = Capture(self)
        return capture

    def pager(
        self, pager: Optional[Pager] = None, styles: bool = False, links: bool = False
    ) -> PagerContext:
        """A context manager to display anything printed within a "pager". The pager application
        is defined by the system and will typically support at least pressing a key to scroll.

        Args:
            pager (Pager, optional): A pager object, or None to use :class:`~rich.pager.SystemPager`. Defaults to None.
            styles (bool, optional): Show styles in pager. Defaults to False.
            links (bool, optional): Show links in pager. Defaults to False.

        Example:
            >>> from rich.console import Console
            >>> from rich.__main__ import make_test_card
            >>> console = Console()
            >>> with console.pager():
                    console.print(make_test_card())

        Returns:
            PagerContext: A context manager.
        """
        return PagerContext(self, pager=pager, styles=styles, links=links)

    def line(self, count: int = 1) -> None:
        """Write new line(s).

        Args:
            count (int, optional): Number of new lines. Defaults to 1.
        """

        assert count >= 0, "count must be >= 0"
        self.print(NewLine(count))

    def clear(self, home: bool = True) -> None:
        """Clear the screen.

        Args:
            home (bool, optional): Also move the cursor to 'home' position. Defaults to True.
        """
        if home:
            self.control(Control.clear(), Control.home())
        else:
            self.control(Control.clear())

    def status(
        self,
        status: RenderableType,
        *,
        spinner: str = "dots",
        spinner_style: StyleType = "status.spinner",
        speed: float = 1.0,
        refresh_per_second: float = 12.5,
    ) -> "Status":
        """Display a status and spinner.

        Args:
            status (RenderableType): A status renderable (str or Text typically).
            spinner (str, optional): Name of spinner animation (see python -m rich.spinner). Defaults to "dots".
            spinner_style (StyleType, optional): Style of spinner. Defaults to "status.spinner".
            speed (float, optional): Speed factor for spinner animation. Defaults to 1.0.
            refresh_per_second (float, optional): Number of refreshes per second. Defaults to 12.5.

        Returns:
            Status: A Status object that may be used as a context manager.
        """
        from .status import Status

        status_renderable = Status(
            status,
            console=self,
            spinner=spinner,
            spinner_style=spinner_style,
            speed=speed,
            refresh_per_second=refresh_per_second,
        )
        return status_renderable

    def show_cursor(self, show: bool = True) -> bool:
        """Show or hide the cursor.

        Args:
            show (bool, optional): Set visibility of the cursor.
        """
        if self.is_terminal:
            self.control(Control.show_cursor(show))
            return True
        return False

    def set_alt_screen(self, enable: bool = True) -> bool:
        """Enables alternative screen mode.

        Note, if you enable this mode, you should ensure that is disabled before
        the application exits. See :meth:`~rich.Console.screen` for a context manager
        that handles this for you.

        Args:
            enable (bool, optional): Enable (True) or disable (False) alternate screen. Defaults to True.

        Returns:
            bool: True if the control codes were written.

        """
        changed = False
        if self.is_terminal and not self.legacy_windows:
            self.control(Control.alt_screen(enable))
            changed = True
            self._is_alt_screen = enable
        return changed

    @property
    def is_alt_screen(self) -> bool:
        """Check if the alt screen was enabled.

        Returns:
            bool: True if the alt screen was enabled, otherwise False.
        """
        return self._is_alt_screen

    def set_window_title(self, title: str) -> bool:
        """Set the title of the console terminal window.

        Warning: There is no means within Rich of "resetting" the window title to its
        previous value, meaning the title you set will persist even after your application
        exits.

        ``fish`` shell resets the window title before and after each command by default,
        negating this issue. Windows Terminal and command prompt will also reset the title for you.
        Most other shells and terminals, however, do not do this.

        Some terminals may require configuration changes before you can set the title.
        Some terminals may not support setting the title at all.

        Other software (including the terminal itself, the shell, custom prompts, plugins, etc.)
        may also set the terminal window title. This could result in whatever value you write
        using this method being overwritten.

        Args:
            title (str): The new title of the terminal window.

        Returns:
            bool: True if the control code to change the terminal title was
                written, otherwise False. Note that a return value of True
                does not guarantee that the window title has actually changed,
                since the feature may be unsupported/disabled in some terminals.
        """
        if self.is_terminal:
            self.control(Control.title(title))
            return True
        return False

    def screen(
        self, hide_cursor: bool = True, style: Optional[StyleType] = None
    ) -> "ScreenContext":
        """Context manager to enable and disable 'alternative screen' mode.

        Args:
            hide_cursor (bool, optional): Also hide the cursor. Defaults to False.
            style (Style, optional): Optional style for screen. Defaults to None.

        Returns:
            ~ScreenContext: Context which enables alternate screen on enter, and disables it on exit.
        """
        return ScreenContext(self, hide_cursor=hide_cursor, style=style or "")

    def measure(
        self, renderable: RenderableType, *, options: Optional[ConsoleOptions] = None
    ) -> Measurement:
        """Measure a renderable. Returns a :class:`~rich.measure.Measurement` object which contains
        information regarding the number of characters required to print the renderable.

        Args:
            renderable (RenderableType): Any renderable or string.
            options (Optional[ConsoleOptions], optional): Options to use when measuring, or None
                to use default options. Defaults to None.

        Returns:
            Measurement: A measurement of the renderable.
        """
        measurement = Measurement.get(self, options or self.options, renderable)
        return measurement

    def render(
        self, renderable: RenderableType, options: Optional[ConsoleOptions] = None
    ) -> Iterable[Segment]:
        """Render an object in to an iterable of `Segment` instances.

        This method contains the logic for rendering objects with the console protocol.
        You are unlikely to need to use it directly, unless you are extending the library.

        Args:
            renderable (RenderableType): An object supporting the console protocol, or
                an object that may be converted to a string.
            options (ConsoleOptions, optional): An options object, or None to use self.options. Defaults to None.

        Returns:
            Iterable[Segment]: An iterable of segments that may be rendered.
        """

        _options = options or self.options
        if _options.max_width < 1:
            # No space to render anything. This prevents potential recursion errors.
            return
        render_iterable: RenderResult

        renderable = rich_cast(renderable)
        if hasattr(renderable, "__rich_console__") and not isclass(renderable):
            render_iterable = renderable.__rich_console__(self, _options)
        elif isinstance(renderable, str):
            text_renderable = self.render_str(
                renderable, highlight=_options.highlight, markup=_options.markup
            )
            render_iterable = text_renderable.__rich_console__(self, _options)
        else:
            raise errors.NotRenderableError(
                f"Unable to render {renderable!r}; "
                "A str, Segment or object with __rich_console__ method is required"
            )

        try:
            iter_render = iter(render_iterable)
        except TypeError:
            raise errors.NotRenderableError(
                f"object {render_iterable!r} is not renderable"
            )
        _Segment = Segment
        _options = _options.reset_height()
        for render_output in iter_render:
            if isinstance(render_output, _Segment):
                yield render_output
            else:
                yield from self.render(render_output, _options)

    def render_lines(
        self,
        renderable: RenderableType,
        options: Optional[ConsoleOptions] = None,
        *,
        style: Optional[Style] = None,
        pad: bool = True,
        new_lines: bool = False,
    ) -> List[List[Segment]]:
        """Render objects in to a list of lines.

        The output of render_lines is useful when further formatting of rendered console text
        is required, such as the Panel class which draws a border around any renderable object.

        Args:
            renderable (RenderableType): Any object renderable in the console.
            options (Optional[ConsoleOptions], optional): Console options, or None to use self.options. Default to ``None``.
            style (Style, optional): Optional style to apply to renderables. Defaults to ``None``.
            pad (bool, optional): Pad lines shorter than render width. Defaults to ``True``.
            new_lines (bool, optional): Include "\n" characters at end of lines.

        Returns:
            List[List[Segment]]: A list of lines, where a line is a list of Segment objects.
        """
        with self._lock:
            render_options = options or self.options
            _rendered = self.render(renderable, render_options)
            if style:
                _rendered = Segment.apply_style(_rendered, style)

            render_height = render_options.height
            if render_height is not None:
                render_height = max(0, render_height)

            lines = list(
                islice(
                    Segment.split_and_crop_lines(
                        _rendered,
                        render_options.max_width,
                        include_new_lines=new_lines,
                        pad=pad,
                        style=style,
                    ),
                    None,
                    render_height,
                )
            )
            if render_options.height is not None:
                extra_lines = render_options.height - len(lines)
                if extra_lines > 0:
                    pad_line = [
                        (
                            [
                                Segment(" " * render_options.max_width, style),
                                Segment("\n"),
                            ]
                            if new_lines
                            else [Segment(" " * render_options.max_width, style)]
                        )
                    ]
                    lines.extend(pad_line * extra_lines)

            return lines

    def render_str(
        self,
        text: str,
        *,
        style: Union[str, Style] = "",
        justify: Optional[JustifyMethod] = None,
        overflow: Optional[OverflowMethod] = None,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
        highlighter: Optional[HighlighterType] = None,
    ) -> "Text":
        """Convert a string to a Text instance. This is called automatically if
        you print or log a string.

        Args:
            text (str): Text to render.
            style (Union[str, Style], optional): Style to apply to rendered text.
            justify (str, optional): Justify method: "default", "left", "center", "full", or "right". Defaults to ``None``.
            overflow (str, optional): Overflow method: "crop", "fold", or "ellipsis". Defaults to ``None``.
            emoji (Optional[bool], optional): Enable emoji, or ``None`` to use Console default.
            markup (Optional[bool], optional): Enable markup, or ``None`` to use Console default.
            highlight (Optional[bool], optional): Enable highlighting, or ``None`` to use Console default.
            highlighter (HighlighterType, optional): Optional highlighter to apply.
        Returns:
            ConsoleRenderable: Renderable object.

        """
        emoji_enabled = emoji or (emoji is None and self._emoji)
        markup_enabled = markup or (markup is None and self._markup)
        highlight_enabled = highlight or (highlight is None and self._highlight)

        if markup_enabled:
            rich_text = render_markup(
                text,
                style=style,
                emoji=emoji_enabled,
                emoji_variant=self._emoji_variant,
            )
            rich_text.justify = justify
            rich_text.overflow = overflow
        else:
            rich_text = Text(
                (
                    _emoji_replace(text, default_variant=self._emoji_variant)
                    if emoji_enabled
                    else text
                ),
                justify=justify,
                overflow=overflow,
                style=style,
            )

        _highlighter = (highlighter or self.highlighter) if highlight_enabled else None
        if _highlighter is not None:
            highlight_text = _highlighter(str(rich_text))
            highlight_text.copy_styles(rich_text)
            return highlight_text

        return rich_text

    def get_style(
        self, name: Union[str, Style], *, default: Optional[Union[Style, str]] = None
    ) -> Style:
        """Get a Style instance by its theme name or parse a definition.

        Args:
            name (str): The name of a style or a style definition.

        Returns:
            Style: A Style object.

        Raises:
            MissingStyle: If no style could be parsed from name.

        """
        if isinstance(name, Style):
            return name

        try:
            style = self._theme_stack.get(name)
            if style is None:
                style = Style.parse(name)
            return style.copy() if style.link else style
        except errors.StyleSyntaxError as error:
            if default is not None:
                return self.get_style(default)
            raise errors.MissingStyle(
                f"Failed to get style {name!r}; {error}"
            ) from None

    def _collect_renderables(
        self,
        objects: Iterable[Any],
        sep: str,
        end: str,
        *,
        justify: Optional[JustifyMethod] = None,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
    ) -> List[ConsoleRenderable]:
        """Combine a number of renderables and text into one renderable.

        Args:
            objects (Iterable[Any]): Anything that Rich can render.
            sep (str): String to write between print data.
            end (str): String to write at end of print data.
            justify (str, optional): One of "left", "right", "center", or "full". Defaults to ``None``.
            emoji (Optional[bool], optional): Enable emoji code, or ``None`` to use console default.
            markup (Optional[bool], optional): Enable markup, or ``None`` to use console default.
            highlight (Optional[bool], optional): Enable automatic highlighting, or ``None`` to use console default.

        Returns:
            List[ConsoleRenderable]: A list of things to render.
        """
        renderables: List[ConsoleRenderable] = []
        _append = renderables.append
        text: List[Text] = []
        append_text = text.append

        append = _append
        if justify in ("left", "center", "right"):

            def align_append(renderable: RenderableType) -> None:
                _append(Align(renderable, cast(AlignMethod, justify)))

            append = align_append

        _highlighter: HighlighterType = _null_highlighter
        if highlight or (highlight is None and self._highlight):
            _highlighter = self.highlighter

        def check_text() -> None:
            if text:
                sep_text = Text(sep, justify=justify, end=end)
                append(sep_text.join(text))
                text.clear()

        for renderable in objects:
            renderable = rich_cast(renderable)
            if isinstance(renderable, str):
                append_text(
                    self.render_str(
                        renderable,
                        emoji=emoji,
                        markup=markup,
                        highlight=highlight,
                        highlighter=_highlighter,
                    )
                )
            elif isinstance(renderable, Text):
                append_text(renderable)
            elif isinstance(renderable, ConsoleRenderable):
                check_text()
                append(renderable)
            elif is_expandable(renderable):
                check_text()
                append(Pretty(renderable, highlighter=_highlighter))
            else:
                append_text(_highlighter(str(renderable)))

        check_text()

        if self.style is not None:
            style = self.get_style(self.style)
            renderables = [Styled(renderable, style) for renderable in renderables]

        return renderables

    def rule(
        self,
        title: TextType = "",
        *,
        characters: str = "─",
        style: Union[str, Style] = "rule.line",
        align: AlignMethod = "center",
    ) -> None:
        """Draw a line with optional centered title.

        Args:
            title (str, optional): Text to render over the rule. Defaults to "".
            characters (str, optional): Character(s) to form the line. Defaults to "─".
            style (str, optional): Style of line. Defaults to "rule.line".
            align (str, optional): How to align the title, one of "left", "center", or "right". Defaults to "center".
        """
        from .rule import Rule

        rule = Rule(title=title, characters=characters, style=style, align=align)
        self.print(rule)

    def control(self, *control: Control) -> None:
        """Insert non-printing control codes.

        Args:
            control_codes (str): Control codes, such as those that may move the cursor.
        """
        if not self.is_dumb_terminal:
            with self:
                self._buffer.extend(_control.segment for _control in control)

    def out(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[Union[str, Style]] = None,
        highlight: Optional[bool] = None,
    ) -> None:
        """Output to the terminal. This is a low-level way of writing to the terminal which unlike
        :meth:`~rich.console.Console.print` won't pretty print, wrap text, or apply markup, but will
        optionally apply highlighting and a basic style.

        Args:
            sep (str, optional): String to write between print data. Defaults to " ".
            end (str, optional): String to write at end of print data. Defaults to "\\\\n".
            style (Union[str, Style], optional): A style to apply to output. Defaults to None.
            highlight (Optional[bool], optional): Enable automatic highlighting, or ``None`` to use
                console default. Defaults to ``None``.
        """
        raw_output: str = sep.join(str(_object) for _object in objects)
        self.print(
            raw_output,
            style=style,
            highlight=highlight,
            emoji=False,
            markup=False,
            no_wrap=True,
            overflow="ignore",
            crop=False,
            end=end,
        )

    def print(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[Union[str, Style]] = None,
        justify: Optional[JustifyMethod] = None,
        overflow: Optional[OverflowMethod] = None,
        no_wrap: Optional[bool] = None,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop: bool = True,
        soft_wrap: Optional[bool] = None,
        new_line_start: bool = False,
    ) -> None:
        """Print to the console.

        Args:
            objects (positional args): Objects to log to the terminal.
            sep (str, optional): String to write between print data. Defaults to " ".
            end (str, optional): String to write at end of print data. Defaults to "\\\\n".
            style (Union[str, Style], optional): A style to apply to output. Defaults to None.
            justify (str, optional): Justify method: "default", "left", "right", "center", or "full". Defaults to ``None``.
            overflow (str, optional): Overflow method: "ignore", "crop", "fold", or "ellipsis". Defaults to None.
            no_wrap (Optional[bool], optional): Disable word wrapping. Defaults to None.
            emoji (Optional[bool], optional): Enable emoji code, or ``None`` to use console default. Defaults to ``None``.
            markup (Optional[bool], optional): Enable markup, or ``None`` to use console default. Defaults to ``None``.
            highlight (Optional[bool], optional): Enable automatic highlighting, or ``None`` to use console default. Defaults to ``None``.
            width (Optional[int], optional): Width of output, or ``None`` to auto-detect. Defaults to ``None``.
            crop (Optional[bool], optional): Crop output to width of terminal. Defaults to True.
            soft_wrap (bool, optional): Enable soft wrap mode which disables word wrapping and cropping of text or ``None`` for
                Console default. Defaults to ``None``.
            new_line_start (bool, False): Insert a new line at the start if the output contains more than one line. Defaults to ``False``.
        """
        if not objects:
            objects = (NewLine(),)

        if soft_wrap is None:
            soft_wrap = self.soft_wrap
        if soft_wrap:
            if no_wrap is None:
                no_wrap = True
            if overflow is None:
                overflow = "ignore"
            crop = False
        render_hooks = self._render_hooks[:]
        with self:
            renderables = self._collect_renderables(
                objects,
                sep,
                end,
                justify=justify,
                emoji=emoji,
                markup=markup,
                highlight=highlight,
            )
            for hook in render_hooks:
                renderables = hook.process_renderables(renderables)
            render_options = self.options.update(
                justify=justify,
                overflow=overflow,
                width=min(width, self.width) if width is not None else NO_CHANGE,
                height=height,
                no_wrap=no_wrap,
                markup=markup,
                highlight=highlight,
            )

            new_segments: List[Segment] = []
            extend = new_segments.extend
            render = self.render
            if style is None:
                for renderable in renderables:
                    extend(render(renderable, render_options))
            else:
                for renderable in renderables:
                    extend(
                        Segment.apply_style(
                            render(renderable, render_options), self.get_style(style)
                        )
                    )
            if new_line_start:
                if (
                    len("".join(segment.text for segment in new_segments).splitlines())
                    > 1
                ):
                    new_segments.insert(0, Segment.line())
            if crop:
                buffer_extend = self._buffer.extend
                for line in Segment.split_and_crop_lines(
                    new_segments, self.width, pad=False
                ):
                    buffer_extend(line)
            else:
                self._buffer.extend(new_segments)

    def print_json(
        self,
        json: Optional[str] = None,
        *,
        data: Any = None,
        indent: Union[None, int, str] = 2,
        highlight: bool = True,
        skip_keys: bool = False,
        ensure_ascii: bool = False,
        check_circular: bool = True,
        allow_nan: bool = True,
        default: Optional[Callable[[Any], Any]] = None,
        sort_keys: bool = False,
    ) -> None:
        """Pretty prints JSON. Output will be valid JSON.

        Args:
            json (Optional[str]): A string containing JSON.
            data (Any): If json is not supplied, then encode this data.
            indent (Union[None, int, str], optional): Number of spaces to indent. Defaults to 2.
            highlight (bool, optional): Enable highlighting of output: Defaults to True.
            skip_keys (bool, optional): Skip keys not of a basic type. Defaults to False.
            ensure_ascii (bool, optional): Escape all non-ascii characters. Defaults to False.
            check_circular (bool, optional): Check for circular references. Defaults to True.
            allow_nan (bool, optional): Allow NaN and Infinity values. Defaults to True.
            default (Callable, optional): A callable that converts values that can not be encoded
                in to something that can be JSON encoded. Defaults to None.
            sort_keys (bool, optional): Sort dictionary keys. Defaults to False.
        """
        from pip._vendor.rich.json import JSON

        if json is None:
            json_renderable = JSON.from_data(
                data,
                indent=indent,
                highlight=highlight,
                skip_keys=skip_keys,
                ensure_ascii=ensure_ascii,
                check_circular=check_circular,
                allow_nan=allow_nan,
                default=default,
                sort_keys=sort_keys,
            )
        else:
            if not isinstance(json, str):
                raise TypeError(
                    f"json must be str. Did you mean print_json(data={json!r}) ?"
                )
            json_renderable = JSON(
                json,
                indent=indent,
                highlight=highlight,
                skip_keys=skip_keys,
                ensure_ascii=ensure_ascii,
                check_circular=check_circular,
                allow_nan=allow_nan,
                default=default,
                sort_keys=sort_keys,
            )
        self.print(json_renderable, soft_wrap=True)

    def update_screen(
        self,
        renderable: RenderableType,
        *,
        region: Optional[Region] = None,
        options: Optional[ConsoleOptions] = None,
    ) -> None:
        """Update the screen at a given offset.

        Args:
            renderable (RenderableType): A Rich renderable.
            region (Region, optional): Region of screen to update, or None for entire screen. Defaults to None.
            x (int, optional): x offset. Defaults to 0.
            y (int, optional): y offset. Defaults to 0.

        Raises:
            errors.NoAltScreen: If the Console isn't in alt screen mode.

        """
        if not self.is_alt_screen:
            raise errors.NoAltScreen("Alt screen must be enabled to call update_screen")
        render_options = options or self.options
        if region is None:
            x = y = 0
            render_options = render_options.update_dimensions(
                render_options.max_width, render_options.height or self.height
            )
        else:
            x, y, width, height = region
            render_options = render_options.update_dimensions(width, height)

        lines = self.render_lines(renderable, options=render_options)
        self.update_screen_lines(lines, x, y)

    def update_screen_lines(
        self, lines: List[List[Segment]], x: int = 0, y: int = 0
    ) -> None:
        """Update lines of the screen at a given offset.

        Args:
            lines (List[List[Segment]]): Rendered lines (as produced by :meth:`~rich.Console.render_lines`).
            x (int, optional): x offset (column no). Defaults to 0.
            y (int, optional): y offset (column no). Defaults to 0.

        Raises:
            errors.NoAltScreen: If the Console isn't in alt screen mode.
        """
        if not self.is_alt_screen:
            raise errors.NoAltScreen("Alt screen must be enabled to call update_screen")
        screen_update = ScreenUpdate(lines, x, y)
        segments = self.render(screen_update)
        self._buffer.extend(segments)
        self._check_buffer()

    def print_exception(
        self,
        *,
        width: Optional[int] = 100,
        extra_lines: int = 3,
        theme: Optional[str] = None,
        word_wrap: bool = False,
        show_locals: bool = False,
        suppress: Iterable[Union[str, ModuleType]] = (),
        max_frames: int = 100,
    ) -> None:
        """Prints a rich render of the last exception and traceback.

        Args:
            width (Optional[int], optional): Number of characters used to render code. Defaults to 100.
            extra_lines (int, optional): Additional lines of code to render. Defaults to 3.
            theme (str, optional): Override pygments theme used in traceback
            word_wrap (bool, optional): Enable word wrapping of long lines. Defaults to False.
            show_locals (bool, optional): Enable display of local variables. Defaults to False.
            suppress (Iterable[Union[str, ModuleType]]): Optional sequence of modules or paths to exclude from traceback.
            max_frames (int): Maximum number of frames to show in a traceback, 0 for no maximum. Defaults to 100.
        """
        from .traceback import Traceback

        traceback = Traceback(
            width=width,
            extra_lines=extra_lines,
            theme=theme,
            word_wrap=word_wrap,
            show_locals=show_locals,
            suppress=suppress,
            max_frames=max_frames,
        )
        self.print(traceback)

    @staticmethod
    def _caller_frame_info(
        offset: int,
        currentframe: Callable[[], Optional[FrameType]] = inspect.currentframe,
    ) -> Tuple[str, int, Dict[str, Any]]:
        """Get caller frame information.

        Args:
            offset (int): the caller offset within the current frame stack.
            currentframe (Callable[[], Optional[FrameType]], optional): the callable to use to
                retrieve the current frame. Defaults to ``inspect.currentframe``.

        Returns:
            Tuple[str, int, Dict[str, Any]]: A tuple containing the filename, the line number and
                the dictionary of local variables associated with the caller frame.

        Raises:
            RuntimeError: If the stack offset is invalid.
        """
        # Ignore the frame of this local helper
        offset += 1

        frame = currentframe()
        if frame is not None:
            # Use the faster currentframe where implemented
            while offset and frame is not None:
                frame = frame.f_back
                offset -= 1
            assert frame is not None
            return frame.f_code.co_filename, frame.f_lineno, frame.f_locals
        else:
            # Fallback to the slower stack
            frame_info = inspect.stack()[offset]
            return frame_info.filename, frame_info.lineno, frame_info.frame.f_locals

    def log(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[Union[str, Style]] = None,
        justify: Optional[JustifyMethod] = None,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
        log_locals: bool = False,
        _stack_offset: int = 1,
    ) -> None:
        """Log rich content to the terminal.

        Args:
            objects (positional args): Objects to log to the terminal.
            sep (str, optional): String to write between print data. Defaults to " ".
            end (str, optional): String to write at end of print data. Defaults to "\\\\n".
            style (Union[str, Style], optional): A style to apply to output. Defaults to None.
            justify (str, optional): One of "left", "right", "center", or "full". Defaults to ``None``.
            emoji (Optional[bool], optional): Enable emoji code, or ``None`` to use console default. Defaults to None.
            markup (Optional[bool], optional): Enable markup, or ``None`` to use console default. Defaults to None.
            highlight (Optional[bool], optional): Enable automatic highlighting, or ``None`` to use console default. Defaults to None.
            log_locals (bool, optional): Boolean to enable logging of locals where ``log()``
                was called. Defaults to False.
            _stack_offset (int, optional): Offset of caller from end of call stack. Defaults to 1.
        """
        if not objects:
            objects = (NewLine(),)

        render_hooks = self._render_hooks[:]

        with self:
            renderables = self._collect_renderables(
                objects,
                sep,
                end,
                justify=justify,
                emoji=emoji,
                markup=markup,
                highlight=highlight,
            )
            if style is not None:
                renderables = [Styled(renderable, style) for renderable in renderables]

            filename, line_no, locals = self._caller_frame_info(_stack_offset)
            link_path = None if filename.startswith("<") else os.path.abspath(filename)
            path = filename.rpartition(os.sep)[-1]
            if log_locals:
                locals_map = {
                    key: value
                    for key, value in locals.items()
                    if not key.startswith("__")
                }
                renderables.append(render_scope(locals_map, title="[i]locals"))

            renderables = [
                self._log_render(
                    self,
                    renderables,
                    log_time=self.get_datetime(),
                    path=path,
                    line_no=line_no,
                    link_path=link_path,
                )
            ]
            for hook in render_hooks:
                renderables = hook.process_renderables(renderables)
            new_segments: List[Segment] = []
            extend = new_segments.extend
            render = self.render
            render_options = self.options
            for renderable in renderables:
                extend(render(renderable, render_options))
            buffer_extend = self._buffer.extend
            for line in Segment.split_and_crop_lines(
                new_segments, self.width, pad=False
            ):
                buffer_extend(line)

    def on_broken_pipe(self) -> None:
        """This function is called when a `BrokenPipeError` is raised.

        This can occur when piping Textual output in Linux and macOS.
        The default implementation is to exit the app, but you could implement
        this method in a subclass to change the behavior.

        See https://docs.python.org/3/library/signal.html#note-on-sigpipe for details.
        """
        self.quiet = True
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        raise SystemExit(1)

    def _check_buffer(self) -> None:
        """Check if the buffer may be rendered. Render it if it can (e.g. Console.quiet is False)
        Rendering is supported on Windows, Unix and Jupyter environments. For
        legacy Windows consoles, the win32 API is called directly.
        This method will also record what it renders if recording is enabled via Console.record.
        """
        if self.quiet:
            del self._buffer[:]
            return

        try:
            self._write_buffer()
        except BrokenPipeError:
            self.on_broken_pipe()

    def _write_buffer(self) -> None:
        """Write the buffer to the output file."""

        with self._lock:
            if self.record and not self._buffer_index:
                with self._record_buffer_lock:
                    self._record_buffer.extend(self._buffer[:])

            if self._buffer_index == 0:
                if self.is_jupyter:  # pragma: no cover
                    from .jupyter import display

                    display(self._buffer, self._render_buffer(self._buffer[:]))
                    del self._buffer[:]
                else:
                    if WINDOWS:
                        use_legacy_windows_render = False
                        if self.legacy_windows:
                            fileno = get_fileno(self.file)
                            if fileno is not None:
                                use_legacy_windows_render = (
                                    fileno in _STD_STREAMS_OUTPUT
                                )

                        if use_legacy_windows_render:
                            from pip._vendor.rich._win32_console import LegacyWindowsTerm
                            from pip._vendor.rich._windows_renderer import legacy_windows_render

                            buffer = self._buffer[:]
                            if self.no_color and self._color_system:
                                buffer = list(Segment.remove_color(buffer))

                            legacy_windows_render(buffer, LegacyWindowsTerm(self.file))
                        else:
                            # Either a non-std stream on legacy Windows, or modern Windows.
                            text = self._render_buffer(self._buffer[:])
                            # https://bugs.python.org/issue37871
                            # https://github.com/python/cpython/issues/82052
                            # We need to avoid writing more than 32Kb in a single write, due to the above bug
                            write = self.file.write
                            # Worse case scenario, every character is 4 bytes of utf-8
                            MAX_WRITE = 32 * 1024 // 4
                            try:
                                if len(text) <= MAX_WRITE:
                                    write(text)
                                else:
                                    batch: List[str] = []
                                    batch_append = batch.append
                                    size = 0
                                    for line in text.splitlines(True):
                                        if size + len(line) > MAX_WRITE and batch:
                                            write("".join(batch))
                                            batch.clear()
                                            size = 0
                                        batch_append(line)
                                        size += len(line)
                                    if batch:
                                        write("".join(batch))
                                        batch.clear()
                            except UnicodeEncodeError as error:
                                error.reason = f"{error.reason}\n*** You may need to add PYTHONIOENCODING=utf-8 to your environment ***"
                                raise
                    else:
                        text = self._render_buffer(self._buffer[:])
                        try:
                            self.file.write(text)
                        except UnicodeEncodeError as error:
                            error.reason = f"{error.reason}\n*** You may need to add PYTHONIOENCODING=utf-8 to your environment ***"
                            raise

                    self.file.flush()
                    del self._buffer[:]

    def _render_buffer(self, buffer: Iterable[Segment]) -> str:
        """Render buffered output, and clear buffer."""
        output: List[str] = []
        append = output.append
        color_system = self._color_system
        legacy_windows = self.legacy_windows
        not_terminal = not self.is_terminal
        if self.no_color and color_system:
            buffer = Segment.remove_color(buffer)
        for text, style, control in buffer:
            if style:
                append(
                    style.render(
                        text,
                        color_system=color_system,
                        legacy_windows=legacy_windows,
                    )
                )
            elif not (not_terminal and control):
                append(text)

        rendered = "".join(output)
        return rendered

    def input(
        self,
        prompt: TextType = "",
        *,
        markup: bool = True,
        emoji: bool = True,
        password: bool = False,
        stream: Optional[TextIO] = None,
    ) -> str:
        """Displays a prompt and waits for input from the user. The prompt may contain color / style.

        It works in the same way as Python's builtin :func:`input` function and provides elaborate line editing and history features if Python's builtin :mod:`readline` module is previously loaded.

        Args:
            prompt (Union[str, Text]): Text to render in the prompt.
            markup (bool, optional): Enable console markup (requires a str prompt). Defaults to True.
            emoji (bool, optional): Enable emoji (requires a str prompt). Defaults to True.
            password: (bool, optional): Hide typed text. Defaults to False.
            stream: (TextIO, optional): Optional file to read input from (rather than stdin). Defaults to None.

        Returns:
            str: Text read from stdin.
        """
        if prompt:
            self.print(prompt, markup=markup, emoji=emoji, end="")
        if password:
            result = getpass("", stream=stream)
        else:
            if stream:
                result = stream.readline()
            else:
                result = input()
        return result

    def export_text(self, *, clear: bool = True, styles: bool = False) -> str:
        """Generate text from console contents (requires record=True argument in constructor).

        Args:
            clear (bool, optional): Clear record buffer after exporting. Defaults to ``True``.
            styles (bool, optional): If ``True``, ansi escape codes will be included. ``False`` for plain text.
                Defaults to ``False``.

        Returns:
            str: String containing console contents.

        """
        assert (
            self.record
        ), "To export console contents set record=True in the constructor or instance"

        with self._record_buffer_lock:
            if styles:
                text = "".join(
                    (style.render(text) if style else text)
                    for text, style, _ in self._record_buffer
                )
            else:
                text = "".join(
                    segment.text
                    for segment in self._record_buffer
                    if not segment.control
                )
            if clear:
                del self._record_buffer[:]
        return text

    def save_text(self, path: str, *, clear: bool = True, styles: bool = False) -> None:
        """Generate text from console and save to a given location (requires record=True argument in constructor).

        Args:
            path (str): Path to write text files.
            clear (bool, optional): Clear record buffer after exporting. Defaults to ``True``.
            styles (bool, optional): If ``True``, ansi style codes will be included. ``False`` for plain text.
                Defaults to ``False``.

        """
        text = self.export_text(clear=clear, styles=styles)
        with open(path, "w", encoding="utf-8") as write_file:
            write_file.write(text)

    def export_html(
        self,
        *,
        theme: Optional[TerminalTheme] = None,
        clear: bool = True,
        code_format: Optional[str] = None,
        inline_styles: bool = False,
    ) -> str:
        """Generate HTML from console contents (requires record=True argument in constructor).

        Args:
            theme (TerminalTheme, optional): TerminalTheme object containing console colors.
            clear (bool, optional): Clear record buffer after exporting. Defaults to ``True``.
            code_format (str, optional): Format string to render HTML. In addition to '{foreground}',
                '{background}', and '{code}', should contain '{stylesheet}' if inline_styles is ``False``.
            inline_styles (bool, optional): If ``True`` styles will be inlined in to spans, which makes files
                larger but easier to cut and paste markup. If ``False``, styles will be embedded in a style tag.
                Defaults to False.

        Returns:
            str: String containing console contents as HTML.
        """
        assert (
            self.record
        ), "To export console contents set record=True in the constructor or instance"
        fragments: List[str] = []
        append = fragments.append
        _theme = theme or DEFAULT_TERMINAL_THEME
        stylesheet = ""

        render_code_format = CONSOLE_HTML_FORMAT if code_format is None else code_format

        with self._record_buffer_lock:
            if inline_styles:
                for text, style, _ in Segment.filter_control(
                    Segment.simplify(self._record_buffer)
                ):
                    text = escape(text)
                    if style:
                        rule = style.get_html_style(_theme)
                        if style.link:
                            text = f'<a href="{style.link}">{text}</a>'
                        text = f'<span style="{rule}">{text}</span>' if rule else text
                    append(text)
            else:
                styles: Dict[str, int] = {}
                for text, style, _ in Segment.filter_control(
                    Segment.simplify(self._record_buffer)
                ):
                    text = escape(text)
                    if style:
                        rule = style.get_html_style(_theme)
                        style_number = styles.setdefault(rule, len(styles) + 1)
                        if style.link:
                            text = f'<a class="r{style_number}" href="{style.link}">{text}</a>'
                        else:
                            text = f'<span class="r{style_number}">{text}</span>'
                    append(text)
                stylesheet_rules: List[str] = []
                stylesheet_append = stylesheet_rules.append
                for style_rule, style_number in styles.items():
                    if style_rule:
                        stylesheet_append(f".r{style_number} {{{style_rule}}}")
                stylesheet = "\n".join(stylesheet_rules)

            rendered_code = render_code_format.format(
                code="".join(fragments),
                stylesheet=stylesheet,
                foreground=_theme.foreground_color.hex,
                background=_theme.background_color.hex,
            )
            if clear:
                del self._record_buffer[:]
        return rendered_code

    def save_html(
        self,
        path: str,
        *,
        theme: Optional[TerminalTheme] = None,
        clear: bool = True,
        code_format: str = CONSOLE_HTML_FORMAT,
        inline_styles: bool = False,
    ) -> None:
        """Generate HTML from console contents and write to a file (requires record=True argument in constructor).

        Args:
            path (str): Path to write html file.
            theme (TerminalTheme, optional): TerminalTheme object containing console colors.
            clear (bool, optional): Clear record buffer after exporting. Defaults to ``True``.
            code_format (str, optional): Format string to render HTML. In addition to '{foreground}',
                '{background}', and '{code}', should contain '{stylesheet}' if inline_styles is ``False``.
            inline_styles (bool, optional): If ``True`` styles will be inlined in to spans, which makes files
                larger but easier to cut and paste markup. If ``False``, styles will be embedded in a style tag.
                Defaults to False.

        """
        html = self.export_html(
            theme=theme,
            clear=clear,
            code_format=code_format,
            inline_styles=inline_styles,
        )
        with open(path, "w", encoding="utf-8") as write_file:
            write_file.write(html)

    def export_svg(
        self,
        *,
        title: str = "Rich",
        theme: Optional[TerminalTheme] = None,
        clear: bool = True,
        code_format: str = CONSOLE_SVG_FORMAT,
        font_aspect_ratio: float = 0.61,
        unique_id: Optional[str] = None,
    ) -> str:
        """
        Generate an SVG from the console contents (requires record=True in Console constructor).

        Args:
            title (str, optional): The title of the tab in the output image
            theme (TerminalTheme, optional): The ``TerminalTheme`` object to use to style the terminal
            clear (bool, optional): Clear record buffer after exporting. Defaults to ``True``
            code_format (str, optional): Format string used to generate the SVG. Rich will inject a number of variables
                into the string in order to form the final SVG output. The default template used and the variables
                injected by Rich can be found by inspecting the ``console.CONSOLE_SVG_FORMAT`` variable.
            font_aspect_ratio (float, optional): The width to height ratio of the font used in the ``code_format``
                string. Defaults to 0.61, which is the width to height ratio of Fira Code (the default font).
                If you aren't specifying a different font inside ``code_format``, you probably don't need this.
            unique_id (str, optional): unique id that is used as the prefix for various elements (CSS styles, node
                ids). If not set, this defaults to a computed value based on the recorded content.
        """

        from pip._vendor.rich.cells import cell_len

        style_cache: Dict[Style, str] = {}

        def get_svg_style(style: Style) -> str:
            """Convert a Style to CSS rules for SVG."""
            if style in style_cache:
                return style_cache[style]
            css_rules = []
            color = (
                _theme.foreground_color
                if (style.color is None or style.color.is_default)
                else style.color.get_truecolor(_theme)
            )
            bgcolor = (
                _theme.background_color
                if (style.bgcolor is None or style.bgcolor.is_default)
                else style.bgcolor.get_truecolor(_theme)
            )
            if style.reverse:
                color, bgcolor = bgcolor, color
            if style.dim:
                color = blend_rgb(color, bgcolor, 0.4)
            css_rules.append(f"fill: {color.hex}")
            if style.bold:
                css_rules.append("font-weight: bold")
            if style.italic:
                css_rules.append("font-style: italic;")
            if style.underline:
                css_rules.append("text-decoration: underline;")
            if style.strike:
                css_rules.append("text-decoration: line-through;")

            css = ";".join(css_rules)
            style_cache[style] = css
            return css

        _theme = theme or SVG_EXPORT_THEME

        width = self.width
        char_height = 20
        char_width = char_height * font_aspect_ratio
        line_height = char_height * 1.22

        margin_top = 1
        margin_right = 1
        margin_bottom = 1
        margin_left = 1

        padding_top = 40
        padding_right = 8
        padding_bottom = 8
        padding_left = 8

        padding_width = padding_left + padding_right
        padding_height = padding_top + padding_bottom
        margin_width = margin_left + margin_right
        margin_height = margin_top + margin_bottom

        text_backgrounds: List[str] = []
        text_group: List[str] = []
        classes: Dict[str, int] = {}
        style_no = 1

        def escape_text(text: str) -> str:
            """HTML escape text and replace spaces with nbsp."""
            return escape(text).replace(" ", "&#160;")

        def make_tag(
            name: str, content: Optional[str] = None, **attribs: object
        ) -> str:
            """Make a tag from name, content, and attributes."""

            def stringify(value: object) -> str:
                if isinstance(value, (float)):
                    return format(value, "g")
                return str(value)

            tag_attribs = " ".join(
                f'{k.lstrip("_").replace("_", "-")}="{stringify(v)}"'
                for k, v in attribs.items()
            )
            return (
                f"<{name} {tag_attribs}>{content}</{name}>"
                if content
                else f"<{name} {tag_attribs}/>"
            )

        with self._record_buffer_lock:
            segments = list(Segment.filter_control(self._record_buffer))
            if clear:
                self._record_buffer.clear()

        if unique_id is None:
            unique_id = "terminal-" + str(
                zlib.adler32(
                    ("".join(repr(segment) for segment in segments)).encode(
                        "utf-8",
                        "ignore",
                    )
                    + title.encode("utf-8", "ignore")
                )
            )
        y = 0
        for y, line in enumerate(Segment.split_and_crop_lines(segments, length=width)):
            x = 0
            for text, style, _control in line:
                style = style or Style()
                rules = get_svg_style(style)
                if rules not in classes:
                    classes[rules] = style_no
                    style_no += 1
                class_name = f"r{classes[rules]}"

                if style.reverse:
                    has_background = True
                    background = (
                        _theme.foreground_color.hex
                        if style.color is None
                        else style.color.get_truecolor(_theme).hex
                    )
                else:
                    bgcolor = style.bgcolor
                    has_background = bgcolor is not None and not bgcolor.is_default
                    background = (
                        _theme.background_color.hex
                        if style.bgcolor is None
                        else style.bgcolor.get_truecolor(_theme).hex
                    )

                text_length = cell_len(text)
                if has_background:
                    text_backgrounds.append(
                        make_tag(
                            "rect",
                            fill=background,
                            x=x * char_width,
                            y=y * line_height + 1.5,
                            width=char_width * text_length,
                            height=line_height + 0.25,
                            shape_rendering="crispEdges",
                        )
                    )

                if text != " " * len(text):
                    text_group.append(
                        make_tag(
                            "text",
                            escape_text(text),
                            _class=f"{unique_id}-{class_name}",
                            x=x * char_width,
                            y=y * line_height + char_height,
                            textLength=char_width * len(text),
                            clip_path=f"url(#{unique_id}-line-{y})",
                        )
                    )
                x += cell_len(text)

        line_offsets = [line_no * line_height + 1.5 for line_no in range(y)]
        lines = "\n".join(
            f"""<clipPath id="{unique_id}-line-{line_no}">
    {make_tag("rect", x=0, y=offset, width=char_width * width, height=line_height + 0.25)}
            </clipPath>"""
            for line_no, offset in enumerate(line_offsets)
        )

        styles = "\n".join(
            f".{unique_id}-r{rule_no} {{ {css} }}" for css, rule_no in classes.items()
        )
        backgrounds = "".join(text_backgrounds)
        matrix = "".join(text_group)

        terminal_width = ceil(width * char_width + padding_width)
        terminal_height = (y + 1) * line_height + padding_height
        chrome = make_tag(
            "rect",
            fill=_theme.background_color.hex,
            stroke="rgba(255,255,255,0.35)",
            stroke_width="1",
            x=margin_left,
            y=margin_top,
            width=terminal_width,
            height=terminal_height,
            rx=8,
        )

        title_color = _theme.foreground_color.hex
        if title:
            chrome += make_tag(
                "text",
                escape_text(title),
                _class=f"{unique_id}-title",
                fill=title_color,
                text_anchor="middle",
                x=terminal_width // 2,
                y=margin_top + char_height + 6,
            )
        chrome += f"""
            <g transform="translate(26,22)">
            <circle cx="0" cy="0" r="7" fill="#ff5f57"/>
            <circle cx="22" cy="0" r="7" fill="#febc2e"/>
            <circle cx="44" cy="0" r="7" fill="#28c840"/>
            </g>
        """

        svg = code_format.format(
            unique_id=unique_id,
            char_width=char_width,
            char_height=char_height,
            line_height=line_height,
            terminal_width=char_width * width - 1,
            terminal_height=(y + 1) * line_height - 1,
            width=terminal_width + margin_width,
            height=terminal_height + margin_height,
            terminal_x=margin_left + padding_left,
            terminal_y=margin_top + padding_top,
            styles=styles,
            chrome=chrome,
            backgrounds=backgrounds,
            matrix=matrix,
            lines=lines,
        )
        return svg

    def save_svg(
        self,
        path: str,
        *,
        title: str = "Rich",
        theme: Optional[TerminalTheme] = None,
        clear: bool = True,
        code_format: str = CONSOLE_SVG_FORMAT,
        font_aspect_ratio: float = 0.61,
        unique_id: Optional[str] = None,
    ) -> None:
        """Generate an SVG file from the console contents (requires record=True in Console constructor).

        Args:
            path (str): The path to write the SVG to.
            title (str, optional): The title of the tab in the output image
            theme (TerminalTheme, optional): The ``TerminalTheme`` object to use to style the terminal
            clear (bool, optional): Clear record buffer after exporting. Defaults to ``True``
            code_format (str, optional): Format string used to generate the SVG. Rich will inject a number of variables
                into the string in order to form the final SVG output. The default template used and the variables
                injected by Rich can be found by inspecting the ``console.CONSOLE_SVG_FORMAT`` variable.
            font_aspect_ratio (float, optional): The width to height ratio of the font used in the ``code_format``
                string. Defaults to 0.61, which is the width to height ratio of Fira Code (the default font).
                If you aren't specifying a different font inside ``code_format``, you probably don't need this.
            unique_id (str, optional): unique id that is used as the prefix for various elements (CSS styles, node
                ids). If not set, this defaults to a computed value based on the recorded content.
        """
        svg = self.export_svg(
            title=title,
            theme=theme,
            clear=clear,
            code_format=code_format,
            font_aspect_ratio=font_aspect_ratio,
            unique_id=unique_id,
        )
        with open(path, "w", encoding="utf-8") as write_file:
            write_file.write(svg)


def _svg_hash(svg_main_code: str) -> str:
    """Returns a unique hash for the given SVG main code.

    Args:
        svg_main_code (str): The content we're going to inject in the SVG envelope.

    Returns:
        str: a hash of the given content
    """
    return str(zlib.adler32(svg_main_code.encode()))


if __name__ == "__main__":  # pragma: no cover
    console = Console(record=True)

    console.log(
        "JSONRPC [i]request[/i]",
        5,
        1.3,
        True,
        False,
        None,
        {
            "jsonrpc": "2.0",
            "method": "subtract",
            "params": {"minuend": 42, "subtrahend": 23},
            "id": 3,
        },
    )

    console.log("Hello, World!", "{'a': 1}", repr(console))

    console.print(
        {
            "name": None,
            "empty": [],
            "quiz": {
                "sport": {
                    "answered": True,
                    "q1": {
                        "question": "Which one is correct team name in NBA?",
                        "options": [
                            "New York Bulls",
                            "Los Angeles Kings",
                            "Golden State Warriors",
                            "Huston Rocket",
                        ],
                        "answer": "Huston Rocket",
                    },
                },
                "maths": {
                    "answered": False,
                    "q1": {
                        "question": "5 + 7 = ?",
                        "options": [10, 11, 12, 13],
                        "answer": 12,
                    },
                    "q2": {
                        "question": "12 - 8 = ?",
                        "options": [1, 2, 3, 4],
                        "answer": 4,
                    },
                },
            },
        }
    )

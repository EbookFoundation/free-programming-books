import time
from typing import TYPE_CHECKING, Callable, Dict, Iterable, List, Union, Final

from .segment import ControlCode, ControlType, Segment

if TYPE_CHECKING:
    from .console import Console, ConsoleOptions, RenderResult

STRIP_CONTROL_CODES: Final = [
    7,  # Bell
    8,  # Backspace
    11,  # Vertical tab
    12,  # Form feed
    13,  # Carriage return
]
_CONTROL_STRIP_TRANSLATE: Final = {
    _codepoint: None for _codepoint in STRIP_CONTROL_CODES
}

CONTROL_ESCAPE: Final = {
    7: "\\a",
    8: "\\b",
    11: "\\v",
    12: "\\f",
    13: "\\r",
}

CONTROL_CODES_FORMAT: Dict[int, Callable[..., str]] = {
    ControlType.BELL: lambda: "\x07",
    ControlType.CARRIAGE_RETURN: lambda: "\r",
    ControlType.HOME: lambda: "\x1b[H",
    ControlType.CLEAR: lambda: "\x1b[2J",
    ControlType.ENABLE_ALT_SCREEN: lambda: "\x1b[?1049h",
    ControlType.DISABLE_ALT_SCREEN: lambda: "\x1b[?1049l",
    ControlType.SHOW_CURSOR: lambda: "\x1b[?25h",
    ControlType.HIDE_CURSOR: lambda: "\x1b[?25l",
    ControlType.CURSOR_UP: lambda param: f"\x1b[{param}A",
    ControlType.CURSOR_DOWN: lambda param: f"\x1b[{param}B",
    ControlType.CURSOR_FORWARD: lambda param: f"\x1b[{param}C",
    ControlType.CURSOR_BACKWARD: lambda param: f"\x1b[{param}D",
    ControlType.CURSOR_MOVE_TO_COLUMN: lambda param: f"\x1b[{param+1}G",
    ControlType.ERASE_IN_LINE: lambda param: f"\x1b[{param}K",
    ControlType.CURSOR_MOVE_TO: lambda x, y: f"\x1b[{y+1};{x+1}H",
    ControlType.SET_WINDOW_TITLE: lambda title: f"\x1b]0;{title}\x07",
}


class Control:
    """A renderable that inserts a control code (non printable but may move cursor).

    Args:
        *codes (str): Positional arguments are either a :class:`~rich.segment.ControlType` enum or a
            tuple of ControlType and an integer parameter
    """

    __slots__ = ["segment"]

    def __init__(self, *codes: Union[ControlType, ControlCode]) -> None:
        control_codes: List[ControlCode] = [
            (code,) if isinstance(code, ControlType) else code for code in codes
        ]
        _format_map = CONTROL_CODES_FORMAT
        rendered_codes = "".join(
            _format_map[code](*parameters) for code, *parameters in control_codes
        )
        self.segment = Segment(rendered_codes, None, control_codes)

    @classmethod
    def bell(cls) -> "Control":
        """Ring the 'bell'."""
        return cls(ControlType.BELL)

    @classmethod
    def home(cls) -> "Control":
        """Move cursor to 'home' position."""
        return cls(ControlType.HOME)

    @classmethod
    def move(cls, x: int = 0, y: int = 0) -> "Control":
        """Move cursor relative to current position.

        Args:
            x (int): X offset.
            y (int): Y offset.

        Returns:
            ~Control: Control object.

        """

        def get_codes() -> Iterable[ControlCode]:
            control = ControlType
            if x:
                yield (
                    control.CURSOR_FORWARD if x > 0 else control.CURSOR_BACKWARD,
                    abs(x),
                )
            if y:
                yield (
                    control.CURSOR_DOWN if y > 0 else control.CURSOR_UP,
                    abs(y),
                )

        control = cls(*get_codes())
        return control

    @classmethod
    def move_to_column(cls, x: int, y: int = 0) -> "Control":
        """Move to the given column, optionally add offset to row.

        Returns:
            x (int): absolute x (column)
            y (int): optional y offset (row)

        Returns:
            ~Control: Control object.
        """

        return (
            cls(
                (ControlType.CURSOR_MOVE_TO_COLUMN, x),
                (
                    ControlType.CURSOR_DOWN if y > 0 else ControlType.CURSOR_UP,
                    abs(y),
                ),
            )
            if y
            else cls((ControlType.CURSOR_MOVE_TO_COLUMN, x))
        )

    @classmethod
    def move_to(cls, x: int, y: int) -> "Control":
        """Move cursor to absolute position.

        Args:
            x (int): x offset (column)
            y (int): y offset (row)

        Returns:
            ~Control: Control object.
        """
        return cls((ControlType.CURSOR_MOVE_TO, x, y))

    @classmethod
    def clear(cls) -> "Control":
        """Clear the screen."""
        return cls(ControlType.CLEAR)

    @classmethod
    def show_cursor(cls, show: bool) -> "Control":
        """Show or hide the cursor."""
        return cls(ControlType.SHOW_CURSOR if show else ControlType.HIDE_CURSOR)

    @classmethod
    def alt_screen(cls, enable: bool) -> "Control":
        """Enable or disable alt screen."""
        if enable:
            return cls(ControlType.ENABLE_ALT_SCREEN, ControlType.HOME)
        else:
            return cls(ControlType.DISABLE_ALT_SCREEN)

    @classmethod
    def title(cls, title: str) -> "Control":
        """Set the terminal window title

        Args:
            title (str): The new terminal window title
        """
        return cls((ControlType.SET_WINDOW_TITLE, title))

    def __str__(self) -> str:
        return self.segment.text

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> "RenderResult":
        if self.segment.text:
            yield self.segment


def strip_control_codes(
    text: str, _translate_table: Dict[int, None] = _CONTROL_STRIP_TRANSLATE
) -> str:
    """Remove control codes from text.

    Args:
        text (str): A string possibly contain control codes.

    Returns:
        str: String with control codes removed.
    """
    return text.translate(_translate_table)


def escape_control_codes(
    text: str,
    _translate_table: Dict[int, str] = CONTROL_ESCAPE,
) -> str:
    """Replace control codes with their "escaped" equivalent in the given text.
    (e.g. "\b" becomes "\\b")

    Args:
        text (str): A string possibly containing control codes.

    Returns:
        str: String with control codes replaced with their escaped version.
    """
    return text.translate(_translate_table)


if __name__ == "__main__":  # pragma: no cover
    from pip._vendor.rich.console import Console

    console = Console()
    console.print("Look at the title of your terminal window ^")
    # console.print(Control((ControlType.SET_WINDOW_TITLE, "Hello, world!")))
    for i in range(10):
        console.set_window_title("🚀 Loading" + "." * i)
        time.sleep(0.5)

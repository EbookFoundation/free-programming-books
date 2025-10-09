from typing import Optional, Union

from .color import Color
from .console import Console, ConsoleOptions, RenderResult
from .jupyter import JupyterMixin
from .measure import Measurement
from .segment import Segment
from .style import Style

# There are left-aligned characters for 1/8 to 7/8, but
# the right-aligned characters exist only for 1/8 and 4/8.
BEGIN_BLOCK_ELEMENTS = ["█", "█", "█", "▐", "▐", "▐", "▕", "▕"]
END_BLOCK_ELEMENTS = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉"]
FULL_BLOCK = "█"


class Bar(JupyterMixin):
    """Renders a solid block bar.

    Args:
        size (float): Value for the end of the bar.
        begin (float): Begin point (between 0 and size, inclusive).
        end (float): End point (between 0 and size, inclusive).
        width (int, optional): Width of the bar, or ``None`` for maximum width. Defaults to None.
        color (Union[Color, str], optional): Color of the bar. Defaults to "default".
        bgcolor (Union[Color, str], optional): Color of bar background. Defaults to "default".
    """

    def __init__(
        self,
        size: float,
        begin: float,
        end: float,
        *,
        width: Optional[int] = None,
        color: Union[Color, str] = "default",
        bgcolor: Union[Color, str] = "default",
    ):
        self.size = size
        self.begin = max(begin, 0)
        self.end = min(end, size)
        self.width = width
        self.style = Style(color=color, bgcolor=bgcolor)

    def __repr__(self) -> str:
        return f"Bar({self.size}, {self.begin}, {self.end})"

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        width = min(
            self.width if self.width is not None else options.max_width,
            options.max_width,
        )

        if self.begin >= self.end:
            yield Segment(" " * width, self.style)
            yield Segment.line()
            return

        prefix_complete_eights = int(width * 8 * self.begin / self.size)
        prefix_bar_count = prefix_complete_eights // 8
        prefix_eights_count = prefix_complete_eights % 8

        body_complete_eights = int(width * 8 * self.end / self.size)
        body_bar_count = body_complete_eights // 8
        body_eights_count = body_complete_eights % 8

        # When start and end fall into the same cell, we ideally should render
        # a symbol that's "center-aligned", but there is no good symbol in Unicode.
        # In this case, we fall back to right-aligned block symbol for simplicity.

        prefix = " " * prefix_bar_count
        if prefix_eights_count:
            prefix += BEGIN_BLOCK_ELEMENTS[prefix_eights_count]

        body = FULL_BLOCK * body_bar_count
        if body_eights_count:
            body += END_BLOCK_ELEMENTS[body_eights_count]

        suffix = " " * (width - len(body))

        yield Segment(prefix + body[len(prefix) :] + suffix, self.style)
        yield Segment.line()

    def __rich_measure__(
        self, console: Console, options: ConsoleOptions
    ) -> Measurement:
        return (
            Measurement(self.width, self.width)
            if self.width is not None
            else Measurement(4, options.max_width)
        )

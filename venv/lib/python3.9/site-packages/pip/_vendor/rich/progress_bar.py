import math
from functools import lru_cache
from time import monotonic
from typing import Iterable, List, Optional

from .color import Color, blend_rgb
from .color_triplet import ColorTriplet
from .console import Console, ConsoleOptions, RenderResult
from .jupyter import JupyterMixin
from .measure import Measurement
from .segment import Segment
from .style import Style, StyleType

# Number of characters before 'pulse' animation repeats
PULSE_SIZE = 20


class ProgressBar(JupyterMixin):
    """Renders a (progress) bar. Used by rich.progress.

    Args:
        total (float, optional): Number of steps in the bar. Defaults to 100. Set to None to render a pulsing animation.
        completed (float, optional): Number of steps completed. Defaults to 0.
        width (int, optional): Width of the bar, or ``None`` for maximum width. Defaults to None.
        pulse (bool, optional): Enable pulse effect. Defaults to False. Will pulse if a None total was passed.
        style (StyleType, optional): Style for the bar background. Defaults to "bar.back".
        complete_style (StyleType, optional): Style for the completed bar. Defaults to "bar.complete".
        finished_style (StyleType, optional): Style for a finished bar. Defaults to "bar.finished".
        pulse_style (StyleType, optional): Style for pulsing bars. Defaults to "bar.pulse".
        animation_time (Optional[float], optional): Time in seconds to use for animation, or None to use system time.
    """

    def __init__(
        self,
        total: Optional[float] = 100.0,
        completed: float = 0,
        width: Optional[int] = None,
        pulse: bool = False,
        style: StyleType = "bar.back",
        complete_style: StyleType = "bar.complete",
        finished_style: StyleType = "bar.finished",
        pulse_style: StyleType = "bar.pulse",
        animation_time: Optional[float] = None,
    ):
        self.total = total
        self.completed = completed
        self.width = width
        self.pulse = pulse
        self.style = style
        self.complete_style = complete_style
        self.finished_style = finished_style
        self.pulse_style = pulse_style
        self.animation_time = animation_time

        self._pulse_segments: Optional[List[Segment]] = None

    def __repr__(self) -> str:
        return f"<Bar {self.completed!r} of {self.total!r}>"

    @property
    def percentage_completed(self) -> Optional[float]:
        """Calculate percentage complete."""
        if self.total is None:
            return None
        completed = (self.completed / self.total) * 100.0
        completed = min(100, max(0.0, completed))
        return completed

    @lru_cache(maxsize=16)
    def _get_pulse_segments(
        self,
        fore_style: Style,
        back_style: Style,
        color_system: str,
        no_color: bool,
        ascii: bool = False,
    ) -> List[Segment]:
        """Get a list of segments to render a pulse animation.

        Returns:
            List[Segment]: A list of segments, one segment per character.
        """
        bar = "-" if ascii else "━"
        segments: List[Segment] = []
        if color_system not in ("standard", "eight_bit", "truecolor") or no_color:
            segments += [Segment(bar, fore_style)] * (PULSE_SIZE // 2)
            segments += [Segment(" " if no_color else bar, back_style)] * (
                PULSE_SIZE - (PULSE_SIZE // 2)
            )
            return segments

        append = segments.append
        fore_color = (
            fore_style.color.get_truecolor()
            if fore_style.color
            else ColorTriplet(255, 0, 255)
        )
        back_color = (
            back_style.color.get_truecolor()
            if back_style.color
            else ColorTriplet(0, 0, 0)
        )
        cos = math.cos
        pi = math.pi
        _Segment = Segment
        _Style = Style
        from_triplet = Color.from_triplet

        for index in range(PULSE_SIZE):
            position = index / PULSE_SIZE
            fade = 0.5 + cos(position * pi * 2) / 2.0
            color = blend_rgb(fore_color, back_color, cross_fade=fade)
            append(_Segment(bar, _Style(color=from_triplet(color))))
        return segments

    def update(self, completed: float, total: Optional[float] = None) -> None:
        """Update progress with new values.

        Args:
            completed (float): Number of steps completed.
            total (float, optional): Total number of steps, or ``None`` to not change. Defaults to None.
        """
        self.completed = completed
        self.total = total if total is not None else self.total

    def _render_pulse(
        self, console: Console, width: int, ascii: bool = False
    ) -> Iterable[Segment]:
        """Renders the pulse animation.

        Args:
            console (Console): Console instance.
            width (int): Width in characters of pulse animation.

        Returns:
            RenderResult: [description]

        Yields:
            Iterator[Segment]: Segments to render pulse
        """
        fore_style = console.get_style(self.pulse_style, default="white")
        back_style = console.get_style(self.style, default="black")

        pulse_segments = self._get_pulse_segments(
            fore_style, back_style, console.color_system, console.no_color, ascii=ascii
        )
        segment_count = len(pulse_segments)
        current_time = (
            monotonic() if self.animation_time is None else self.animation_time
        )
        segments = pulse_segments * (int(width / segment_count) + 2)
        offset = int(-current_time * 15) % segment_count
        segments = segments[offset : offset + width]
        yield from segments

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        width = min(self.width or options.max_width, options.max_width)
        ascii = options.legacy_windows or options.ascii_only
        should_pulse = self.pulse or self.total is None
        if should_pulse:
            yield from self._render_pulse(console, width, ascii=ascii)
            return

        completed: Optional[float] = (
            min(self.total, max(0, self.completed)) if self.total is not None else None
        )

        bar = "-" if ascii else "━"
        half_bar_right = " " if ascii else "╸"
        half_bar_left = " " if ascii else "╺"
        complete_halves = (
            int(width * 2 * completed / self.total)
            if self.total and completed is not None
            else width * 2
        )
        bar_count = complete_halves // 2
        half_bar_count = complete_halves % 2
        style = console.get_style(self.style)
        is_finished = self.total is None or self.completed >= self.total
        complete_style = console.get_style(
            self.finished_style if is_finished else self.complete_style
        )
        _Segment = Segment
        if bar_count:
            yield _Segment(bar * bar_count, complete_style)
        if half_bar_count:
            yield _Segment(half_bar_right * half_bar_count, complete_style)

        if not console.no_color:
            remaining_bars = width - bar_count - half_bar_count
            if remaining_bars and console.color_system is not None:
                if not half_bar_count and bar_count:
                    yield _Segment(half_bar_left, style)
                    remaining_bars -= 1
                if remaining_bars:
                    yield _Segment(bar * remaining_bars, style)

    def __rich_measure__(
        self, console: Console, options: ConsoleOptions
    ) -> Measurement:
        return (
            Measurement(self.width, self.width)
            if self.width is not None
            else Measurement(4, options.max_width)
        )


if __name__ == "__main__":  # pragma: no cover
    console = Console()
    bar = ProgressBar(width=50, total=100)

    import time

    console.show_cursor(False)
    for n in range(0, 101, 1):
        bar.update(n)
        console.print(bar)
        console.file.write("\r")
        time.sleep(0.05)
    console.show_cursor(True)
    console.print()

from itertools import chain
from typing import TYPE_CHECKING, Iterable, Optional, Literal

from .constrain import Constrain
from .jupyter import JupyterMixin
from .measure import Measurement
from .segment import Segment
from .style import StyleType

if TYPE_CHECKING:
    from .console import Console, ConsoleOptions, RenderableType, RenderResult

AlignMethod = Literal["left", "center", "right"]
VerticalAlignMethod = Literal["top", "middle", "bottom"]


class Align(JupyterMixin):
    """Align a renderable by adding spaces if necessary.

    Args:
        renderable (RenderableType): A console renderable.
        align (AlignMethod): One of "left", "center", or "right""
        style (StyleType, optional): An optional style to apply to the background.
        vertical (Optional[VerticalAlignMethod], optional): Optional vertical align, one of "top", "middle", or "bottom". Defaults to None.
        pad (bool, optional): Pad the right with spaces. Defaults to True.
        width (int, optional): Restrict contents to given width, or None to use default width. Defaults to None.
        height (int, optional): Set height of align renderable, or None to fit to contents. Defaults to None.

    Raises:
        ValueError: if ``align`` is not one of the expected values.
    """

    def __init__(
        self,
        renderable: "RenderableType",
        align: AlignMethod = "left",
        style: Optional[StyleType] = None,
        *,
        vertical: Optional[VerticalAlignMethod] = None,
        pad: bool = True,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> None:
        if align not in ("left", "center", "right"):
            raise ValueError(
                f'invalid value for align, expected "left", "center", or "right" (not {align!r})'
            )
        if vertical is not None and vertical not in ("top", "middle", "bottom"):
            raise ValueError(
                f'invalid value for vertical, expected "top", "middle", or "bottom" (not {vertical!r})'
            )
        self.renderable = renderable
        self.align = align
        self.style = style
        self.vertical = vertical
        self.pad = pad
        self.width = width
        self.height = height

    def __repr__(self) -> str:
        return f"Align({self.renderable!r}, {self.align!r})"

    @classmethod
    def left(
        cls,
        renderable: "RenderableType",
        style: Optional[StyleType] = None,
        *,
        vertical: Optional[VerticalAlignMethod] = None,
        pad: bool = True,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> "Align":
        """Align a renderable to the left."""
        return cls(
            renderable,
            "left",
            style=style,
            vertical=vertical,
            pad=pad,
            width=width,
            height=height,
        )

    @classmethod
    def center(
        cls,
        renderable: "RenderableType",
        style: Optional[StyleType] = None,
        *,
        vertical: Optional[VerticalAlignMethod] = None,
        pad: bool = True,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> "Align":
        """Align a renderable to the center."""
        return cls(
            renderable,
            "center",
            style=style,
            vertical=vertical,
            pad=pad,
            width=width,
            height=height,
        )

    @classmethod
    def right(
        cls,
        renderable: "RenderableType",
        style: Optional[StyleType] = None,
        *,
        vertical: Optional[VerticalAlignMethod] = None,
        pad: bool = True,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> "Align":
        """Align a renderable to the right."""
        return cls(
            renderable,
            "right",
            style=style,
            vertical=vertical,
            pad=pad,
            width=width,
            height=height,
        )

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> "RenderResult":
        align = self.align
        width = console.measure(self.renderable, options=options).maximum
        rendered = console.render(
            Constrain(
                self.renderable, width if self.width is None else min(width, self.width)
            ),
            options.update(height=None),
        )
        lines = list(Segment.split_lines(rendered))
        width, height = Segment.get_shape(lines)
        lines = Segment.set_shape(lines, width, height)
        new_line = Segment.line()
        excess_space = options.max_width - width
        style = console.get_style(self.style) if self.style is not None else None

        def generate_segments() -> Iterable[Segment]:
            if excess_space <= 0:
                # Exact fit
                for line in lines:
                    yield from line
                    yield new_line

            elif align == "left":
                # Pad on the right
                pad = Segment(" " * excess_space, style) if self.pad else None
                for line in lines:
                    yield from line
                    if pad:
                        yield pad
                    yield new_line

            elif align == "center":
                # Pad left and right
                left = excess_space // 2
                pad = Segment(" " * left, style)
                pad_right = (
                    Segment(" " * (excess_space - left), style) if self.pad else None
                )
                for line in lines:
                    if left:
                        yield pad
                    yield from line
                    if pad_right:
                        yield pad_right
                    yield new_line

            elif align == "right":
                # Padding on left
                pad = Segment(" " * excess_space, style)
                for line in lines:
                    yield pad
                    yield from line
                    yield new_line

        blank_line = (
            Segment(f"{' ' * (self.width or options.max_width)}\n", style)
            if self.pad
            else Segment("\n")
        )

        def blank_lines(count: int) -> Iterable[Segment]:
            if count > 0:
                for _ in range(count):
                    yield blank_line

        vertical_height = self.height or options.height
        iter_segments: Iterable[Segment]
        if self.vertical and vertical_height is not None:
            if self.vertical == "top":
                bottom_space = vertical_height - height
                iter_segments = chain(generate_segments(), blank_lines(bottom_space))
            elif self.vertical == "middle":
                top_space = (vertical_height - height) // 2
                bottom_space = vertical_height - top_space - height
                iter_segments = chain(
                    blank_lines(top_space),
                    generate_segments(),
                    blank_lines(bottom_space),
                )
            else:  #  self.vertical == "bottom":
                top_space = vertical_height - height
                iter_segments = chain(blank_lines(top_space), generate_segments())
        else:
            iter_segments = generate_segments()
        if self.style:
            style = console.get_style(self.style)
            iter_segments = Segment.apply_style(iter_segments, style)
        yield from iter_segments

    def __rich_measure__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> Measurement:
        measurement = Measurement.get(console, options, self.renderable)
        return measurement


class VerticalCenter(JupyterMixin):
    """Vertically aligns a renderable.

    Warn:
        This class is deprecated and may be removed in a future version. Use Align class with
        `vertical="middle"`.

    Args:
        renderable (RenderableType): A renderable object.
        style (StyleType, optional): An optional style to apply to the background. Defaults to None.
    """

    def __init__(
        self,
        renderable: "RenderableType",
        style: Optional[StyleType] = None,
    ) -> None:
        self.renderable = renderable
        self.style = style

    def __repr__(self) -> str:
        return f"VerticalCenter({self.renderable!r})"

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> "RenderResult":
        style = console.get_style(self.style) if self.style is not None else None
        lines = console.render_lines(
            self.renderable, options.update(height=None), pad=False
        )
        width, _height = Segment.get_shape(lines)
        new_line = Segment.line()
        height = options.height or options.size.height
        top_space = (height - len(lines)) // 2
        bottom_space = height - top_space - len(lines)
        blank_line = Segment(f"{' ' * width}", style)

        def blank_lines(count: int) -> Iterable[Segment]:
            for _ in range(count):
                yield blank_line
                yield new_line

        if top_space > 0:
            yield from blank_lines(top_space)
        for line in lines:
            yield from line
            yield new_line
        if bottom_space > 0:
            yield from blank_lines(bottom_space)

    def __rich_measure__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> Measurement:
        measurement = Measurement.get(console, options, self.renderable)
        return measurement


if __name__ == "__main__":  # pragma: no cover
    from pip._vendor.rich.console import Console, Group
    from pip._vendor.rich.highlighter import ReprHighlighter
    from pip._vendor.rich.panel import Panel

    highlighter = ReprHighlighter()
    console = Console()

    panel = Panel(
        Group(
            Align.left(highlighter("align='left'")),
            Align.center(highlighter("align='center'")),
            Align.right(highlighter("align='right'")),
        ),
        width=60,
        style="on dark_blue",
        title="Align",
    )

    console.print(
        Align.center(panel, vertical="middle", style="on red", height=console.height)
    )

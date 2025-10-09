from math import sqrt
from functools import lru_cache
from typing import Sequence, Tuple, TYPE_CHECKING

from .color_triplet import ColorTriplet

if TYPE_CHECKING:
    from pip._vendor.rich.table import Table


class Palette:
    """A palette of available colors."""

    def __init__(self, colors: Sequence[Tuple[int, int, int]]):
        self._colors = colors

    def __getitem__(self, number: int) -> ColorTriplet:
        return ColorTriplet(*self._colors[number])

    def __rich__(self) -> "Table":
        from pip._vendor.rich.color import Color
        from pip._vendor.rich.style import Style
        from pip._vendor.rich.text import Text
        from pip._vendor.rich.table import Table

        table = Table(
            "index",
            "RGB",
            "Color",
            title="Palette",
            caption=f"{len(self._colors)} colors",
            highlight=True,
            caption_justify="right",
        )
        for index, color in enumerate(self._colors):
            table.add_row(
                str(index),
                repr(color),
                Text(" " * 16, style=Style(bgcolor=Color.from_rgb(*color))),
            )
        return table

    # This is somewhat inefficient and needs caching
    @lru_cache(maxsize=1024)
    def match(self, color: Tuple[int, int, int]) -> int:
        """Find a color from a palette that most closely matches a given color.

        Args:
            color (Tuple[int, int, int]): RGB components in range 0 > 255.

        Returns:
            int: Index of closes matching color.
        """
        red1, green1, blue1 = color
        _sqrt = sqrt
        get_color = self._colors.__getitem__

        def get_color_distance(index: int) -> float:
            """Get the distance to a color."""
            red2, green2, blue2 = get_color(index)
            red_mean = (red1 + red2) // 2
            red = red1 - red2
            green = green1 - green2
            blue = blue1 - blue2
            return _sqrt(
                (((512 + red_mean) * red * red) >> 8)
                + 4 * green * green
                + (((767 - red_mean) * blue * blue) >> 8)
            )

        min_index = min(range(len(self._colors)), key=get_color_distance)
        return min_index


if __name__ == "__main__":  # pragma: no cover
    import colorsys
    from typing import Iterable
    from pip._vendor.rich.color import Color
    from pip._vendor.rich.console import Console, ConsoleOptions
    from pip._vendor.rich.segment import Segment
    from pip._vendor.rich.style import Style

    class ColorBox:
        def __rich_console__(
            self, console: Console, options: ConsoleOptions
        ) -> Iterable[Segment]:
            height = console.size.height - 3
            for y in range(0, height):
                for x in range(options.max_width):
                    h = x / options.max_width
                    l = y / (height + 1)
                    r1, g1, b1 = colorsys.hls_to_rgb(h, l, 1.0)
                    r2, g2, b2 = colorsys.hls_to_rgb(h, l + (1 / height / 2), 1.0)
                    bgcolor = Color.from_rgb(r1 * 255, g1 * 255, b1 * 255)
                    color = Color.from_rgb(r2 * 255, g2 * 255, b2 * 255)
                    yield Segment("▄", Style(color=color, bgcolor=bgcolor))
                yield Segment.line()

    console = Console()
    console.print(ColorBox())

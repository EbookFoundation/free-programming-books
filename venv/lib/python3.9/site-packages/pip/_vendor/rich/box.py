from typing import TYPE_CHECKING, Iterable, List, Literal


from ._loop import loop_last

if TYPE_CHECKING:
    from pip._vendor.rich.console import ConsoleOptions


class Box:
    """Defines characters to render boxes.

    ┌─┬┐ top
    │ ││ head
    ├─┼┤ head_row
    │ ││ mid
    ├─┼┤ row
    ├─┼┤ foot_row
    │ ││ foot
    └─┴┘ bottom

    Args:
        box (str): Characters making up box.
        ascii (bool, optional): True if this box uses ascii characters only. Default is False.
    """

    def __init__(self, box: str, *, ascii: bool = False) -> None:
        self._box = box
        self.ascii = ascii
        line1, line2, line3, line4, line5, line6, line7, line8 = box.splitlines()
        # top
        self.top_left, self.top, self.top_divider, self.top_right = iter(line1)
        # head
        self.head_left, _, self.head_vertical, self.head_right = iter(line2)
        # head_row
        (
            self.head_row_left,
            self.head_row_horizontal,
            self.head_row_cross,
            self.head_row_right,
        ) = iter(line3)

        # mid
        self.mid_left, _, self.mid_vertical, self.mid_right = iter(line4)
        # row
        self.row_left, self.row_horizontal, self.row_cross, self.row_right = iter(line5)
        # foot_row
        (
            self.foot_row_left,
            self.foot_row_horizontal,
            self.foot_row_cross,
            self.foot_row_right,
        ) = iter(line6)
        # foot
        self.foot_left, _, self.foot_vertical, self.foot_right = iter(line7)
        # bottom
        self.bottom_left, self.bottom, self.bottom_divider, self.bottom_right = iter(
            line8
        )

    def __repr__(self) -> str:
        return "Box(...)"

    def __str__(self) -> str:
        return self._box

    def substitute(self, options: "ConsoleOptions", safe: bool = True) -> "Box":
        """Substitute this box for another if it won't render due to platform issues.

        Args:
            options (ConsoleOptions): Console options used in rendering.
            safe (bool, optional): Substitute this for another Box if there are known problems
                displaying on the platform (currently only relevant on Windows). Default is True.

        Returns:
            Box: A different Box or the same Box.
        """
        box = self
        if options.legacy_windows and safe:
            box = LEGACY_WINDOWS_SUBSTITUTIONS.get(box, box)
        if options.ascii_only and not box.ascii:
            box = ASCII
        return box

    def get_plain_headed_box(self) -> "Box":
        """If this box uses special characters for the borders of the header, then
        return the equivalent box that does not.

        Returns:
            Box: The most similar Box that doesn't use header-specific box characters.
                If the current Box already satisfies this criterion, then it's returned.
        """
        return PLAIN_HEADED_SUBSTITUTIONS.get(self, self)

    def get_top(self, widths: Iterable[int]) -> str:
        """Get the top of a simple box.

        Args:
            widths (List[int]): Widths of columns.

        Returns:
            str: A string of box characters.
        """

        parts: List[str] = []
        append = parts.append
        append(self.top_left)
        for last, width in loop_last(widths):
            append(self.top * width)
            if not last:
                append(self.top_divider)
        append(self.top_right)
        return "".join(parts)

    def get_row(
        self,
        widths: Iterable[int],
        level: Literal["head", "row", "foot", "mid"] = "row",
        edge: bool = True,
    ) -> str:
        """Get the top of a simple box.

        Args:
            width (List[int]): Widths of columns.

        Returns:
            str: A string of box characters.
        """
        if level == "head":
            left = self.head_row_left
            horizontal = self.head_row_horizontal
            cross = self.head_row_cross
            right = self.head_row_right
        elif level == "row":
            left = self.row_left
            horizontal = self.row_horizontal
            cross = self.row_cross
            right = self.row_right
        elif level == "mid":
            left = self.mid_left
            horizontal = " "
            cross = self.mid_vertical
            right = self.mid_right
        elif level == "foot":
            left = self.foot_row_left
            horizontal = self.foot_row_horizontal
            cross = self.foot_row_cross
            right = self.foot_row_right
        else:
            raise ValueError("level must be 'head', 'row' or 'foot'")

        parts: List[str] = []
        append = parts.append
        if edge:
            append(left)
        for last, width in loop_last(widths):
            append(horizontal * width)
            if not last:
                append(cross)
        if edge:
            append(right)
        return "".join(parts)

    def get_bottom(self, widths: Iterable[int]) -> str:
        """Get the bottom of a simple box.

        Args:
            widths (List[int]): Widths of columns.

        Returns:
            str: A string of box characters.
        """

        parts: List[str] = []
        append = parts.append
        append(self.bottom_left)
        for last, width in loop_last(widths):
            append(self.bottom * width)
            if not last:
                append(self.bottom_divider)
        append(self.bottom_right)
        return "".join(parts)


# fmt: off
ASCII: Box = Box(
    "+--+\n"
    "| ||\n"
    "|-+|\n"
    "| ||\n"
    "|-+|\n"
    "|-+|\n"
    "| ||\n"
    "+--+\n",
    ascii=True,
)

ASCII2: Box = Box(
    "+-++\n"
    "| ||\n"
    "+-++\n"
    "| ||\n"
    "+-++\n"
    "+-++\n"
    "| ||\n"
    "+-++\n",
    ascii=True,
)

ASCII_DOUBLE_HEAD: Box = Box(
    "+-++\n"
    "| ||\n"
    "+=++\n"
    "| ||\n"
    "+-++\n"
    "+-++\n"
    "| ||\n"
    "+-++\n",
    ascii=True,
)

SQUARE: Box = Box(
    "┌─┬┐\n"
    "│ ││\n"
    "├─┼┤\n"
    "│ ││\n"
    "├─┼┤\n"
    "├─┼┤\n"
    "│ ││\n"
    "└─┴┘\n"
)

SQUARE_DOUBLE_HEAD: Box = Box(
    "┌─┬┐\n"
    "│ ││\n"
    "╞═╪╡\n"
    "│ ││\n"
    "├─┼┤\n"
    "├─┼┤\n"
    "│ ││\n"
    "└─┴┘\n"
)

MINIMAL: Box = Box(
    "  ╷ \n"
    "  │ \n"
    "╶─┼╴\n"
    "  │ \n"
    "╶─┼╴\n"
    "╶─┼╴\n"
    "  │ \n"
    "  ╵ \n"
)


MINIMAL_HEAVY_HEAD: Box = Box(
    "  ╷ \n"
    "  │ \n"
    "╺━┿╸\n"
    "  │ \n"
    "╶─┼╴\n"
    "╶─┼╴\n"
    "  │ \n"
    "  ╵ \n"
)

MINIMAL_DOUBLE_HEAD: Box = Box(
    "  ╷ \n"
    "  │ \n"
    " ═╪ \n"
    "  │ \n"
    " ─┼ \n"
    " ─┼ \n"
    "  │ \n"
    "  ╵ \n"
)


SIMPLE: Box = Box(
    "    \n"
    "    \n"
    " ── \n"
    "    \n"
    "    \n"
    " ── \n"
    "    \n"
    "    \n"
)

SIMPLE_HEAD: Box = Box(
    "    \n"
    "    \n"
    " ── \n"
    "    \n"
    "    \n"
    "    \n"
    "    \n"
    "    \n"
)


SIMPLE_HEAVY: Box = Box(
    "    \n"
    "    \n"
    " ━━ \n"
    "    \n"
    "    \n"
    " ━━ \n"
    "    \n"
    "    \n"
)


HORIZONTALS: Box = Box(
    " ── \n"
    "    \n"
    " ── \n"
    "    \n"
    " ── \n"
    " ── \n"
    "    \n"
    " ── \n"
)

ROUNDED: Box = Box(
    "╭─┬╮\n"
    "│ ││\n"
    "├─┼┤\n"
    "│ ││\n"
    "├─┼┤\n"
    "├─┼┤\n"
    "│ ││\n"
    "╰─┴╯\n"
)

HEAVY: Box = Box(
    "┏━┳┓\n"
    "┃ ┃┃\n"
    "┣━╋┫\n"
    "┃ ┃┃\n"
    "┣━╋┫\n"
    "┣━╋┫\n"
    "┃ ┃┃\n"
    "┗━┻┛\n"
)

HEAVY_EDGE: Box = Box(
    "┏━┯┓\n"
    "┃ │┃\n"
    "┠─┼┨\n"
    "┃ │┃\n"
    "┠─┼┨\n"
    "┠─┼┨\n"
    "┃ │┃\n"
    "┗━┷┛\n"
)

HEAVY_HEAD: Box = Box(
    "┏━┳┓\n"
    "┃ ┃┃\n"
    "┡━╇┩\n"
    "│ ││\n"
    "├─┼┤\n"
    "├─┼┤\n"
    "│ ││\n"
    "└─┴┘\n"
)

DOUBLE: Box = Box(
    "╔═╦╗\n"
    "║ ║║\n"
    "╠═╬╣\n"
    "║ ║║\n"
    "╠═╬╣\n"
    "╠═╬╣\n"
    "║ ║║\n"
    "╚═╩╝\n"
)

DOUBLE_EDGE: Box = Box(
    "╔═╤╗\n"
    "║ │║\n"
    "╟─┼╢\n"
    "║ │║\n"
    "╟─┼╢\n"
    "╟─┼╢\n"
    "║ │║\n"
    "╚═╧╝\n"
)

MARKDOWN: Box = Box(
    "    \n"
    "| ||\n"
    "|-||\n"
    "| ||\n"
    "|-||\n"
    "|-||\n"
    "| ||\n"
    "    \n",
    ascii=True,
)
# fmt: on

# Map Boxes that don't render with raster fonts on to equivalent that do
LEGACY_WINDOWS_SUBSTITUTIONS = {
    ROUNDED: SQUARE,
    MINIMAL_HEAVY_HEAD: MINIMAL,
    SIMPLE_HEAVY: SIMPLE,
    HEAVY: SQUARE,
    HEAVY_EDGE: SQUARE,
    HEAVY_HEAD: SQUARE,
}

# Map headed boxes to their headerless equivalents
PLAIN_HEADED_SUBSTITUTIONS = {
    HEAVY_HEAD: SQUARE,
    SQUARE_DOUBLE_HEAD: SQUARE,
    MINIMAL_DOUBLE_HEAD: MINIMAL,
    MINIMAL_HEAVY_HEAD: MINIMAL,
    ASCII_DOUBLE_HEAD: ASCII2,
}


if __name__ == "__main__":  # pragma: no cover
    from pip._vendor.rich.columns import Columns
    from pip._vendor.rich.panel import Panel

    from . import box as box
    from .console import Console
    from .table import Table
    from .text import Text

    console = Console(record=True)

    BOXES = [
        "ASCII",
        "ASCII2",
        "ASCII_DOUBLE_HEAD",
        "SQUARE",
        "SQUARE_DOUBLE_HEAD",
        "MINIMAL",
        "MINIMAL_HEAVY_HEAD",
        "MINIMAL_DOUBLE_HEAD",
        "SIMPLE",
        "SIMPLE_HEAD",
        "SIMPLE_HEAVY",
        "HORIZONTALS",
        "ROUNDED",
        "HEAVY",
        "HEAVY_EDGE",
        "HEAVY_HEAD",
        "DOUBLE",
        "DOUBLE_EDGE",
        "MARKDOWN",
    ]

    console.print(Panel("[bold green]Box Constants", style="green"), justify="center")
    console.print()

    columns = Columns(expand=True, padding=2)
    for box_name in sorted(BOXES):
        table = Table(
            show_footer=True, style="dim", border_style="not dim", expand=True
        )
        table.add_column("Header 1", "Footer 1")
        table.add_column("Header 2", "Footer 2")
        table.add_row("Cell", "Cell")
        table.add_row("Cell", "Cell")
        table.box = getattr(box, box_name)
        table.title = Text(f"box.{box_name}", style="magenta")
        columns.add_renderable(table)
    console.print(columns)

    # console.save_svg("box.svg")

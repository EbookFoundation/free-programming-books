from collections import defaultdict
from itertools import chain
from operator import itemgetter
from typing import Dict, Iterable, List, Optional, Tuple

from .align import Align, AlignMethod
from .console import Console, ConsoleOptions, RenderableType, RenderResult
from .constrain import Constrain
from .measure import Measurement
from .padding import Padding, PaddingDimensions
from .table import Table
from .text import TextType
from .jupyter import JupyterMixin


class Columns(JupyterMixin):
    """Display renderables in neat columns.

    Args:
        renderables (Iterable[RenderableType]): Any number of Rich renderables (including str).
        width (int, optional): The desired width of the columns, or None to auto detect. Defaults to None.
        padding (PaddingDimensions, optional): Optional padding around cells. Defaults to (0, 1).
        expand (bool, optional): Expand columns to full width. Defaults to False.
        equal (bool, optional): Arrange in to equal sized columns. Defaults to False.
        column_first (bool, optional): Align items from top to bottom (rather than left to right). Defaults to False.
        right_to_left (bool, optional): Start column from right hand side. Defaults to False.
        align (str, optional): Align value ("left", "right", or "center") or None for default. Defaults to None.
        title (TextType, optional): Optional title for Columns.
    """

    def __init__(
        self,
        renderables: Optional[Iterable[RenderableType]] = None,
        padding: PaddingDimensions = (0, 1),
        *,
        width: Optional[int] = None,
        expand: bool = False,
        equal: bool = False,
        column_first: bool = False,
        right_to_left: bool = False,
        align: Optional[AlignMethod] = None,
        title: Optional[TextType] = None,
    ) -> None:
        self.renderables = list(renderables or [])
        self.width = width
        self.padding = padding
        self.expand = expand
        self.equal = equal
        self.column_first = column_first
        self.right_to_left = right_to_left
        self.align: Optional[AlignMethod] = align
        self.title = title

    def add_renderable(self, renderable: RenderableType) -> None:
        """Add a renderable to the columns.

        Args:
            renderable (RenderableType): Any renderable object.
        """
        self.renderables.append(renderable)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        render_str = console.render_str
        renderables = [
            render_str(renderable) if isinstance(renderable, str) else renderable
            for renderable in self.renderables
        ]
        if not renderables:
            return
        _top, right, _bottom, left = Padding.unpack(self.padding)
        width_padding = max(left, right)
        max_width = options.max_width
        widths: Dict[int, int] = defaultdict(int)
        column_count = len(renderables)

        get_measurement = Measurement.get
        renderable_widths = [
            get_measurement(console, options, renderable).maximum
            for renderable in renderables
        ]
        if self.equal:
            renderable_widths = [max(renderable_widths)] * len(renderable_widths)

        def iter_renderables(
            column_count: int,
        ) -> Iterable[Tuple[int, Optional[RenderableType]]]:
            item_count = len(renderables)
            if self.column_first:
                width_renderables = list(zip(renderable_widths, renderables))

                column_lengths: List[int] = [item_count // column_count] * column_count
                for col_no in range(item_count % column_count):
                    column_lengths[col_no] += 1

                row_count = (item_count + column_count - 1) // column_count
                cells = [[-1] * column_count for _ in range(row_count)]
                row = col = 0
                for index in range(item_count):
                    cells[row][col] = index
                    column_lengths[col] -= 1
                    if column_lengths[col]:
                        row += 1
                    else:
                        col += 1
                        row = 0
                for index in chain.from_iterable(cells):
                    if index == -1:
                        break
                    yield width_renderables[index]
            else:
                yield from zip(renderable_widths, renderables)
            # Pad odd elements with spaces
            if item_count % column_count:
                for _ in range(column_count - (item_count % column_count)):
                    yield 0, None

        table = Table.grid(padding=self.padding, collapse_padding=True, pad_edge=False)
        table.expand = self.expand
        table.title = self.title

        if self.width is not None:
            column_count = (max_width) // (self.width + width_padding)
            for _ in range(column_count):
                table.add_column(width=self.width)
        else:
            while column_count > 1:
                widths.clear()
                column_no = 0
                for renderable_width, _ in iter_renderables(column_count):
                    widths[column_no] = max(widths[column_no], renderable_width)
                    total_width = sum(widths.values()) + width_padding * (
                        len(widths) - 1
                    )
                    if total_width > max_width:
                        column_count = len(widths) - 1
                        break
                    else:
                        column_no = (column_no + 1) % column_count
                else:
                    break

        get_renderable = itemgetter(1)
        _renderables = [
            get_renderable(_renderable)
            for _renderable in iter_renderables(column_count)
        ]
        if self.equal:
            _renderables = [
                None
                if renderable is None
                else Constrain(renderable, renderable_widths[0])
                for renderable in _renderables
            ]
        if self.align:
            align = self.align
            _Align = Align
            _renderables = [
                None if renderable is None else _Align(renderable, align)
                for renderable in _renderables
            ]

        right_to_left = self.right_to_left
        add_row = table.add_row
        for start in range(0, len(_renderables), column_count):
            row = _renderables[start : start + column_count]
            if right_to_left:
                row = row[::-1]
            add_row(*row)
        yield table


if __name__ == "__main__":  # pragma: no cover
    import os

    console = Console()

    files = [f"{i} {s}" for i, s in enumerate(sorted(os.listdir()))]
    columns = Columns(files, padding=(0, 1), expand=False, equal=False)
    console.print(columns)
    console.rule()
    columns.column_first = True
    console.print(columns)
    columns.right_to_left = True
    console.rule()
    console.print(columns)

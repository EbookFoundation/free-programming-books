from abc import ABC, abstractmethod
from itertools import islice
from operator import itemgetter
from threading import RLock
from typing import (
    TYPE_CHECKING,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from ._ratio import ratio_resolve
from .align import Align
from .console import Console, ConsoleOptions, RenderableType, RenderResult
from .highlighter import ReprHighlighter
from .panel import Panel
from .pretty import Pretty
from .region import Region
from .repr import Result, rich_repr
from .segment import Segment
from .style import StyleType

if TYPE_CHECKING:
    from pip._vendor.rich.tree import Tree


class LayoutRender(NamedTuple):
    """An individual layout render."""

    region: Region
    render: List[List[Segment]]


RegionMap = Dict["Layout", Region]
RenderMap = Dict["Layout", LayoutRender]


class LayoutError(Exception):
    """Layout related error."""


class NoSplitter(LayoutError):
    """Requested splitter does not exist."""


class _Placeholder:
    """An internal renderable used as a Layout placeholder."""

    highlighter = ReprHighlighter()

    def __init__(self, layout: "Layout", style: StyleType = "") -> None:
        self.layout = layout
        self.style = style

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        width = options.max_width
        height = options.height or options.size.height
        layout = self.layout
        title = (
            f"{layout.name!r} ({width} x {height})"
            if layout.name
            else f"({width} x {height})"
        )
        yield Panel(
            Align.center(Pretty(layout), vertical="middle"),
            style=self.style,
            title=self.highlighter(title),
            border_style="blue",
            height=height,
        )


class Splitter(ABC):
    """Base class for a splitter."""

    name: str = ""

    @abstractmethod
    def get_tree_icon(self) -> str:
        """Get the icon (emoji) used in layout.tree"""

    @abstractmethod
    def divide(
        self, children: Sequence["Layout"], region: Region
    ) -> Iterable[Tuple["Layout", Region]]:
        """Divide a region amongst several child layouts.

        Args:
            children (Sequence(Layout)): A number of child layouts.
            region (Region): A rectangular region to divide.
        """


class RowSplitter(Splitter):
    """Split a layout region in to rows."""

    name = "row"

    def get_tree_icon(self) -> str:
        return "[layout.tree.row]⬌"

    def divide(
        self, children: Sequence["Layout"], region: Region
    ) -> Iterable[Tuple["Layout", Region]]:
        x, y, width, height = region
        render_widths = ratio_resolve(width, children)
        offset = 0
        _Region = Region
        for child, child_width in zip(children, render_widths):
            yield child, _Region(x + offset, y, child_width, height)
            offset += child_width


class ColumnSplitter(Splitter):
    """Split a layout region in to columns."""

    name = "column"

    def get_tree_icon(self) -> str:
        return "[layout.tree.column]⬍"

    def divide(
        self, children: Sequence["Layout"], region: Region
    ) -> Iterable[Tuple["Layout", Region]]:
        x, y, width, height = region
        render_heights = ratio_resolve(height, children)
        offset = 0
        _Region = Region
        for child, child_height in zip(children, render_heights):
            yield child, _Region(x, y + offset, width, child_height)
            offset += child_height


@rich_repr
class Layout:
    """A renderable to divide a fixed height in to rows or columns.

    Args:
        renderable (RenderableType, optional): Renderable content, or None for placeholder. Defaults to None.
        name (str, optional): Optional identifier for Layout. Defaults to None.
        size (int, optional): Optional fixed size of layout. Defaults to None.
        minimum_size (int, optional): Minimum size of layout. Defaults to 1.
        ratio (int, optional): Optional ratio for flexible layout. Defaults to 1.
        visible (bool, optional): Visibility of layout. Defaults to True.
    """

    splitters = {"row": RowSplitter, "column": ColumnSplitter}

    def __init__(
        self,
        renderable: Optional[RenderableType] = None,
        *,
        name: Optional[str] = None,
        size: Optional[int] = None,
        minimum_size: int = 1,
        ratio: int = 1,
        visible: bool = True,
    ) -> None:
        self._renderable = renderable or _Placeholder(self)
        self.size = size
        self.minimum_size = minimum_size
        self.ratio = ratio
        self.name = name
        self.visible = visible
        self.splitter: Splitter = self.splitters["column"]()
        self._children: List[Layout] = []
        self._render_map: RenderMap = {}
        self._lock = RLock()

    def __rich_repr__(self) -> Result:
        yield "name", self.name, None
        yield "size", self.size, None
        yield "minimum_size", self.minimum_size, 1
        yield "ratio", self.ratio, 1

    @property
    def renderable(self) -> RenderableType:
        """Layout renderable."""
        return self if self._children else self._renderable

    @property
    def children(self) -> List["Layout"]:
        """Gets (visible) layout children."""
        return [child for child in self._children if child.visible]

    @property
    def map(self) -> RenderMap:
        """Get a map of the last render."""
        return self._render_map

    def get(self, name: str) -> Optional["Layout"]:
        """Get a named layout, or None if it doesn't exist.

        Args:
            name (str): Name of layout.

        Returns:
            Optional[Layout]: Layout instance or None if no layout was found.
        """
        if self.name == name:
            return self
        else:
            for child in self._children:
                named_layout = child.get(name)
                if named_layout is not None:
                    return named_layout
        return None

    def __getitem__(self, name: str) -> "Layout":
        layout = self.get(name)
        if layout is None:
            raise KeyError(f"No layout with name {name!r}")
        return layout

    @property
    def tree(self) -> "Tree":
        """Get a tree renderable to show layout structure."""
        from pip._vendor.rich.styled import Styled
        from pip._vendor.rich.table import Table
        from pip._vendor.rich.tree import Tree

        def summary(layout: "Layout") -> Table:
            icon = layout.splitter.get_tree_icon()

            table = Table.grid(padding=(0, 1, 0, 0))

            text: RenderableType = (
                Pretty(layout) if layout.visible else Styled(Pretty(layout), "dim")
            )
            table.add_row(icon, text)
            _summary = table
            return _summary

        layout = self
        tree = Tree(
            summary(layout),
            guide_style=f"layout.tree.{layout.splitter.name}",
            highlight=True,
        )

        def recurse(tree: "Tree", layout: "Layout") -> None:
            for child in layout._children:
                recurse(
                    tree.add(
                        summary(child),
                        guide_style=f"layout.tree.{child.splitter.name}",
                    ),
                    child,
                )

        recurse(tree, self)
        return tree

    def split(
        self,
        *layouts: Union["Layout", RenderableType],
        splitter: Union[Splitter, str] = "column",
    ) -> None:
        """Split the layout in to multiple sub-layouts.

        Args:
            *layouts (Layout): Positional arguments should be (sub) Layout instances.
            splitter (Union[Splitter, str]): Splitter instance or name of splitter.
        """
        _layouts = [
            layout if isinstance(layout, Layout) else Layout(layout)
            for layout in layouts
        ]
        try:
            self.splitter = (
                splitter
                if isinstance(splitter, Splitter)
                else self.splitters[splitter]()
            )
        except KeyError:
            raise NoSplitter(f"No splitter called {splitter!r}")
        self._children[:] = _layouts

    def add_split(self, *layouts: Union["Layout", RenderableType]) -> None:
        """Add a new layout(s) to existing split.

        Args:
            *layouts (Union[Layout, RenderableType]): Positional arguments should be renderables or (sub) Layout instances.

        """
        _layouts = (
            layout if isinstance(layout, Layout) else Layout(layout)
            for layout in layouts
        )
        self._children.extend(_layouts)

    def split_row(self, *layouts: Union["Layout", RenderableType]) -> None:
        """Split the layout in to a row (layouts side by side).

        Args:
            *layouts (Layout): Positional arguments should be (sub) Layout instances.
        """
        self.split(*layouts, splitter="row")

    def split_column(self, *layouts: Union["Layout", RenderableType]) -> None:
        """Split the layout in to a column (layouts stacked on top of each other).

        Args:
            *layouts (Layout): Positional arguments should be (sub) Layout instances.
        """
        self.split(*layouts, splitter="column")

    def unsplit(self) -> None:
        """Reset splits to initial state."""
        del self._children[:]

    def update(self, renderable: RenderableType) -> None:
        """Update renderable.

        Args:
            renderable (RenderableType): New renderable object.
        """
        with self._lock:
            self._renderable = renderable

    def refresh_screen(self, console: "Console", layout_name: str) -> None:
        """Refresh a sub-layout.

        Args:
            console (Console): Console instance where Layout is to be rendered.
            layout_name (str): Name of layout.
        """
        with self._lock:
            layout = self[layout_name]
            region, _lines = self._render_map[layout]
            (x, y, width, height) = region
            lines = console.render_lines(
                layout, console.options.update_dimensions(width, height)
            )
            self._render_map[layout] = LayoutRender(region, lines)
            console.update_screen_lines(lines, x, y)

    def _make_region_map(self, width: int, height: int) -> RegionMap:
        """Create a dict that maps layout on to Region."""
        stack: List[Tuple[Layout, Region]] = [(self, Region(0, 0, width, height))]
        push = stack.append
        pop = stack.pop
        layout_regions: List[Tuple[Layout, Region]] = []
        append_layout_region = layout_regions.append
        while stack:
            append_layout_region(pop())
            layout, region = layout_regions[-1]
            children = layout.children
            if children:
                for child_and_region in layout.splitter.divide(children, region):
                    push(child_and_region)

        region_map = {
            layout: region
            for layout, region in sorted(layout_regions, key=itemgetter(1))
        }
        return region_map

    def render(self, console: Console, options: ConsoleOptions) -> RenderMap:
        """Render the sub_layouts.

        Args:
            console (Console): Console instance.
            options (ConsoleOptions): Console options.

        Returns:
            RenderMap: A dict that maps Layout on to a tuple of Region, lines
        """
        render_width = options.max_width
        render_height = options.height or console.height
        region_map = self._make_region_map(render_width, render_height)
        layout_regions = [
            (layout, region)
            for layout, region in region_map.items()
            if not layout.children
        ]
        render_map: Dict["Layout", "LayoutRender"] = {}
        render_lines = console.render_lines
        update_dimensions = options.update_dimensions

        for layout, region in layout_regions:
            lines = render_lines(
                layout.renderable, update_dimensions(region.width, region.height)
            )
            render_map[layout] = LayoutRender(region, lines)
        return render_map

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        with self._lock:
            width = options.max_width or console.width
            height = options.height or console.height
            render_map = self.render(console, options.update_dimensions(width, height))
            self._render_map = render_map
            layout_lines: List[List[Segment]] = [[] for _ in range(height)]
            _islice = islice
            for region, lines in render_map.values():
                _x, y, _layout_width, layout_height = region
                for row, line in zip(
                    _islice(layout_lines, y, y + layout_height), lines
                ):
                    row.extend(line)

            new_line = Segment.line()
            for layout_row in layout_lines:
                yield from layout_row
                yield new_line


if __name__ == "__main__":
    from pip._vendor.rich.console import Console

    console = Console()
    layout = Layout()

    layout.split_column(
        Layout(name="header", size=3),
        Layout(ratio=1, name="main"),
        Layout(size=10, name="footer"),
    )

    layout["main"].split_row(Layout(name="side"), Layout(name="body", ratio=2))

    layout["body"].split_row(Layout(name="content", ratio=2), Layout(name="s2"))

    layout["s2"].split_column(
        Layout(name="top"), Layout(name="middle"), Layout(name="bottom")
    )

    layout["side"].split_column(Layout(layout.tree, name="left1"), Layout(name="left2"))

    layout["content"].update("foo")

    console.print(layout)

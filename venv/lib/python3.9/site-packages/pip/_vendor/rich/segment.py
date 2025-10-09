from enum import IntEnum
from functools import lru_cache
from itertools import filterfalse
from logging import getLogger
from operator import attrgetter
from typing import (
    TYPE_CHECKING,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
)

from .cells import (
    _is_single_cell_widths,
    cached_cell_len,
    cell_len,
    get_character_cell_size,
    set_cell_size,
)
from .repr import Result, rich_repr
from .style import Style

if TYPE_CHECKING:
    from .console import Console, ConsoleOptions, RenderResult

log = getLogger("rich")


class ControlType(IntEnum):
    """Non-printable control codes which typically translate to ANSI codes."""

    BELL = 1
    CARRIAGE_RETURN = 2
    HOME = 3
    CLEAR = 4
    SHOW_CURSOR = 5
    HIDE_CURSOR = 6
    ENABLE_ALT_SCREEN = 7
    DISABLE_ALT_SCREEN = 8
    CURSOR_UP = 9
    CURSOR_DOWN = 10
    CURSOR_FORWARD = 11
    CURSOR_BACKWARD = 12
    CURSOR_MOVE_TO_COLUMN = 13
    CURSOR_MOVE_TO = 14
    ERASE_IN_LINE = 15
    SET_WINDOW_TITLE = 16


ControlCode = Union[
    Tuple[ControlType],
    Tuple[ControlType, Union[int, str]],
    Tuple[ControlType, int, int],
]


@rich_repr()
class Segment(NamedTuple):
    """A piece of text with associated style. Segments are produced by the Console render process and
    are ultimately converted in to strings to be written to the terminal.

    Args:
        text (str): A piece of text.
        style (:class:`~rich.style.Style`, optional): An optional style to apply to the text.
        control (Tuple[ControlCode], optional): Optional sequence of control codes.

    Attributes:
        cell_length (int): The cell length of this Segment.
    """

    text: str
    style: Optional[Style] = None
    control: Optional[Sequence[ControlCode]] = None

    @property
    def cell_length(self) -> int:
        """The number of terminal cells required to display self.text.

        Returns:
            int: A number of cells.
        """
        text, _style, control = self
        return 0 if control else cell_len(text)

    def __rich_repr__(self) -> Result:
        yield self.text
        if self.control is None:
            if self.style is not None:
                yield self.style
        else:
            yield self.style
            yield self.control

    def __bool__(self) -> bool:
        """Check if the segment contains text."""
        return bool(self.text)

    @property
    def is_control(self) -> bool:
        """Check if the segment contains control codes."""
        return self.control is not None

    @classmethod
    @lru_cache(1024 * 16)
    def _split_cells(cls, segment: "Segment", cut: int) -> Tuple["Segment", "Segment"]:
        """Split a segment in to two at a given cell position.

        Note that splitting a double-width character, may result in that character turning
        into two spaces.

        Args:
            segment (Segment): A segment to split.
            cut (int): A cell position to cut on.

        Returns:
            A tuple of two segments.
        """
        text, style, control = segment
        _Segment = Segment
        cell_length = segment.cell_length
        if cut >= cell_length:
            return segment, _Segment("", style, control)

        cell_size = get_character_cell_size

        pos = int((cut / cell_length) * len(text))

        while True:
            before = text[:pos]
            cell_pos = cell_len(before)
            out_by = cell_pos - cut
            if not out_by:
                return (
                    _Segment(before, style, control),
                    _Segment(text[pos:], style, control),
                )
            if out_by == -1 and cell_size(text[pos]) == 2:
                return (
                    _Segment(text[:pos] + " ", style, control),
                    _Segment(" " + text[pos + 1 :], style, control),
                )
            if out_by == +1 and cell_size(text[pos - 1]) == 2:
                return (
                    _Segment(text[: pos - 1] + " ", style, control),
                    _Segment(" " + text[pos:], style, control),
                )
            if cell_pos < cut:
                pos += 1
            else:
                pos -= 1

    def split_cells(self, cut: int) -> Tuple["Segment", "Segment"]:
        """Split segment in to two segments at the specified column.

        If the cut point falls in the middle of a 2-cell wide character then it is replaced
        by two spaces, to preserve the display width of the parent segment.

        Args:
            cut (int): Offset within the segment to cut.

        Returns:
            Tuple[Segment, Segment]: Two segments.
        """
        text, style, control = self
        assert cut >= 0

        if _is_single_cell_widths(text):
            # Fast path with all 1 cell characters
            if cut >= len(text):
                return self, Segment("", style, control)
            return (
                Segment(text[:cut], style, control),
                Segment(text[cut:], style, control),
            )

        return self._split_cells(self, cut)

    @classmethod
    def line(cls) -> "Segment":
        """Make a new line segment."""
        return cls("\n")

    @classmethod
    def apply_style(
        cls,
        segments: Iterable["Segment"],
        style: Optional[Style] = None,
        post_style: Optional[Style] = None,
    ) -> Iterable["Segment"]:
        """Apply style(s) to an iterable of segments.

        Returns an iterable of segments where the style is replaced by ``style + segment.style + post_style``.

        Args:
            segments (Iterable[Segment]): Segments to process.
            style (Style, optional): Base style. Defaults to None.
            post_style (Style, optional): Style to apply on top of segment style. Defaults to None.

        Returns:
            Iterable[Segments]: A new iterable of segments (possibly the same iterable).
        """
        result_segments = segments
        if style:
            apply = style.__add__
            result_segments = (
                cls(text, None if control else apply(_style), control)
                for text, _style, control in result_segments
            )
        if post_style:
            result_segments = (
                cls(
                    text,
                    (
                        None
                        if control
                        else (_style + post_style if _style else post_style)
                    ),
                    control,
                )
                for text, _style, control in result_segments
            )
        return result_segments

    @classmethod
    def filter_control(
        cls, segments: Iterable["Segment"], is_control: bool = False
    ) -> Iterable["Segment"]:
        """Filter segments by ``is_control`` attribute.

        Args:
            segments (Iterable[Segment]): An iterable of Segment instances.
            is_control (bool, optional): is_control flag to match in search.

        Returns:
            Iterable[Segment]: And iterable of Segment instances.

        """
        if is_control:
            return filter(attrgetter("control"), segments)
        else:
            return filterfalse(attrgetter("control"), segments)

    @classmethod
    def split_lines(cls, segments: Iterable["Segment"]) -> Iterable[List["Segment"]]:
        """Split a sequence of segments in to a list of lines.

        Args:
            segments (Iterable[Segment]): Segments potentially containing line feeds.

        Yields:
            Iterable[List[Segment]]: Iterable of segment lists, one per line.
        """
        line: List[Segment] = []
        append = line.append

        for segment in segments:
            if "\n" in segment.text and not segment.control:
                text, style, _ = segment
                while text:
                    _text, new_line, text = text.partition("\n")
                    if _text:
                        append(cls(_text, style))
                    if new_line:
                        yield line
                        line = []
                        append = line.append
            else:
                append(segment)
        if line:
            yield line

    @classmethod
    def split_and_crop_lines(
        cls,
        segments: Iterable["Segment"],
        length: int,
        style: Optional[Style] = None,
        pad: bool = True,
        include_new_lines: bool = True,
    ) -> Iterable[List["Segment"]]:
        """Split segments in to lines, and crop lines greater than a given length.

        Args:
            segments (Iterable[Segment]): An iterable of segments, probably
                generated from console.render.
            length (int): Desired line length.
            style (Style, optional): Style to use for any padding.
            pad (bool): Enable padding of lines that are less than `length`.

        Returns:
            Iterable[List[Segment]]: An iterable of lines of segments.
        """
        line: List[Segment] = []
        append = line.append

        adjust_line_length = cls.adjust_line_length
        new_line_segment = cls("\n")

        for segment in segments:
            if "\n" in segment.text and not segment.control:
                text, segment_style, _ = segment
                while text:
                    _text, new_line, text = text.partition("\n")
                    if _text:
                        append(cls(_text, segment_style))
                    if new_line:
                        cropped_line = adjust_line_length(
                            line, length, style=style, pad=pad
                        )
                        if include_new_lines:
                            cropped_line.append(new_line_segment)
                        yield cropped_line
                        line.clear()
            else:
                append(segment)
        if line:
            yield adjust_line_length(line, length, style=style, pad=pad)

    @classmethod
    def adjust_line_length(
        cls,
        line: List["Segment"],
        length: int,
        style: Optional[Style] = None,
        pad: bool = True,
    ) -> List["Segment"]:
        """Adjust a line to a given width (cropping or padding as required).

        Args:
            segments (Iterable[Segment]): A list of segments in a single line.
            length (int): The desired width of the line.
            style (Style, optional): The style of padding if used (space on the end). Defaults to None.
            pad (bool, optional): Pad lines with spaces if they are shorter than `length`. Defaults to True.

        Returns:
            List[Segment]: A line of segments with the desired length.
        """
        line_length = sum(segment.cell_length for segment in line)
        new_line: List[Segment]

        if line_length < length:
            if pad:
                new_line = line + [cls(" " * (length - line_length), style)]
            else:
                new_line = line[:]
        elif line_length > length:
            new_line = []
            append = new_line.append
            line_length = 0
            for segment in line:
                segment_length = segment.cell_length
                if line_length + segment_length < length or segment.control:
                    append(segment)
                    line_length += segment_length
                else:
                    text, segment_style, _ = segment
                    text = set_cell_size(text, length - line_length)
                    append(cls(text, segment_style))
                    break
        else:
            new_line = line[:]
        return new_line

    @classmethod
    def get_line_length(cls, line: List["Segment"]) -> int:
        """Get the length of list of segments.

        Args:
            line (List[Segment]): A line encoded as a list of Segments (assumes no '\\\\n' characters),

        Returns:
            int: The length of the line.
        """
        _cell_len = cell_len
        return sum(_cell_len(text) for text, style, control in line if not control)

    @classmethod
    def get_shape(cls, lines: List[List["Segment"]]) -> Tuple[int, int]:
        """Get the shape (enclosing rectangle) of a list of lines.

        Args:
            lines (List[List[Segment]]): A list of lines (no '\\\\n' characters).

        Returns:
            Tuple[int, int]: Width and height in characters.
        """
        get_line_length = cls.get_line_length
        max_width = max(get_line_length(line) for line in lines) if lines else 0
        return (max_width, len(lines))

    @classmethod
    def set_shape(
        cls,
        lines: List[List["Segment"]],
        width: int,
        height: Optional[int] = None,
        style: Optional[Style] = None,
        new_lines: bool = False,
    ) -> List[List["Segment"]]:
        """Set the shape of a list of lines (enclosing rectangle).

        Args:
            lines (List[List[Segment]]): A list of lines.
            width (int): Desired width.
            height (int, optional): Desired height or None for no change.
            style (Style, optional): Style of any padding added.
            new_lines (bool, optional): Padded lines should include "\n". Defaults to False.

        Returns:
            List[List[Segment]]: New list of lines.
        """
        _height = height or len(lines)

        blank = (
            [cls(" " * width + "\n", style)] if new_lines else [cls(" " * width, style)]
        )

        adjust_line_length = cls.adjust_line_length
        shaped_lines = lines[:_height]
        shaped_lines[:] = [
            adjust_line_length(line, width, style=style) for line in lines
        ]
        if len(shaped_lines) < _height:
            shaped_lines.extend([blank] * (_height - len(shaped_lines)))
        return shaped_lines

    @classmethod
    def align_top(
        cls: Type["Segment"],
        lines: List[List["Segment"]],
        width: int,
        height: int,
        style: Style,
        new_lines: bool = False,
    ) -> List[List["Segment"]]:
        """Aligns lines to top (adds extra lines to bottom as required).

        Args:
            lines (List[List[Segment]]): A list of lines.
            width (int): Desired width.
            height (int, optional): Desired height or None for no change.
            style (Style): Style of any padding added.
            new_lines (bool, optional): Padded lines should include "\n". Defaults to False.

        Returns:
            List[List[Segment]]: New list of lines.
        """
        extra_lines = height - len(lines)
        if not extra_lines:
            return lines[:]
        lines = lines[:height]
        blank = cls(" " * width + "\n", style) if new_lines else cls(" " * width, style)
        lines = lines + [[blank]] * extra_lines
        return lines

    @classmethod
    def align_bottom(
        cls: Type["Segment"],
        lines: List[List["Segment"]],
        width: int,
        height: int,
        style: Style,
        new_lines: bool = False,
    ) -> List[List["Segment"]]:
        """Aligns render to bottom (adds extra lines above as required).

        Args:
            lines (List[List[Segment]]): A list of lines.
            width (int): Desired width.
            height (int, optional): Desired height or None for no change.
            style (Style): Style of any padding added. Defaults to None.
            new_lines (bool, optional): Padded lines should include "\n". Defaults to False.

        Returns:
            List[List[Segment]]: New list of lines.
        """
        extra_lines = height - len(lines)
        if not extra_lines:
            return lines[:]
        lines = lines[:height]
        blank = cls(" " * width + "\n", style) if new_lines else cls(" " * width, style)
        lines = [[blank]] * extra_lines + lines
        return lines

    @classmethod
    def align_middle(
        cls: Type["Segment"],
        lines: List[List["Segment"]],
        width: int,
        height: int,
        style: Style,
        new_lines: bool = False,
    ) -> List[List["Segment"]]:
        """Aligns lines to middle (adds extra lines to above and below as required).

        Args:
            lines (List[List[Segment]]): A list of lines.
            width (int): Desired width.
            height (int, optional): Desired height or None for no change.
            style (Style): Style of any padding added.
            new_lines (bool, optional): Padded lines should include "\n". Defaults to False.

        Returns:
            List[List[Segment]]: New list of lines.
        """
        extra_lines = height - len(lines)
        if not extra_lines:
            return lines[:]
        lines = lines[:height]
        blank = cls(" " * width + "\n", style) if new_lines else cls(" " * width, style)
        top_lines = extra_lines // 2
        bottom_lines = extra_lines - top_lines
        lines = [[blank]] * top_lines + lines + [[blank]] * bottom_lines
        return lines

    @classmethod
    def simplify(cls, segments: Iterable["Segment"]) -> Iterable["Segment"]:
        """Simplify an iterable of segments by combining contiguous segments with the same style.

        Args:
            segments (Iterable[Segment]): An iterable of segments.

        Returns:
            Iterable[Segment]: A possibly smaller iterable of segments that will render the same way.
        """
        iter_segments = iter(segments)
        try:
            last_segment = next(iter_segments)
        except StopIteration:
            return

        _Segment = Segment
        for segment in iter_segments:
            if last_segment.style == segment.style and not segment.control:
                last_segment = _Segment(
                    last_segment.text + segment.text, last_segment.style
                )
            else:
                yield last_segment
                last_segment = segment
        yield last_segment

    @classmethod
    def strip_links(cls, segments: Iterable["Segment"]) -> Iterable["Segment"]:
        """Remove all links from an iterable of styles.

        Args:
            segments (Iterable[Segment]): An iterable segments.

        Yields:
            Segment: Segments with link removed.
        """
        for segment in segments:
            if segment.control or segment.style is None:
                yield segment
            else:
                text, style, _control = segment
                yield cls(text, style.update_link(None) if style else None)

    @classmethod
    def strip_styles(cls, segments: Iterable["Segment"]) -> Iterable["Segment"]:
        """Remove all styles from an iterable of segments.

        Args:
            segments (Iterable[Segment]): An iterable segments.

        Yields:
            Segment: Segments with styles replace with None
        """
        for text, _style, control in segments:
            yield cls(text, None, control)

    @classmethod
    def remove_color(cls, segments: Iterable["Segment"]) -> Iterable["Segment"]:
        """Remove all color from an iterable of segments.

        Args:
            segments (Iterable[Segment]): An iterable segments.

        Yields:
            Segment: Segments with colorless style.
        """

        cache: Dict[Style, Style] = {}
        for text, style, control in segments:
            if style:
                colorless_style = cache.get(style)
                if colorless_style is None:
                    colorless_style = style.without_color
                    cache[style] = colorless_style
                yield cls(text, colorless_style, control)
            else:
                yield cls(text, None, control)

    @classmethod
    def divide(
        cls, segments: Iterable["Segment"], cuts: Iterable[int]
    ) -> Iterable[List["Segment"]]:
        """Divides an iterable of segments in to portions.

        Args:
            cuts (Iterable[int]): Cell positions where to divide.

        Yields:
            [Iterable[List[Segment]]]: An iterable of Segments in List.
        """
        split_segments: List["Segment"] = []
        add_segment = split_segments.append

        iter_cuts = iter(cuts)

        while True:
            cut = next(iter_cuts, -1)
            if cut == -1:
                return
            if cut != 0:
                break
            yield []
        pos = 0

        segments_clear = split_segments.clear
        segments_copy = split_segments.copy

        _cell_len = cached_cell_len
        for segment in segments:
            text, _style, control = segment
            while text:
                end_pos = pos if control else pos + _cell_len(text)
                if end_pos < cut:
                    add_segment(segment)
                    pos = end_pos
                    break

                if end_pos == cut:
                    add_segment(segment)
                    yield segments_copy()
                    segments_clear()
                    pos = end_pos

                    cut = next(iter_cuts, -1)
                    if cut == -1:
                        if split_segments:
                            yield segments_copy()
                        return

                    break

                else:
                    before, segment = segment.split_cells(cut - pos)
                    text, _style, control = segment
                    add_segment(before)
                    yield segments_copy()
                    segments_clear()
                    pos = cut

                cut = next(iter_cuts, -1)
                if cut == -1:
                    if split_segments:
                        yield segments_copy()
                    return

        yield segments_copy()


class Segments:
    """A simple renderable to render an iterable of segments. This class may be useful if
    you want to print segments outside of a __rich_console__ method.

    Args:
        segments (Iterable[Segment]): An iterable of segments.
        new_lines (bool, optional): Add new lines between segments. Defaults to False.
    """

    def __init__(self, segments: Iterable[Segment], new_lines: bool = False) -> None:
        self.segments = list(segments)
        self.new_lines = new_lines

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> "RenderResult":
        if self.new_lines:
            line = Segment.line()
            for segment in self.segments:
                yield segment
                yield line
        else:
            yield from self.segments


class SegmentLines:
    def __init__(self, lines: Iterable[List[Segment]], new_lines: bool = False) -> None:
        """A simple renderable containing a number of lines of segments. May be used as an intermediate
        in rendering process.

        Args:
            lines (Iterable[List[Segment]]): Lists of segments forming lines.
            new_lines (bool, optional): Insert new lines after each line. Defaults to False.
        """
        self.lines = list(lines)
        self.new_lines = new_lines

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> "RenderResult":
        if self.new_lines:
            new_line = Segment.line()
            for line in self.lines:
                yield from line
                yield new_line
        else:
            for line in self.lines:
                yield from line


if __name__ == "__main__":  # pragma: no cover
    from pip._vendor.rich.console import Console
    from pip._vendor.rich.syntax import Syntax
    from pip._vendor.rich.text import Text

    code = """from rich.console import Console
console = Console()
text = Text.from_markup("Hello, [bold magenta]World[/]!")
console.print(text)"""

    text = Text.from_markup("Hello, [bold magenta]World[/]!")

    console = Console()

    console.rule("rich.Segment")
    console.print(
        "A Segment is the last step in the Rich render process before generating text with ANSI codes."
    )
    console.print("\nConsider the following code:\n")
    console.print(Syntax(code, "python", line_numbers=True))
    console.print()
    console.print(
        "When you call [b]print()[/b], Rich [i]renders[/i] the object in to the following:\n"
    )
    fragments = list(console.render(text))
    console.print(fragments)
    console.print()
    console.print("The Segments are then processed to produce the following output:\n")
    console.print(text)
    console.print(
        "\nYou will only need to know this if you are implementing your own Rich renderables."
    )

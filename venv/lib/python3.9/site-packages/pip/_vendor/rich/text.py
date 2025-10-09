import re
from functools import partial, reduce
from math import gcd
from operator import itemgetter
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Pattern,
    Tuple,
    Union,
)

from ._loop import loop_last
from ._pick import pick_bool
from ._wrap import divide_line
from .align import AlignMethod
from .cells import cell_len, set_cell_size
from .containers import Lines
from .control import strip_control_codes
from .emoji import EmojiVariant
from .jupyter import JupyterMixin
from .measure import Measurement
from .segment import Segment
from .style import Style, StyleType

if TYPE_CHECKING:  # pragma: no cover
    from .console import Console, ConsoleOptions, JustifyMethod, OverflowMethod

DEFAULT_JUSTIFY: "JustifyMethod" = "default"
DEFAULT_OVERFLOW: "OverflowMethod" = "fold"


_re_whitespace = re.compile(r"\s+$")

TextType = Union[str, "Text"]
"""A plain string or a :class:`Text` instance."""

GetStyleCallable = Callable[[str], Optional[StyleType]]


class Span(NamedTuple):
    """A marked up region in some text."""

    start: int
    """Span start index."""
    end: int
    """Span end index."""
    style: Union[str, Style]
    """Style associated with the span."""

    def __repr__(self) -> str:
        return f"Span({self.start}, {self.end}, {self.style!r})"

    def __bool__(self) -> bool:
        return self.end > self.start

    def split(self, offset: int) -> Tuple["Span", Optional["Span"]]:
        """Split a span in to 2 from a given offset."""

        if offset < self.start:
            return self, None
        if offset >= self.end:
            return self, None

        start, end, style = self
        span1 = Span(start, min(end, offset), style)
        span2 = Span(span1.end, end, style)
        return span1, span2

    def move(self, offset: int) -> "Span":
        """Move start and end by a given offset.

        Args:
            offset (int): Number of characters to add to start and end.

        Returns:
            TextSpan: A new TextSpan with adjusted position.
        """
        start, end, style = self
        return Span(start + offset, end + offset, style)

    def right_crop(self, offset: int) -> "Span":
        """Crop the span at the given offset.

        Args:
            offset (int): A value between start and end.

        Returns:
            Span: A new (possibly smaller) span.
        """
        start, end, style = self
        if offset >= end:
            return self
        return Span(start, min(offset, end), style)

    def extend(self, cells: int) -> "Span":
        """Extend the span by the given number of cells.

        Args:
            cells (int): Additional space to add to end of span.

        Returns:
            Span: A span.
        """
        if cells:
            start, end, style = self
            return Span(start, end + cells, style)
        else:
            return self


class Text(JupyterMixin):
    """Text with color / style.

    Args:
        text (str, optional): Default unstyled text. Defaults to "".
        style (Union[str, Style], optional): Base style for text. Defaults to "".
        justify (str, optional): Justify method: "left", "center", "full", "right". Defaults to None.
        overflow (str, optional): Overflow method: "crop", "fold", "ellipsis". Defaults to None.
        no_wrap (bool, optional): Disable text wrapping, or None for default. Defaults to None.
        end (str, optional): Character to end text with. Defaults to "\\\\n".
        tab_size (int): Number of spaces per tab, or ``None`` to use ``console.tab_size``. Defaults to None.
        spans (List[Span], optional). A list of predefined style spans. Defaults to None.
    """

    __slots__ = [
        "_text",
        "style",
        "justify",
        "overflow",
        "no_wrap",
        "end",
        "tab_size",
        "_spans",
        "_length",
    ]

    def __init__(
        self,
        text: str = "",
        style: Union[str, Style] = "",
        *,
        justify: Optional["JustifyMethod"] = None,
        overflow: Optional["OverflowMethod"] = None,
        no_wrap: Optional[bool] = None,
        end: str = "\n",
        tab_size: Optional[int] = None,
        spans: Optional[List[Span]] = None,
    ) -> None:
        sanitized_text = strip_control_codes(text)
        self._text = [sanitized_text]
        self.style = style
        self.justify: Optional["JustifyMethod"] = justify
        self.overflow: Optional["OverflowMethod"] = overflow
        self.no_wrap = no_wrap
        self.end = end
        self.tab_size = tab_size
        self._spans: List[Span] = spans or []
        self._length: int = len(sanitized_text)

    def __len__(self) -> int:
        return self._length

    def __bool__(self) -> bool:
        return bool(self._length)

    def __str__(self) -> str:
        return self.plain

    def __repr__(self) -> str:
        return f"<text {self.plain!r} {self._spans!r} {self.style!r}>"

    def __add__(self, other: Any) -> "Text":
        if isinstance(other, (str, Text)):
            result = self.copy()
            result.append(other)
            return result
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Text):
            return NotImplemented
        return self.plain == other.plain and self._spans == other._spans

    def __contains__(self, other: object) -> bool:
        if isinstance(other, str):
            return other in self.plain
        elif isinstance(other, Text):
            return other.plain in self.plain
        return False

    def __getitem__(self, slice: Union[int, slice]) -> "Text":
        def get_text_at(offset: int) -> "Text":
            _Span = Span
            text = Text(
                self.plain[offset],
                spans=[
                    _Span(0, 1, style)
                    for start, end, style in self._spans
                    if end > offset >= start
                ],
                end="",
            )
            return text

        if isinstance(slice, int):
            return get_text_at(slice)
        else:
            start, stop, step = slice.indices(len(self.plain))
            if step == 1:
                lines = self.divide([start, stop])
                return lines[1]
            else:
                # This would be a bit of work to implement efficiently
                # For now, its not required
                raise TypeError("slices with step!=1 are not supported")

    @property
    def cell_len(self) -> int:
        """Get the number of cells required to render this text."""
        return cell_len(self.plain)

    @property
    def markup(self) -> str:
        """Get console markup to render this Text.

        Returns:
            str: A string potentially creating markup tags.
        """
        from .markup import escape

        output: List[str] = []

        plain = self.plain
        markup_spans = [
            (0, False, self.style),
            *((span.start, False, span.style) for span in self._spans),
            *((span.end, True, span.style) for span in self._spans),
            (len(plain), True, self.style),
        ]
        markup_spans.sort(key=itemgetter(0, 1))
        position = 0
        append = output.append
        for offset, closing, style in markup_spans:
            if offset > position:
                append(escape(plain[position:offset]))
                position = offset
            if style:
                append(f"[/{style}]" if closing else f"[{style}]")
        markup = "".join(output)
        return markup

    @classmethod
    def from_markup(
        cls,
        text: str,
        *,
        style: Union[str, Style] = "",
        emoji: bool = True,
        emoji_variant: Optional[EmojiVariant] = None,
        justify: Optional["JustifyMethod"] = None,
        overflow: Optional["OverflowMethod"] = None,
        end: str = "\n",
    ) -> "Text":
        """Create Text instance from markup.

        Args:
            text (str): A string containing console markup.
            style (Union[str, Style], optional): Base style for text. Defaults to "".
            emoji (bool, optional): Also render emoji code. Defaults to True.
            emoji_variant (str, optional): Optional emoji variant, either "text" or "emoji". Defaults to None.
            justify (str, optional): Justify method: "left", "center", "full", "right". Defaults to None.
            overflow (str, optional): Overflow method: "crop", "fold", "ellipsis". Defaults to None.
            end (str, optional): Character to end text with. Defaults to "\\\\n".

        Returns:
            Text: A Text instance with markup rendered.
        """
        from .markup import render

        rendered_text = render(text, style, emoji=emoji, emoji_variant=emoji_variant)
        rendered_text.justify = justify
        rendered_text.overflow = overflow
        rendered_text.end = end
        return rendered_text

    @classmethod
    def from_ansi(
        cls,
        text: str,
        *,
        style: Union[str, Style] = "",
        justify: Optional["JustifyMethod"] = None,
        overflow: Optional["OverflowMethod"] = None,
        no_wrap: Optional[bool] = None,
        end: str = "\n",
        tab_size: Optional[int] = 8,
    ) -> "Text":
        """Create a Text object from a string containing ANSI escape codes.

        Args:
            text (str): A string containing escape codes.
            style (Union[str, Style], optional): Base style for text. Defaults to "".
            justify (str, optional): Justify method: "left", "center", "full", "right". Defaults to None.
            overflow (str, optional): Overflow method: "crop", "fold", "ellipsis". Defaults to None.
            no_wrap (bool, optional): Disable text wrapping, or None for default. Defaults to None.
            end (str, optional): Character to end text with. Defaults to "\\\\n".
            tab_size (int): Number of spaces per tab, or ``None`` to use ``console.tab_size``. Defaults to None.
        """
        from .ansi import AnsiDecoder

        joiner = Text(
            "\n",
            justify=justify,
            overflow=overflow,
            no_wrap=no_wrap,
            end=end,
            tab_size=tab_size,
            style=style,
        )
        decoder = AnsiDecoder()
        result = joiner.join(line for line in decoder.decode(text))
        return result

    @classmethod
    def styled(
        cls,
        text: str,
        style: StyleType = "",
        *,
        justify: Optional["JustifyMethod"] = None,
        overflow: Optional["OverflowMethod"] = None,
    ) -> "Text":
        """Construct a Text instance with a pre-applied styled. A style applied in this way won't be used
        to pad the text when it is justified.

        Args:
            text (str): A string containing console markup.
            style (Union[str, Style]): Style to apply to the text. Defaults to "".
            justify (str, optional): Justify method: "left", "center", "full", "right". Defaults to None.
            overflow (str, optional): Overflow method: "crop", "fold", "ellipsis". Defaults to None.

        Returns:
            Text: A text instance with a style applied to the entire string.
        """
        styled_text = cls(text, justify=justify, overflow=overflow)
        styled_text.stylize(style)
        return styled_text

    @classmethod
    def assemble(
        cls,
        *parts: Union[str, "Text", Tuple[str, StyleType]],
        style: Union[str, Style] = "",
        justify: Optional["JustifyMethod"] = None,
        overflow: Optional["OverflowMethod"] = None,
        no_wrap: Optional[bool] = None,
        end: str = "\n",
        tab_size: int = 8,
        meta: Optional[Dict[str, Any]] = None,
    ) -> "Text":
        """Construct a text instance by combining a sequence of strings with optional styles.
        The positional arguments should be either strings, or a tuple of string + style.

        Args:
            style (Union[str, Style], optional): Base style for text. Defaults to "".
            justify (str, optional): Justify method: "left", "center", "full", "right". Defaults to None.
            overflow (str, optional): Overflow method: "crop", "fold", "ellipsis". Defaults to None.
            no_wrap (bool, optional): Disable text wrapping, or None for default. Defaults to None.
            end (str, optional): Character to end text with. Defaults to "\\\\n".
            tab_size (int): Number of spaces per tab, or ``None`` to use ``console.tab_size``. Defaults to None.
            meta (Dict[str, Any], optional). Meta data to apply to text, or None for no meta data. Default to None

        Returns:
            Text: A new text instance.
        """
        text = cls(
            style=style,
            justify=justify,
            overflow=overflow,
            no_wrap=no_wrap,
            end=end,
            tab_size=tab_size,
        )
        append = text.append
        _Text = Text
        for part in parts:
            if isinstance(part, (_Text, str)):
                append(part)
            else:
                append(*part)
        if meta:
            text.apply_meta(meta)
        return text

    @property
    def plain(self) -> str:
        """Get the text as a single string."""
        if len(self._text) != 1:
            self._text[:] = ["".join(self._text)]
        return self._text[0]

    @plain.setter
    def plain(self, new_text: str) -> None:
        """Set the text to a new value."""
        if new_text != self.plain:
            sanitized_text = strip_control_codes(new_text)
            self._text[:] = [sanitized_text]
            old_length = self._length
            self._length = len(sanitized_text)
            if old_length > self._length:
                self._trim_spans()

    @property
    def spans(self) -> List[Span]:
        """Get a reference to the internal list of spans."""
        return self._spans

    @spans.setter
    def spans(self, spans: List[Span]) -> None:
        """Set spans."""
        self._spans = spans[:]

    def blank_copy(self, plain: str = "") -> "Text":
        """Return a new Text instance with copied metadata (but not the string or spans)."""
        copy_self = Text(
            plain,
            style=self.style,
            justify=self.justify,
            overflow=self.overflow,
            no_wrap=self.no_wrap,
            end=self.end,
            tab_size=self.tab_size,
        )
        return copy_self

    def copy(self) -> "Text":
        """Return a copy of this instance."""
        copy_self = Text(
            self.plain,
            style=self.style,
            justify=self.justify,
            overflow=self.overflow,
            no_wrap=self.no_wrap,
            end=self.end,
            tab_size=self.tab_size,
        )
        copy_self._spans[:] = self._spans
        return copy_self

    def stylize(
        self,
        style: Union[str, Style],
        start: int = 0,
        end: Optional[int] = None,
    ) -> None:
        """Apply a style to the text, or a portion of the text.

        Args:
            style (Union[str, Style]): Style instance or style definition to apply.
            start (int): Start offset (negative indexing is supported). Defaults to 0.
            end (Optional[int], optional): End offset (negative indexing is supported), or None for end of text. Defaults to None.
        """
        if style:
            length = len(self)
            if start < 0:
                start = length + start
            if end is None:
                end = length
            if end < 0:
                end = length + end
            if start >= length or end <= start:
                # Span not in text or not valid
                return
            self._spans.append(Span(start, min(length, end), style))

    def stylize_before(
        self,
        style: Union[str, Style],
        start: int = 0,
        end: Optional[int] = None,
    ) -> None:
        """Apply a style to the text, or a portion of the text. Styles will be applied before other styles already present.

        Args:
            style (Union[str, Style]): Style instance or style definition to apply.
            start (int): Start offset (negative indexing is supported). Defaults to 0.
            end (Optional[int], optional): End offset (negative indexing is supported), or None for end of text. Defaults to None.
        """
        if style:
            length = len(self)
            if start < 0:
                start = length + start
            if end is None:
                end = length
            if end < 0:
                end = length + end
            if start >= length or end <= start:
                # Span not in text or not valid
                return
            self._spans.insert(0, Span(start, min(length, end), style))

    def apply_meta(
        self, meta: Dict[str, Any], start: int = 0, end: Optional[int] = None
    ) -> None:
        """Apply metadata to the text, or a portion of the text.

        Args:
            meta (Dict[str, Any]): A dict of meta information.
            start (int): Start offset (negative indexing is supported). Defaults to 0.
            end (Optional[int], optional): End offset (negative indexing is supported), or None for end of text. Defaults to None.

        """
        style = Style.from_meta(meta)
        self.stylize(style, start=start, end=end)

    def on(self, meta: Optional[Dict[str, Any]] = None, **handlers: Any) -> "Text":
        """Apply event handlers (used by Textual project).

        Example:
            >>> from rich.text import Text
            >>> text = Text("hello world")
            >>> text.on(click="view.toggle('world')")

        Args:
            meta (Dict[str, Any]): Mapping of meta information.
            **handlers: Keyword args are prefixed with "@" to defined handlers.

        Returns:
            Text: Self is returned to method may be chained.
        """
        meta = {} if meta is None else meta
        meta.update({f"@{key}": value for key, value in handlers.items()})
        self.stylize(Style.from_meta(meta))
        return self

    def remove_suffix(self, suffix: str) -> None:
        """Remove a suffix if it exists.

        Args:
            suffix (str): Suffix to remove.
        """
        if self.plain.endswith(suffix):
            self.right_crop(len(suffix))

    def get_style_at_offset(self, console: "Console", offset: int) -> Style:
        """Get the style of a character at give offset.

        Args:
            console (~Console): Console where text will be rendered.
            offset (int): Offset in to text (negative indexing supported)

        Returns:
            Style: A Style instance.
        """
        # TODO: This is a little inefficient, it is only used by full justify
        if offset < 0:
            offset = len(self) + offset
        get_style = console.get_style
        style = get_style(self.style).copy()
        for start, end, span_style in self._spans:
            if end > offset >= start:
                style += get_style(span_style, default="")
        return style

    def extend_style(self, spaces: int) -> None:
        """Extend the Text given number of spaces where the spaces have the same style as the last character.

        Args:
            spaces (int): Number of spaces to add to the Text.
        """
        if spaces <= 0:
            return
        spans = self.spans
        new_spaces = " " * spaces
        if spans:
            end_offset = len(self)
            self._spans[:] = [
                span.extend(spaces) if span.end >= end_offset else span
                for span in spans
            ]
            self._text.append(new_spaces)
            self._length += spaces
        else:
            self.plain += new_spaces

    def highlight_regex(
        self,
        re_highlight: Union[Pattern[str], str],
        style: Optional[Union[GetStyleCallable, StyleType]] = None,
        *,
        style_prefix: str = "",
    ) -> int:
        """Highlight text with a regular expression, where group names are
        translated to styles.

        Args:
            re_highlight (Union[re.Pattern, str]): A regular expression object or string.
            style (Union[GetStyleCallable, StyleType]): Optional style to apply to whole match, or a callable
                which accepts the matched text and returns a style. Defaults to None.
            style_prefix (str, optional): Optional prefix to add to style group names.

        Returns:
            int: Number of regex matches
        """
        count = 0
        append_span = self._spans.append
        _Span = Span
        plain = self.plain
        if isinstance(re_highlight, str):
            re_highlight = re.compile(re_highlight)
        for match in re_highlight.finditer(plain):
            get_span = match.span
            if style:
                start, end = get_span()
                match_style = style(plain[start:end]) if callable(style) else style
                if match_style is not None and end > start:
                    append_span(_Span(start, end, match_style))

            count += 1
            for name in match.groupdict().keys():
                start, end = get_span(name)
                if start != -1 and end > start:
                    append_span(_Span(start, end, f"{style_prefix}{name}"))
        return count

    def highlight_words(
        self,
        words: Iterable[str],
        style: Union[str, Style],
        *,
        case_sensitive: bool = True,
    ) -> int:
        """Highlight words with a style.

        Args:
            words (Iterable[str]): Words to highlight.
            style (Union[str, Style]): Style to apply.
            case_sensitive (bool, optional): Enable case sensitive matching. Defaults to True.

        Returns:
            int: Number of words highlighted.
        """
        re_words = "|".join(re.escape(word) for word in words)
        add_span = self._spans.append
        count = 0
        _Span = Span
        for match in re.finditer(
            re_words, self.plain, flags=0 if case_sensitive else re.IGNORECASE
        ):
            start, end = match.span(0)
            add_span(_Span(start, end, style))
            count += 1
        return count

    def rstrip(self) -> None:
        """Strip whitespace from end of text."""
        self.plain = self.plain.rstrip()

    def rstrip_end(self, size: int) -> None:
        """Remove whitespace beyond a certain width at the end of the text.

        Args:
            size (int): The desired size of the text.
        """
        text_length = len(self)
        if text_length > size:
            excess = text_length - size
            whitespace_match = _re_whitespace.search(self.plain)
            if whitespace_match is not None:
                whitespace_count = len(whitespace_match.group(0))
                self.right_crop(min(whitespace_count, excess))

    def set_length(self, new_length: int) -> None:
        """Set new length of the text, clipping or padding is required."""
        length = len(self)
        if length != new_length:
            if length < new_length:
                self.pad_right(new_length - length)
            else:
                self.right_crop(length - new_length)

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> Iterable[Segment]:
        tab_size: int = console.tab_size if self.tab_size is None else self.tab_size
        justify = self.justify or options.justify or DEFAULT_JUSTIFY

        overflow = self.overflow or options.overflow or DEFAULT_OVERFLOW

        lines = self.wrap(
            console,
            options.max_width,
            justify=justify,
            overflow=overflow,
            tab_size=tab_size or 8,
            no_wrap=pick_bool(self.no_wrap, options.no_wrap, False),
        )
        all_lines = Text("\n").join(lines)
        yield from all_lines.render(console, end=self.end)

    def __rich_measure__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> Measurement:
        text = self.plain
        lines = text.splitlines()
        max_text_width = max(cell_len(line) for line in lines) if lines else 0
        words = text.split()
        min_text_width = (
            max(cell_len(word) for word in words) if words else max_text_width
        )
        return Measurement(min_text_width, max_text_width)

    def render(self, console: "Console", end: str = "") -> Iterable["Segment"]:
        """Render the text as Segments.

        Args:
            console (Console): Console instance.
            end (Optional[str], optional): Optional end character.

        Returns:
            Iterable[Segment]: Result of render that may be written to the console.
        """
        _Segment = Segment
        text = self.plain
        if not self._spans:
            yield Segment(text)
            if end:
                yield _Segment(end)
            return
        get_style = partial(console.get_style, default=Style.null())

        enumerated_spans = list(enumerate(self._spans, 1))
        style_map = {index: get_style(span.style) for index, span in enumerated_spans}
        style_map[0] = get_style(self.style)

        spans = [
            (0, False, 0),
            *((span.start, False, index) for index, span in enumerated_spans),
            *((span.end, True, index) for index, span in enumerated_spans),
            (len(text), True, 0),
        ]
        spans.sort(key=itemgetter(0, 1))

        stack: List[int] = []
        stack_append = stack.append
        stack_pop = stack.remove

        style_cache: Dict[Tuple[Style, ...], Style] = {}
        style_cache_get = style_cache.get
        combine = Style.combine

        def get_current_style() -> Style:
            """Construct current style from stack."""
            styles = tuple(style_map[_style_id] for _style_id in sorted(stack))
            cached_style = style_cache_get(styles)
            if cached_style is not None:
                return cached_style
            current_style = combine(styles)
            style_cache[styles] = current_style
            return current_style

        for (offset, leaving, style_id), (next_offset, _, _) in zip(spans, spans[1:]):
            if leaving:
                stack_pop(style_id)
            else:
                stack_append(style_id)
            if next_offset > offset:
                yield _Segment(text[offset:next_offset], get_current_style())
        if end:
            yield _Segment(end)

    def join(self, lines: Iterable["Text"]) -> "Text":
        """Join text together with this instance as the separator.

        Args:
            lines (Iterable[Text]): An iterable of Text instances to join.

        Returns:
            Text: A new text instance containing join text.
        """

        new_text = self.blank_copy()

        def iter_text() -> Iterable["Text"]:
            if self.plain:
                for last, line in loop_last(lines):
                    yield line
                    if not last:
                        yield self
            else:
                yield from lines

        extend_text = new_text._text.extend
        append_span = new_text._spans.append
        extend_spans = new_text._spans.extend
        offset = 0
        _Span = Span

        for text in iter_text():
            extend_text(text._text)
            if text.style:
                append_span(_Span(offset, offset + len(text), text.style))
            extend_spans(
                _Span(offset + start, offset + end, style)
                for start, end, style in text._spans
            )
            offset += len(text)
        new_text._length = offset
        return new_text

    def expand_tabs(self, tab_size: Optional[int] = None) -> None:
        """Converts tabs to spaces.

        Args:
            tab_size (int, optional): Size of tabs. Defaults to 8.

        """
        if "\t" not in self.plain:
            return
        if tab_size is None:
            tab_size = self.tab_size
        if tab_size is None:
            tab_size = 8

        new_text: List[Text] = []
        append = new_text.append

        for line in self.split("\n", include_separator=True):
            if "\t" not in line.plain:
                append(line)
            else:
                cell_position = 0
                parts = line.split("\t", include_separator=True)
                for part in parts:
                    if part.plain.endswith("\t"):
                        part._text[-1] = part._text[-1][:-1] + " "
                        cell_position += part.cell_len
                        tab_remainder = cell_position % tab_size
                        if tab_remainder:
                            spaces = tab_size - tab_remainder
                            part.extend_style(spaces)
                            cell_position += spaces
                    else:
                        cell_position += part.cell_len
                    append(part)

        result = Text("").join(new_text)

        self._text = [result.plain]
        self._length = len(self.plain)
        self._spans[:] = result._spans

    def truncate(
        self,
        max_width: int,
        *,
        overflow: Optional["OverflowMethod"] = None,
        pad: bool = False,
    ) -> None:
        """Truncate text if it is longer that a given width.

        Args:
            max_width (int): Maximum number of characters in text.
            overflow (str, optional): Overflow method: "crop", "fold", or "ellipsis". Defaults to None, to use self.overflow.
            pad (bool, optional): Pad with spaces if the length is less than max_width. Defaults to False.
        """
        _overflow = overflow or self.overflow or DEFAULT_OVERFLOW
        if _overflow != "ignore":
            length = cell_len(self.plain)
            if length > max_width:
                if _overflow == "ellipsis":
                    self.plain = set_cell_size(self.plain, max_width - 1) + "…"
                else:
                    self.plain = set_cell_size(self.plain, max_width)
            if pad and length < max_width:
                spaces = max_width - length
                self._text = [f"{self.plain}{' ' * spaces}"]
                self._length = len(self.plain)

    def _trim_spans(self) -> None:
        """Remove or modify any spans that are over the end of the text."""
        max_offset = len(self.plain)
        _Span = Span
        self._spans[:] = [
            (
                span
                if span.end < max_offset
                else _Span(span.start, min(max_offset, span.end), span.style)
            )
            for span in self._spans
            if span.start < max_offset
        ]

    def pad(self, count: int, character: str = " ") -> None:
        """Pad left and right with a given number of characters.

        Args:
            count (int): Width of padding.
            character (str): The character to pad with. Must be a string of length 1.
        """
        assert len(character) == 1, "Character must be a string of length 1"
        if count:
            pad_characters = character * count
            self.plain = f"{pad_characters}{self.plain}{pad_characters}"
            _Span = Span
            self._spans[:] = [
                _Span(start + count, end + count, style)
                for start, end, style in self._spans
            ]

    def pad_left(self, count: int, character: str = " ") -> None:
        """Pad the left with a given character.

        Args:
            count (int): Number of characters to pad.
            character (str, optional): Character to pad with. Defaults to " ".
        """
        assert len(character) == 1, "Character must be a string of length 1"
        if count:
            self.plain = f"{character * count}{self.plain}"
            _Span = Span
            self._spans[:] = [
                _Span(start + count, end + count, style)
                for start, end, style in self._spans
            ]

    def pad_right(self, count: int, character: str = " ") -> None:
        """Pad the right with a given character.

        Args:
            count (int): Number of characters to pad.
            character (str, optional): Character to pad with. Defaults to " ".
        """
        assert len(character) == 1, "Character must be a string of length 1"
        if count:
            self.plain = f"{self.plain}{character * count}"

    def align(self, align: AlignMethod, width: int, character: str = " ") -> None:
        """Align text to a given width.

        Args:
            align (AlignMethod): One of "left", "center", or "right".
            width (int): Desired width.
            character (str, optional): Character to pad with. Defaults to " ".
        """
        self.truncate(width)
        excess_space = width - cell_len(self.plain)
        if excess_space:
            if align == "left":
                self.pad_right(excess_space, character)
            elif align == "center":
                left = excess_space // 2
                self.pad_left(left, character)
                self.pad_right(excess_space - left, character)
            else:
                self.pad_left(excess_space, character)

    def append(
        self, text: Union["Text", str], style: Optional[Union[str, "Style"]] = None
    ) -> "Text":
        """Add text with an optional style.

        Args:
            text (Union[Text, str]): A str or Text to append.
            style (str, optional): A style name. Defaults to None.

        Returns:
            Text: Returns self for chaining.
        """

        if not isinstance(text, (str, Text)):
            raise TypeError("Only str or Text can be appended to Text")

        if len(text):
            if isinstance(text, str):
                sanitized_text = strip_control_codes(text)
                self._text.append(sanitized_text)
                offset = len(self)
                text_length = len(sanitized_text)
                if style:
                    self._spans.append(Span(offset, offset + text_length, style))
                self._length += text_length
            elif isinstance(text, Text):
                _Span = Span
                if style is not None:
                    raise ValueError(
                        "style must not be set when appending Text instance"
                    )
                text_length = self._length
                if text.style:
                    self._spans.append(
                        _Span(text_length, text_length + len(text), text.style)
                    )
                self._text.append(text.plain)
                self._spans.extend(
                    _Span(start + text_length, end + text_length, style)
                    for start, end, style in text._spans.copy()
                )
                self._length += len(text)
        return self

    def append_text(self, text: "Text") -> "Text":
        """Append another Text instance. This method is more performant that Text.append, but
        only works for Text.

        Args:
            text (Text): The Text instance to append to this instance.

        Returns:
            Text: Returns self for chaining.
        """
        _Span = Span
        text_length = self._length
        if text.style:
            self._spans.append(_Span(text_length, text_length + len(text), text.style))
        self._text.append(text.plain)
        self._spans.extend(
            _Span(start + text_length, end + text_length, style)
            for start, end, style in text._spans.copy()
        )
        self._length += len(text)
        return self

    def append_tokens(
        self, tokens: Iterable[Tuple[str, Optional[StyleType]]]
    ) -> "Text":
        """Append iterable of str and style. Style may be a Style instance or a str style definition.

        Args:
            tokens (Iterable[Tuple[str, Optional[StyleType]]]): An iterable of tuples containing str content and style.

        Returns:
            Text: Returns self for chaining.
        """
        append_text = self._text.append
        append_span = self._spans.append
        _Span = Span
        offset = len(self)
        for content, style in tokens:
            content = strip_control_codes(content)
            append_text(content)
            if style:
                append_span(_Span(offset, offset + len(content), style))
            offset += len(content)
        self._length = offset
        return self

    def copy_styles(self, text: "Text") -> None:
        """Copy styles from another Text instance.

        Args:
            text (Text): A Text instance to copy styles from, must be the same length.
        """
        self._spans.extend(text._spans)

    def split(
        self,
        separator: str = "\n",
        *,
        include_separator: bool = False,
        allow_blank: bool = False,
    ) -> Lines:
        """Split rich text in to lines, preserving styles.

        Args:
            separator (str, optional): String to split on. Defaults to "\\\\n".
            include_separator (bool, optional): Include the separator in the lines. Defaults to False.
            allow_blank (bool, optional): Return a blank line if the text ends with a separator. Defaults to False.

        Returns:
            List[RichText]: A list of rich text, one per line of the original.
        """
        assert separator, "separator must not be empty"

        text = self.plain
        if separator not in text:
            return Lines([self.copy()])

        if include_separator:
            lines = self.divide(
                match.end() for match in re.finditer(re.escape(separator), text)
            )
        else:

            def flatten_spans() -> Iterable[int]:
                for match in re.finditer(re.escape(separator), text):
                    start, end = match.span()
                    yield start
                    yield end

            lines = Lines(
                line for line in self.divide(flatten_spans()) if line.plain != separator
            )

        if not allow_blank and text.endswith(separator):
            lines.pop()

        return lines

    def divide(self, offsets: Iterable[int]) -> Lines:
        """Divide text in to a number of lines at given offsets.

        Args:
            offsets (Iterable[int]): Offsets used to divide text.

        Returns:
            Lines: New RichText instances between offsets.
        """
        _offsets = list(offsets)

        if not _offsets:
            return Lines([self.copy()])

        text = self.plain
        text_length = len(text)
        divide_offsets = [0, *_offsets, text_length]
        line_ranges = list(zip(divide_offsets, divide_offsets[1:]))

        style = self.style
        justify = self.justify
        overflow = self.overflow
        _Text = Text
        new_lines = Lines(
            _Text(
                text[start:end],
                style=style,
                justify=justify,
                overflow=overflow,
            )
            for start, end in line_ranges
        )
        if not self._spans:
            return new_lines

        _line_appends = [line._spans.append for line in new_lines._lines]
        line_count = len(line_ranges)
        _Span = Span

        for span_start, span_end, style in self._spans:
            lower_bound = 0
            upper_bound = line_count
            start_line_no = (lower_bound + upper_bound) // 2

            while True:
                line_start, line_end = line_ranges[start_line_no]
                if span_start < line_start:
                    upper_bound = start_line_no - 1
                elif span_start > line_end:
                    lower_bound = start_line_no + 1
                else:
                    break
                start_line_no = (lower_bound + upper_bound) // 2

            if span_end < line_end:
                end_line_no = start_line_no
            else:
                end_line_no = lower_bound = start_line_no
                upper_bound = line_count

                while True:
                    line_start, line_end = line_ranges[end_line_no]
                    if span_end < line_start:
                        upper_bound = end_line_no - 1
                    elif span_end > line_end:
                        lower_bound = end_line_no + 1
                    else:
                        break
                    end_line_no = (lower_bound + upper_bound) // 2

            for line_no in range(start_line_no, end_line_no + 1):
                line_start, line_end = line_ranges[line_no]
                new_start = max(0, span_start - line_start)
                new_end = min(span_end - line_start, line_end - line_start)
                if new_end > new_start:
                    _line_appends[line_no](_Span(new_start, new_end, style))

        return new_lines

    def right_crop(self, amount: int = 1) -> None:
        """Remove a number of characters from the end of the text."""
        max_offset = len(self.plain) - amount
        _Span = Span
        self._spans[:] = [
            (
                span
                if span.end < max_offset
                else _Span(span.start, min(max_offset, span.end), span.style)
            )
            for span in self._spans
            if span.start < max_offset
        ]
        self._text = [self.plain[:-amount]]
        self._length -= amount

    def wrap(
        self,
        console: "Console",
        width: int,
        *,
        justify: Optional["JustifyMethod"] = None,
        overflow: Optional["OverflowMethod"] = None,
        tab_size: int = 8,
        no_wrap: Optional[bool] = None,
    ) -> Lines:
        """Word wrap the text.

        Args:
            console (Console): Console instance.
            width (int): Number of cells available per line.
            justify (str, optional): Justify method: "default", "left", "center", "full", "right". Defaults to "default".
            overflow (str, optional): Overflow method: "crop", "fold", or "ellipsis". Defaults to None.
            tab_size (int, optional): Default tab size. Defaults to 8.
            no_wrap (bool, optional): Disable wrapping, Defaults to False.

        Returns:
            Lines: Number of lines.
        """
        wrap_justify = justify or self.justify or DEFAULT_JUSTIFY
        wrap_overflow = overflow or self.overflow or DEFAULT_OVERFLOW

        no_wrap = pick_bool(no_wrap, self.no_wrap, False) or overflow == "ignore"

        lines = Lines()
        for line in self.split(allow_blank=True):
            if "\t" in line:
                line.expand_tabs(tab_size)
            if no_wrap:
                new_lines = Lines([line])
            else:
                offsets = divide_line(str(line), width, fold=wrap_overflow == "fold")
                new_lines = line.divide(offsets)
            for line in new_lines:
                line.rstrip_end(width)
            if wrap_justify:
                new_lines.justify(
                    console, width, justify=wrap_justify, overflow=wrap_overflow
                )
            for line in new_lines:
                line.truncate(width, overflow=wrap_overflow)
            lines.extend(new_lines)
        return lines

    def fit(self, width: int) -> Lines:
        """Fit the text in to given width by chopping in to lines.

        Args:
            width (int): Maximum characters in a line.

        Returns:
            Lines: Lines container.
        """
        lines: Lines = Lines()
        append = lines.append
        for line in self.split():
            line.set_length(width)
            append(line)
        return lines

    def detect_indentation(self) -> int:
        """Auto-detect indentation of code.

        Returns:
            int: Number of spaces used to indent code.
        """

        _indentations = {
            len(match.group(1))
            for match in re.finditer(r"^( *)(.*)$", self.plain, flags=re.MULTILINE)
        }

        try:
            indentation = (
                reduce(gcd, [indent for indent in _indentations if not indent % 2]) or 1
            )
        except TypeError:
            indentation = 1

        return indentation

    def with_indent_guides(
        self,
        indent_size: Optional[int] = None,
        *,
        character: str = "│",
        style: StyleType = "dim green",
    ) -> "Text":
        """Adds indent guide lines to text.

        Args:
            indent_size (Optional[int]): Size of indentation, or None to auto detect. Defaults to None.
            character (str, optional): Character to use for indentation. Defaults to "│".
            style (Union[Style, str], optional): Style of indent guides.

        Returns:
            Text: New text with indentation guides.
        """

        _indent_size = self.detect_indentation() if indent_size is None else indent_size

        text = self.copy()
        text.expand_tabs()
        indent_line = f"{character}{' ' * (_indent_size - 1)}"

        re_indent = re.compile(r"^( *)(.*)$")
        new_lines: List[Text] = []
        add_line = new_lines.append
        blank_lines = 0
        for line in text.split(allow_blank=True):
            match = re_indent.match(line.plain)
            if not match or not match.group(2):
                blank_lines += 1
                continue
            indent = match.group(1)
            full_indents, remaining_space = divmod(len(indent), _indent_size)
            new_indent = f"{indent_line * full_indents}{' ' * remaining_space}"
            line.plain = new_indent + line.plain[len(new_indent) :]
            line.stylize(style, 0, len(new_indent))
            if blank_lines:
                new_lines.extend([Text(new_indent, style=style)] * blank_lines)
                blank_lines = 0
            add_line(line)
        if blank_lines:
            new_lines.extend([Text("", style=style)] * blank_lines)

        new_text = text.blank_copy("\n").join(new_lines)
        return new_text


if __name__ == "__main__":  # pragma: no cover
    from pip._vendor.rich.console import Console

    text = Text(
        """\nLorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.\n"""
    )
    text.highlight_words(["Lorem"], "bold")
    text.highlight_words(["ipsum"], "italic")

    console = Console()

    console.rule("justify='left'")
    console.print(text, style="red")
    console.print()

    console.rule("justify='center'")
    console.print(text, style="green", justify="center")
    console.print()

    console.rule("justify='right'")
    console.print(text, style="blue", justify="right")
    console.print()

    console.rule("justify='full'")
    console.print(text, style="magenta", justify="full")
    console.print()

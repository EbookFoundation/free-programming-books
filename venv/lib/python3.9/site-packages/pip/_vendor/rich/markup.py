import re
from ast import literal_eval
from operator import attrgetter
from typing import Callable, Iterable, List, Match, NamedTuple, Optional, Tuple, Union

from ._emoji_replace import _emoji_replace
from .emoji import EmojiVariant
from .errors import MarkupError
from .style import Style
from .text import Span, Text

RE_TAGS = re.compile(
    r"""((\\*)\[([a-z#/@][^[]*?)])""",
    re.VERBOSE,
)

RE_HANDLER = re.compile(r"^([\w.]*?)(\(.*?\))?$")


class Tag(NamedTuple):
    """A tag in console markup."""

    name: str
    """The tag name. e.g. 'bold'."""
    parameters: Optional[str]
    """Any additional parameters after the name."""

    def __str__(self) -> str:
        return (
            self.name if self.parameters is None else f"{self.name} {self.parameters}"
        )

    @property
    def markup(self) -> str:
        """Get the string representation of this tag."""
        return (
            f"[{self.name}]"
            if self.parameters is None
            else f"[{self.name}={self.parameters}]"
        )


_ReStringMatch = Match[str]  # regex match object
_ReSubCallable = Callable[[_ReStringMatch], str]  # Callable invoked by re.sub
_EscapeSubMethod = Callable[[_ReSubCallable, str], str]  # Sub method of a compiled re


def escape(
    markup: str,
    _escape: _EscapeSubMethod = re.compile(r"(\\*)(\[[a-z#/@][^[]*?])").sub,
) -> str:
    """Escapes text so that it won't be interpreted as markup.

    Args:
        markup (str): Content to be inserted in to markup.

    Returns:
        str: Markup with square brackets escaped.
    """

    def escape_backslashes(match: Match[str]) -> str:
        """Called by re.sub replace matches."""
        backslashes, text = match.groups()
        return f"{backslashes}{backslashes}\\{text}"

    markup = _escape(escape_backslashes, markup)
    if markup.endswith("\\") and not markup.endswith("\\\\"):
        return markup + "\\"

    return markup


def _parse(markup: str) -> Iterable[Tuple[int, Optional[str], Optional[Tag]]]:
    """Parse markup in to an iterable of tuples of (position, text, tag).

    Args:
        markup (str): A string containing console markup

    """
    position = 0
    _divmod = divmod
    _Tag = Tag
    for match in RE_TAGS.finditer(markup):
        full_text, escapes, tag_text = match.groups()
        start, end = match.span()
        if start > position:
            yield start, markup[position:start], None
        if escapes:
            backslashes, escaped = _divmod(len(escapes), 2)
            if backslashes:
                # Literal backslashes
                yield start, "\\" * backslashes, None
                start += backslashes * 2
            if escaped:
                # Escape of tag
                yield start, full_text[len(escapes) :], None
                position = end
                continue
        text, equals, parameters = tag_text.partition("=")
        yield start, None, _Tag(text, parameters if equals else None)
        position = end
    if position < len(markup):
        yield position, markup[position:], None


def render(
    markup: str,
    style: Union[str, Style] = "",
    emoji: bool = True,
    emoji_variant: Optional[EmojiVariant] = None,
) -> Text:
    """Render console markup in to a Text instance.

    Args:
        markup (str): A string containing console markup.
        style: (Union[str, Style]): The style to use.
        emoji (bool, optional): Also render emoji code. Defaults to True.
        emoji_variant (str, optional): Optional emoji variant, either "text" or "emoji". Defaults to None.


    Raises:
        MarkupError: If there is a syntax error in the markup.

    Returns:
        Text: A test instance.
    """
    emoji_replace = _emoji_replace
    if "[" not in markup:
        return Text(
            emoji_replace(markup, default_variant=emoji_variant) if emoji else markup,
            style=style,
        )
    text = Text(style=style)
    append = text.append
    normalize = Style.normalize

    style_stack: List[Tuple[int, Tag]] = []
    pop = style_stack.pop

    spans: List[Span] = []
    append_span = spans.append

    _Span = Span
    _Tag = Tag

    def pop_style(style_name: str) -> Tuple[int, Tag]:
        """Pop tag matching given style name."""
        for index, (_, tag) in enumerate(reversed(style_stack), 1):
            if tag.name == style_name:
                return pop(-index)
        raise KeyError(style_name)

    for position, plain_text, tag in _parse(markup):
        if plain_text is not None:
            # Handle open brace escapes, where the brace is not part of a tag.
            plain_text = plain_text.replace("\\[", "[")
            append(emoji_replace(plain_text) if emoji else plain_text)
        elif tag is not None:
            if tag.name.startswith("/"):  # Closing tag
                style_name = tag.name[1:].strip()

                if style_name:  # explicit close
                    style_name = normalize(style_name)
                    try:
                        start, open_tag = pop_style(style_name)
                    except KeyError:
                        raise MarkupError(
                            f"closing tag '{tag.markup}' at position {position} doesn't match any open tag"
                        ) from None
                else:  # implicit close
                    try:
                        start, open_tag = pop()
                    except IndexError:
                        raise MarkupError(
                            f"closing tag '[/]' at position {position} has nothing to close"
                        ) from None

                if open_tag.name.startswith("@"):
                    if open_tag.parameters:
                        handler_name = ""
                        parameters = open_tag.parameters.strip()
                        handler_match = RE_HANDLER.match(parameters)
                        if handler_match is not None:
                            handler_name, match_parameters = handler_match.groups()
                            parameters = (
                                "()" if match_parameters is None else match_parameters
                            )

                        try:
                            meta_params = literal_eval(parameters)
                        except SyntaxError as error:
                            raise MarkupError(
                                f"error parsing {parameters!r} in {open_tag.parameters!r}; {error.msg}"
                            )
                        except Exception as error:
                            raise MarkupError(
                                f"error parsing {open_tag.parameters!r}; {error}"
                            ) from None

                        if handler_name:
                            meta_params = (
                                handler_name,
                                meta_params
                                if isinstance(meta_params, tuple)
                                else (meta_params,),
                            )

                    else:
                        meta_params = ()

                    append_span(
                        _Span(
                            start, len(text), Style(meta={open_tag.name: meta_params})
                        )
                    )
                else:
                    append_span(_Span(start, len(text), str(open_tag)))

            else:  # Opening tag
                normalized_tag = _Tag(normalize(tag.name), tag.parameters)
                style_stack.append((len(text), normalized_tag))

    text_length = len(text)
    while style_stack:
        start, tag = style_stack.pop()
        style = str(tag)
        if style:
            append_span(_Span(start, text_length, style))

    text.spans = sorted(spans[::-1], key=attrgetter("start"))
    return text


if __name__ == "__main__":  # pragma: no cover
    MARKUP = [
        "[red]Hello World[/red]",
        "[magenta]Hello [b]World[/b]",
        "[bold]Bold[italic] bold and italic [/bold]italic[/italic]",
        "Click [link=https://www.willmcgugan.com]here[/link] to visit my Blog",
        ":warning-emoji: [bold red blink] DANGER![/]",
    ]

    from pip._vendor.rich import print
    from pip._vendor.rich.table import Table

    grid = Table("Markup", "Result", padding=(0, 1))

    for markup in MARKUP:
        grid.add_row(Text(markup), markup)

    print(grid)

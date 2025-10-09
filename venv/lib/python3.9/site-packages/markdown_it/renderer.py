"""
class Renderer

Generates HTML from parsed token stream. Each instance has independent
copy of rules. Those can be rewritten with ease. Also, you can add new
rules if you create plugin and adds new token types.
"""
from __future__ import annotations

from collections.abc import Sequence
import inspect
from typing import Any, ClassVar, Protocol

from .common.utils import escapeHtml, unescapeAll
from .token import Token
from .utils import EnvType, OptionsDict


class RendererProtocol(Protocol):
    __output__: ClassVar[str]

    def render(
        self, tokens: Sequence[Token], options: OptionsDict, env: EnvType
    ) -> Any:
        ...


class RendererHTML(RendererProtocol):
    """Contains render rules for tokens. Can be updated and extended.

    Example:

    Each rule is called as independent static function with fixed signature:

    ::

        class Renderer:
            def token_type_name(self, tokens, idx, options, env) {
                # ...
                return renderedHTML

    ::

        class CustomRenderer(RendererHTML):
            def strong_open(self, tokens, idx, options, env):
                return '<b>'
            def strong_close(self, tokens, idx, options, env):
                return '</b>'

        md = MarkdownIt(renderer_cls=CustomRenderer)

        result = md.render(...)

    See https://github.com/markdown-it/markdown-it/blob/master/lib/renderer.js
    for more details and examples.
    """

    __output__ = "html"

    def __init__(self, parser: Any = None):
        self.rules = {
            k: v
            for k, v in inspect.getmembers(self, predicate=inspect.ismethod)
            if not (k.startswith("render") or k.startswith("_"))
        }

    def render(
        self, tokens: Sequence[Token], options: OptionsDict, env: EnvType
    ) -> str:
        """Takes token stream and generates HTML.

        :param tokens: list on block tokens to render
        :param options: params of parser instance
        :param env: additional data from parsed input

        """
        result = ""

        for i, token in enumerate(tokens):
            if token.type == "inline":
                if token.children:
                    result += self.renderInline(token.children, options, env)
            elif token.type in self.rules:
                result += self.rules[token.type](tokens, i, options, env)
            else:
                result += self.renderToken(tokens, i, options, env)

        return result

    def renderInline(
        self, tokens: Sequence[Token], options: OptionsDict, env: EnvType
    ) -> str:
        """The same as ``render``, but for single token of `inline` type.

        :param tokens: list on block tokens to render
        :param options: params of parser instance
        :param env: additional data from parsed input (references, for example)
        """
        result = ""

        for i, token in enumerate(tokens):
            if token.type in self.rules:
                result += self.rules[token.type](tokens, i, options, env)
            else:
                result += self.renderToken(tokens, i, options, env)

        return result

    def renderToken(
        self,
        tokens: Sequence[Token],
        idx: int,
        options: OptionsDict,
        env: EnvType,
    ) -> str:
        """Default token renderer.

        Can be overridden by custom function

        :param idx: token index to render
        :param options: params of parser instance
        """
        result = ""
        needLf = False
        token = tokens[idx]

        # Tight list paragraphs
        if token.hidden:
            return ""

        # Insert a newline between hidden paragraph and subsequent opening
        # block-level tag.
        #
        # For example, here we should insert a newline before blockquote:
        #  - a
        #    >
        #
        if token.block and token.nesting != -1 and idx and tokens[idx - 1].hidden:
            result += "\n"

        # Add token name, e.g. `<img`
        result += ("</" if token.nesting == -1 else "<") + token.tag

        # Encode attributes, e.g. `<img src="foo"`
        result += self.renderAttrs(token)

        # Add a slash for self-closing tags, e.g. `<img src="foo" /`
        if token.nesting == 0 and options["xhtmlOut"]:
            result += " /"

        # Check if we need to add a newline after this tag
        if token.block:
            needLf = True

            if token.nesting == 1 and (idx + 1 < len(tokens)):
                nextToken = tokens[idx + 1]

                if nextToken.type == "inline" or nextToken.hidden:  # noqa: SIM114
                    # Block-level tag containing an inline tag.
                    #
                    needLf = False

                elif nextToken.nesting == -1 and nextToken.tag == token.tag:
                    # Opening tag + closing tag of the same type. E.g. `<li></li>`.
                    #
                    needLf = False

        result += ">\n" if needLf else ">"

        return result

    @staticmethod
    def renderAttrs(token: Token) -> str:
        """Render token attributes to string."""
        result = ""

        for key, value in token.attrItems():
            result += " " + escapeHtml(key) + '="' + escapeHtml(str(value)) + '"'

        return result

    def renderInlineAsText(
        self,
        tokens: Sequence[Token] | None,
        options: OptionsDict,
        env: EnvType,
    ) -> str:
        """Special kludge for image `alt` attributes to conform CommonMark spec.

        Don't try to use it! Spec requires to show `alt` content with stripped markup,
        instead of simple escaping.

        :param tokens: list on block tokens to render
        :param options: params of parser instance
        :param env: additional data from parsed input
        """
        result = ""

        for token in tokens or []:
            if token.type == "text":
                result += token.content
            elif token.type == "image":
                if token.children:
                    result += self.renderInlineAsText(token.children, options, env)
            elif token.type == "softbreak":
                result += "\n"

        return result

    ###################################################

    def code_inline(
        self, tokens: Sequence[Token], idx: int, options: OptionsDict, env: EnvType
    ) -> str:
        token = tokens[idx]
        return (
            "<code"
            + self.renderAttrs(token)
            + ">"
            + escapeHtml(tokens[idx].content)
            + "</code>"
        )

    def code_block(
        self,
        tokens: Sequence[Token],
        idx: int,
        options: OptionsDict,
        env: EnvType,
    ) -> str:
        token = tokens[idx]

        return (
            "<pre"
            + self.renderAttrs(token)
            + "><code>"
            + escapeHtml(tokens[idx].content)
            + "</code></pre>\n"
        )

    def fence(
        self,
        tokens: Sequence[Token],
        idx: int,
        options: OptionsDict,
        env: EnvType,
    ) -> str:
        token = tokens[idx]
        info = unescapeAll(token.info).strip() if token.info else ""
        langName = ""
        langAttrs = ""

        if info:
            arr = info.split(maxsplit=1)
            langName = arr[0]
            if len(arr) == 2:
                langAttrs = arr[1]

        if options.highlight:
            highlighted = options.highlight(
                token.content, langName, langAttrs
            ) or escapeHtml(token.content)
        else:
            highlighted = escapeHtml(token.content)

        if highlighted.startswith("<pre"):
            return highlighted + "\n"

        # If language exists, inject class gently, without modifying original token.
        # May be, one day we will add .deepClone() for token and simplify this part, but
        # now we prefer to keep things local.
        if info:
            # Fake token just to render attributes
            tmpToken = Token(type="", tag="", nesting=0, attrs=token.attrs.copy())
            tmpToken.attrJoin("class", options.langPrefix + langName)

            return (
                "<pre><code"
                + self.renderAttrs(tmpToken)
                + ">"
                + highlighted
                + "</code></pre>\n"
            )

        return (
            "<pre><code"
            + self.renderAttrs(token)
            + ">"
            + highlighted
            + "</code></pre>\n"
        )

    def image(
        self,
        tokens: Sequence[Token],
        idx: int,
        options: OptionsDict,
        env: EnvType,
    ) -> str:
        token = tokens[idx]

        # "alt" attr MUST be set, even if empty. Because it's mandatory and
        # should be placed on proper position for tests.
        if token.children:
            token.attrSet("alt", self.renderInlineAsText(token.children, options, env))
        else:
            token.attrSet("alt", "")

        return self.renderToken(tokens, idx, options, env)

    def hardbreak(
        self, tokens: Sequence[Token], idx: int, options: OptionsDict, env: EnvType
    ) -> str:
        return "<br />\n" if options.xhtmlOut else "<br>\n"

    def softbreak(
        self, tokens: Sequence[Token], idx: int, options: OptionsDict, env: EnvType
    ) -> str:
        return (
            ("<br />\n" if options.xhtmlOut else "<br>\n") if options.breaks else "\n"
        )

    def text(
        self, tokens: Sequence[Token], idx: int, options: OptionsDict, env: EnvType
    ) -> str:
        return escapeHtml(tokens[idx].content)

    def html_block(
        self, tokens: Sequence[Token], idx: int, options: OptionsDict, env: EnvType
    ) -> str:
        return tokens[idx].content

    def html_inline(
        self, tokens: Sequence[Token], idx: int, options: OptionsDict, env: EnvType
    ) -> str:
        return tokens[idx].content

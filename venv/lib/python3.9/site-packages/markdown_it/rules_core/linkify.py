from __future__ import annotations

import re
from typing import Protocol

from ..common.utils import arrayReplaceAt, isLinkClose, isLinkOpen
from ..token import Token
from .state_core import StateCore

HTTP_RE = re.compile(r"^http://")
MAILTO_RE = re.compile(r"^mailto:")
TEST_MAILTO_RE = re.compile(r"^mailto:", flags=re.IGNORECASE)


def linkify(state: StateCore) -> None:
    """Rule for identifying plain-text links."""
    if not state.md.options.linkify:
        return

    if not state.md.linkify:
        raise ModuleNotFoundError("Linkify enabled but not installed.")

    for inline_token in state.tokens:
        if inline_token.type != "inline" or not state.md.linkify.pretest(
            inline_token.content
        ):
            continue

        tokens = inline_token.children

        htmlLinkLevel = 0

        # We scan from the end, to keep position when new tags added.
        # Use reversed logic in links start/end match
        assert tokens is not None
        i = len(tokens)
        while i >= 1:
            i -= 1
            assert isinstance(tokens, list)
            currentToken = tokens[i]

            # Skip content of markdown links
            if currentToken.type == "link_close":
                i -= 1
                while (
                    tokens[i].level != currentToken.level
                    and tokens[i].type != "link_open"
                ):
                    i -= 1
                continue

            # Skip content of html tag links
            if currentToken.type == "html_inline":
                if isLinkOpen(currentToken.content) and htmlLinkLevel > 0:
                    htmlLinkLevel -= 1
                if isLinkClose(currentToken.content):
                    htmlLinkLevel += 1
            if htmlLinkLevel > 0:
                continue

            if currentToken.type == "text" and state.md.linkify.test(
                currentToken.content
            ):
                text = currentToken.content
                links: list[_LinkType] = state.md.linkify.match(text) or []

                # Now split string to nodes
                nodes = []
                level = currentToken.level
                lastPos = 0

                # forbid escape sequence at the start of the string,
                # this avoids http\://example.com/ from being linkified as
                # http:<a href="//example.com/">//example.com/</a>
                if (
                    links
                    and links[0].index == 0
                    and i > 0
                    and tokens[i - 1].type == "text_special"
                ):
                    links = links[1:]

                for link in links:
                    url = link.url
                    fullUrl = state.md.normalizeLink(url)
                    if not state.md.validateLink(fullUrl):
                        continue

                    urlText = link.text

                    # Linkifier might send raw hostnames like "example.com", where url
                    # starts with domain name. So we prepend http:// in those cases,
                    # and remove it afterwards.
                    if not link.schema:
                        urlText = HTTP_RE.sub(
                            "", state.md.normalizeLinkText("http://" + urlText)
                        )
                    elif link.schema == "mailto:" and TEST_MAILTO_RE.search(urlText):
                        urlText = MAILTO_RE.sub(
                            "", state.md.normalizeLinkText("mailto:" + urlText)
                        )
                    else:
                        urlText = state.md.normalizeLinkText(urlText)

                    pos = link.index

                    if pos > lastPos:
                        token = Token("text", "", 0)
                        token.content = text[lastPos:pos]
                        token.level = level
                        nodes.append(token)

                    token = Token("link_open", "a", 1)
                    token.attrs = {"href": fullUrl}
                    token.level = level
                    level += 1
                    token.markup = "linkify"
                    token.info = "auto"
                    nodes.append(token)

                    token = Token("text", "", 0)
                    token.content = urlText
                    token.level = level
                    nodes.append(token)

                    token = Token("link_close", "a", -1)
                    level -= 1
                    token.level = level
                    token.markup = "linkify"
                    token.info = "auto"
                    nodes.append(token)

                    lastPos = link.last_index

                if lastPos < len(text):
                    token = Token("text", "", 0)
                    token.content = text[lastPos:]
                    token.level = level
                    nodes.append(token)

                inline_token.children = tokens = arrayReplaceAt(tokens, i, nodes)


class _LinkType(Protocol):
    url: str
    text: str
    index: int
    last_index: int
    schema: str | None

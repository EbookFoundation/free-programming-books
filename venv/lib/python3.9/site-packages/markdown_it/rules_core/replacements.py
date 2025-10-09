"""Simple typographic replacements

* ``(c)``, ``(C)`` → ©
* ``(tm)``, ``(TM)`` → ™
* ``(r)``, ``(R)`` → ®
* ``+-`` → ±
* ``...`` → …
* ``?....`` → ?..
* ``!....`` → !..
* ``????????`` → ???
* ``!!!!!`` → !!!
* ``,,,`` → ,
* ``--`` → &ndash
* ``---`` → &mdash
"""
from __future__ import annotations

import logging
import re

from ..token import Token
from .state_core import StateCore

LOGGER = logging.getLogger(__name__)

# TODO:
# - fractionals 1/2, 1/4, 3/4 -> ½, ¼, ¾
# - multiplication 2 x 4 -> 2 × 4

RARE_RE = re.compile(r"\+-|\.\.|\?\?\?\?|!!!!|,,|--")

# Workaround for phantomjs - need regex without /g flag,
# or root check will fail every second time
# SCOPED_ABBR_TEST_RE = r"\((c|tm|r)\)"

SCOPED_ABBR_RE = re.compile(r"\((c|tm|r)\)", flags=re.IGNORECASE)

PLUS_MINUS_RE = re.compile(r"\+-")

ELLIPSIS_RE = re.compile(r"\.{2,}")

ELLIPSIS_QUESTION_EXCLAMATION_RE = re.compile(r"([?!])…")

QUESTION_EXCLAMATION_RE = re.compile(r"([?!]){4,}")

COMMA_RE = re.compile(r",{2,}")

EM_DASH_RE = re.compile(r"(^|[^-])---(?=[^-]|$)", flags=re.MULTILINE)

EN_DASH_RE = re.compile(r"(^|\s)--(?=\s|$)", flags=re.MULTILINE)

EN_DASH_INDENT_RE = re.compile(r"(^|[^-\s])--(?=[^-\s]|$)", flags=re.MULTILINE)


SCOPED_ABBR = {"c": "©", "r": "®", "tm": "™"}


def replaceFn(match: re.Match[str]) -> str:
    return SCOPED_ABBR[match.group(1).lower()]


def replace_scoped(inlineTokens: list[Token]) -> None:
    inside_autolink = 0

    for token in inlineTokens:
        if token.type == "text" and not inside_autolink:
            token.content = SCOPED_ABBR_RE.sub(replaceFn, token.content)

        if token.type == "link_open" and token.info == "auto":
            inside_autolink -= 1

        if token.type == "link_close" and token.info == "auto":
            inside_autolink += 1


def replace_rare(inlineTokens: list[Token]) -> None:
    inside_autolink = 0

    for token in inlineTokens:
        if (
            token.type == "text"
            and (not inside_autolink)
            and RARE_RE.search(token.content)
        ):
            # +- -> ±
            token.content = PLUS_MINUS_RE.sub("±", token.content)

            # .., ..., ....... -> …
            token.content = ELLIPSIS_RE.sub("…", token.content)

            # but ?..... & !..... -> ?.. & !..
            token.content = ELLIPSIS_QUESTION_EXCLAMATION_RE.sub("\\1..", token.content)
            token.content = QUESTION_EXCLAMATION_RE.sub("\\1\\1\\1", token.content)

            # ,,  ,,,  ,,,, -> ,
            token.content = COMMA_RE.sub(",", token.content)

            # em-dash
            token.content = EM_DASH_RE.sub("\\1\u2014", token.content)

            # en-dash
            token.content = EN_DASH_RE.sub("\\1\u2013", token.content)
            token.content = EN_DASH_INDENT_RE.sub("\\1\u2013", token.content)

        if token.type == "link_open" and token.info == "auto":
            inside_autolink -= 1

        if token.type == "link_close" and token.info == "auto":
            inside_autolink += 1


def replace(state: StateCore) -> None:
    if not state.md.options.typographer:
        return

    for token in state.tokens:
        if token.type != "inline":
            continue
        if token.children is None:
            continue

        if SCOPED_ABBR_RE.search(token.content):
            replace_scoped(token.children)

        if RARE_RE.search(token.content):
            replace_rare(token.children)

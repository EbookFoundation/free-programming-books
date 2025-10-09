# HTML block
from __future__ import annotations

import logging
import re

from ..common.html_blocks import block_names
from ..common.html_re import HTML_OPEN_CLOSE_TAG_STR
from .state_block import StateBlock

LOGGER = logging.getLogger(__name__)

# An array of opening and corresponding closing sequences for html tags,
# last argument defines whether it can terminate a paragraph or not
HTML_SEQUENCES: list[tuple[re.Pattern[str], re.Pattern[str], bool]] = [
    (
        re.compile(r"^<(script|pre|style|textarea)(?=(\s|>|$))", re.IGNORECASE),
        re.compile(r"<\/(script|pre|style|textarea)>", re.IGNORECASE),
        True,
    ),
    (re.compile(r"^<!--"), re.compile(r"-->"), True),
    (re.compile(r"^<\?"), re.compile(r"\?>"), True),
    (re.compile(r"^<![A-Z]"), re.compile(r">"), True),
    (re.compile(r"^<!\[CDATA\["), re.compile(r"\]\]>"), True),
    (
        re.compile("^</?(" + "|".join(block_names) + ")(?=(\\s|/?>|$))", re.IGNORECASE),
        re.compile(r"^$"),
        True,
    ),
    (re.compile(HTML_OPEN_CLOSE_TAG_STR + "\\s*$"), re.compile(r"^$"), False),
]


def html_block(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    LOGGER.debug(
        "entering html_block: %s, %s, %s, %s", state, startLine, endLine, silent
    )
    pos = state.bMarks[startLine] + state.tShift[startLine]
    maximum = state.eMarks[startLine]

    if state.is_code_block(startLine):
        return False

    if not state.md.options.get("html", None):
        return False

    if state.src[pos] != "<":
        return False

    lineText = state.src[pos:maximum]

    html_seq = None
    for HTML_SEQUENCE in HTML_SEQUENCES:
        if HTML_SEQUENCE[0].search(lineText):
            html_seq = HTML_SEQUENCE
            break

    if not html_seq:
        return False

    if silent:
        # true if this sequence can be a terminator, false otherwise
        return html_seq[2]

    nextLine = startLine + 1

    # If we are here - we detected HTML block.
    # Let's roll down till block end.
    if not html_seq[1].search(lineText):
        while nextLine < endLine:
            if state.sCount[nextLine] < state.blkIndent:
                break

            pos = state.bMarks[nextLine] + state.tShift[nextLine]
            maximum = state.eMarks[nextLine]
            lineText = state.src[pos:maximum]

            if html_seq[1].search(lineText):
                if len(lineText) != 0:
                    nextLine += 1
                break
            nextLine += 1

    state.line = nextLine

    token = state.push("html_block", "", 0)
    token.map = [startLine, nextLine]
    token.content = state.getLines(startLine, nextLine, state.blkIndent, True)

    return True

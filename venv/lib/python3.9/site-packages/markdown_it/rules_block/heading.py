""" Atex heading (#, ##, ...) """
from __future__ import annotations

import logging

from ..common.utils import isStrSpace
from .state_block import StateBlock

LOGGER = logging.getLogger(__name__)


def heading(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    LOGGER.debug("entering heading: %s, %s, %s, %s", state, startLine, endLine, silent)

    pos = state.bMarks[startLine] + state.tShift[startLine]
    maximum = state.eMarks[startLine]

    if state.is_code_block(startLine):
        return False

    ch: str | None = state.src[pos]

    if ch != "#" or pos >= maximum:
        return False

    # count heading level
    level = 1
    pos += 1
    try:
        ch = state.src[pos]
    except IndexError:
        ch = None
    while ch == "#" and pos < maximum and level <= 6:
        level += 1
        pos += 1
        try:
            ch = state.src[pos]
        except IndexError:
            ch = None

    if level > 6 or (pos < maximum and not isStrSpace(ch)):
        return False

    if silent:
        return True

    # Let's cut tails like '    ###  ' from the end of string

    maximum = state.skipSpacesBack(maximum, pos)
    tmp = state.skipCharsStrBack(maximum, "#", pos)
    if tmp > pos and isStrSpace(state.src[tmp - 1]):
        maximum = tmp

    state.line = startLine + 1

    token = state.push("heading_open", "h" + str(level), 1)
    token.markup = "########"[:level]
    token.map = [startLine, state.line]

    token = state.push("inline", "", 0)
    token.content = state.src[pos:maximum].strip()
    token.map = [startLine, state.line]
    token.children = []

    token = state.push("heading_close", "h" + str(level), -1)
    token.markup = "########"[:level]

    return True

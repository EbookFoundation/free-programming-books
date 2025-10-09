"""Horizontal rule

At least 3 of these characters on a line * - _
"""
import logging

from ..common.utils import isStrSpace
from .state_block import StateBlock

LOGGER = logging.getLogger(__name__)


def hr(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    LOGGER.debug("entering hr: %s, %s, %s, %s", state, startLine, endLine, silent)

    pos = state.bMarks[startLine] + state.tShift[startLine]
    maximum = state.eMarks[startLine]

    if state.is_code_block(startLine):
        return False

    try:
        marker = state.src[pos]
    except IndexError:
        return False
    pos += 1

    # Check hr marker
    if marker not in ("*", "-", "_"):
        return False

    # markers can be mixed with spaces, but there should be at least 3 of them

    cnt = 1
    while pos < maximum:
        ch = state.src[pos]
        pos += 1
        if ch != marker and not isStrSpace(ch):
            return False
        if ch == marker:
            cnt += 1

    if cnt < 3:
        return False

    if silent:
        return True

    state.line = startLine + 1

    token = state.push("hr", "hr", 0)
    token.map = [startLine, state.line]
    token.markup = marker * (cnt + 1)

    return True

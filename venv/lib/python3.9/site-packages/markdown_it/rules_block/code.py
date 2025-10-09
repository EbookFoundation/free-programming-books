"""Code block (4 spaces padded)."""
import logging

from .state_block import StateBlock

LOGGER = logging.getLogger(__name__)


def code(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    LOGGER.debug("entering code: %s, %s, %s, %s", state, startLine, endLine, silent)

    if not state.is_code_block(startLine):
        return False

    last = nextLine = startLine + 1

    while nextLine < endLine:
        if state.isEmpty(nextLine):
            nextLine += 1
            continue

        if state.is_code_block(nextLine):
            nextLine += 1
            last = nextLine
            continue

        break

    state.line = last

    token = state.push("code_block", "code", 0)
    token.content = state.getLines(startLine, last, 4 + state.blkIndent, False) + "\n"
    token.map = [startLine, state.line]

    return True

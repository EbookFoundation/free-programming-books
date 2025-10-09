# fences (``` lang, ~~~ lang)
import logging

from .state_block import StateBlock

LOGGER = logging.getLogger(__name__)


def fence(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    LOGGER.debug("entering fence: %s, %s, %s, %s", state, startLine, endLine, silent)

    haveEndMarker = False
    pos = state.bMarks[startLine] + state.tShift[startLine]
    maximum = state.eMarks[startLine]

    if state.is_code_block(startLine):
        return False

    if pos + 3 > maximum:
        return False

    marker = state.src[pos]

    if marker not in ("~", "`"):
        return False

    # scan marker length
    mem = pos
    pos = state.skipCharsStr(pos, marker)

    length = pos - mem

    if length < 3:
        return False

    markup = state.src[mem:pos]
    params = state.src[pos:maximum]

    if marker == "`" and marker in params:
        return False

    # Since start is found, we can report success here in validation mode
    if silent:
        return True

    # search end of block
    nextLine = startLine

    while True:
        nextLine += 1
        if nextLine >= endLine:
            # unclosed block should be autoclosed by end of document.
            # also block seems to be autoclosed by end of parent
            break

        pos = mem = state.bMarks[nextLine] + state.tShift[nextLine]
        maximum = state.eMarks[nextLine]

        if pos < maximum and state.sCount[nextLine] < state.blkIndent:
            # non-empty line with negative indent should stop the list:
            # - ```
            #  test
            break

        try:
            if state.src[pos] != marker:
                continue
        except IndexError:
            break

        if state.is_code_block(nextLine):
            continue

        pos = state.skipCharsStr(pos, marker)

        # closing code fence must be at least as long as the opening one
        if pos - mem < length:
            continue

        # make sure tail has spaces only
        pos = state.skipSpaces(pos)

        if pos < maximum:
            continue

        haveEndMarker = True
        # found!
        break

    # If a fence has heading spaces, they should be removed from its inner block
    length = state.sCount[startLine]

    state.line = nextLine + (1 if haveEndMarker else 0)

    token = state.push("fence", "code", 0)
    token.info = params
    token.content = state.getLines(startLine + 1, nextLine, length, True)
    token.markup = markup
    token.map = [startLine, state.line]

    return True

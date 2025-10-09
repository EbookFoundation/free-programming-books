# lheading (---, ==)
import logging

from .state_block import StateBlock

LOGGER = logging.getLogger(__name__)


def lheading(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    LOGGER.debug("entering lheading: %s, %s, %s, %s", state, startLine, endLine, silent)

    level = None
    nextLine = startLine + 1
    ruler = state.md.block.ruler
    terminatorRules = ruler.getRules("paragraph")

    if state.is_code_block(startLine):
        return False

    oldParentType = state.parentType
    state.parentType = "paragraph"  # use paragraph to match terminatorRules

    # jump line-by-line until empty one or EOF
    while nextLine < endLine and not state.isEmpty(nextLine):
        # this would be a code block normally, but after paragraph
        # it's considered a lazy continuation regardless of what's there
        if state.sCount[nextLine] - state.blkIndent > 3:
            nextLine += 1
            continue

        # Check for underline in setext header
        if state.sCount[nextLine] >= state.blkIndent:
            pos = state.bMarks[nextLine] + state.tShift[nextLine]
            maximum = state.eMarks[nextLine]

            if pos < maximum:
                marker = state.src[pos]

                if marker in ("-", "="):
                    pos = state.skipCharsStr(pos, marker)
                    pos = state.skipSpaces(pos)

                    # /* = */
                    if pos >= maximum:
                        level = 1 if marker == "=" else 2
                        break

        # quirk for blockquotes, this line should already be checked by that rule
        if state.sCount[nextLine] < 0:
            nextLine += 1
            continue

        # Some tags can terminate paragraph without empty line.
        terminate = False
        for terminatorRule in terminatorRules:
            if terminatorRule(state, nextLine, endLine, True):
                terminate = True
                break
        if terminate:
            break

        nextLine += 1

    if not level:
        # Didn't find valid underline
        return False

    content = state.getLines(startLine, nextLine, state.blkIndent, False).strip()

    state.line = nextLine + 1

    token = state.push("heading_open", "h" + str(level), 1)
    token.markup = marker
    token.map = [startLine, state.line]

    token = state.push("inline", "", 0)
    token.content = content
    token.map = [startLine, state.line - 1]
    token.children = []

    token = state.push("heading_close", "h" + str(level), -1)
    token.markup = marker

    state.parentType = oldParentType

    return True

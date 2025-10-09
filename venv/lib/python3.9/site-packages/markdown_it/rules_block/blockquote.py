# Block quotes
from __future__ import annotations

import logging

from ..common.utils import isStrSpace
from .state_block import StateBlock

LOGGER = logging.getLogger(__name__)


def blockquote(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    LOGGER.debug(
        "entering blockquote: %s, %s, %s, %s", state, startLine, endLine, silent
    )

    oldLineMax = state.lineMax
    pos = state.bMarks[startLine] + state.tShift[startLine]
    max = state.eMarks[startLine]

    if state.is_code_block(startLine):
        return False

    # check the block quote marker
    try:
        if state.src[pos] != ">":
            return False
    except IndexError:
        return False
    pos += 1

    # we know that it's going to be a valid blockquote,
    # so no point trying to find the end of it in silent mode
    if silent:
        return True

    # set offset past spaces and ">"
    initial = offset = state.sCount[startLine] + 1

    try:
        second_char: str | None = state.src[pos]
    except IndexError:
        second_char = None

    # skip one optional space after '>'
    if second_char == " ":
        # ' >   test '
        #     ^ -- position start of line here:
        pos += 1
        initial += 1
        offset += 1
        adjustTab = False
        spaceAfterMarker = True
    elif second_char == "\t":
        spaceAfterMarker = True

        if (state.bsCount[startLine] + offset) % 4 == 3:
            # '  >\t  test '
            #       ^ -- position start of line here (tab has width==1)
            pos += 1
            initial += 1
            offset += 1
            adjustTab = False
        else:
            # ' >\t  test '
            #    ^ -- position start of line here + shift bsCount slightly
            #         to make extra space appear
            adjustTab = True

    else:
        spaceAfterMarker = False

    oldBMarks = [state.bMarks[startLine]]
    state.bMarks[startLine] = pos

    while pos < max:
        ch = state.src[pos]

        if isStrSpace(ch):
            if ch == "\t":
                offset += (
                    4
                    - (offset + state.bsCount[startLine] + (1 if adjustTab else 0)) % 4
                )
            else:
                offset += 1

        else:
            break

        pos += 1

    oldBSCount = [state.bsCount[startLine]]
    state.bsCount[startLine] = (
        state.sCount[startLine] + 1 + (1 if spaceAfterMarker else 0)
    )

    lastLineEmpty = pos >= max

    oldSCount = [state.sCount[startLine]]
    state.sCount[startLine] = offset - initial

    oldTShift = [state.tShift[startLine]]
    state.tShift[startLine] = pos - state.bMarks[startLine]

    terminatorRules = state.md.block.ruler.getRules("blockquote")

    oldParentType = state.parentType
    state.parentType = "blockquote"

    # Search the end of the block
    #
    # Block ends with either:
    #  1. an empty line outside:
    #     ```
    #     > test
    #
    #     ```
    #  2. an empty line inside:
    #     ```
    #     >
    #     test
    #     ```
    #  3. another tag:
    #     ```
    #     > test
    #      - - -
    #     ```

    # for (nextLine = startLine + 1; nextLine < endLine; nextLine++) {
    nextLine = startLine + 1
    while nextLine < endLine:
        # check if it's outdented, i.e. it's inside list item and indented
        # less than said list item:
        #
        # ```
        # 1. anything
        #    > current blockquote
        # 2. checking this line
        # ```
        isOutdented = state.sCount[nextLine] < state.blkIndent

        pos = state.bMarks[nextLine] + state.tShift[nextLine]
        max = state.eMarks[nextLine]

        if pos >= max:
            # Case 1: line is not inside the blockquote, and this line is empty.
            break

        evaluatesTrue = state.src[pos] == ">" and not isOutdented
        pos += 1
        if evaluatesTrue:
            # This line is inside the blockquote.

            # set offset past spaces and ">"
            initial = offset = state.sCount[nextLine] + 1

            try:
                next_char: str | None = state.src[pos]
            except IndexError:
                next_char = None

            # skip one optional space after '>'
            if next_char == " ":
                # ' >   test '
                #     ^ -- position start of line here:
                pos += 1
                initial += 1
                offset += 1
                adjustTab = False
                spaceAfterMarker = True
            elif next_char == "\t":
                spaceAfterMarker = True

                if (state.bsCount[nextLine] + offset) % 4 == 3:
                    # '  >\t  test '
                    #       ^ -- position start of line here (tab has width==1)
                    pos += 1
                    initial += 1
                    offset += 1
                    adjustTab = False
                else:
                    # ' >\t  test '
                    #    ^ -- position start of line here + shift bsCount slightly
                    #         to make extra space appear
                    adjustTab = True

            else:
                spaceAfterMarker = False

            oldBMarks.append(state.bMarks[nextLine])
            state.bMarks[nextLine] = pos

            while pos < max:
                ch = state.src[pos]

                if isStrSpace(ch):
                    if ch == "\t":
                        offset += (
                            4
                            - (
                                offset
                                + state.bsCount[nextLine]
                                + (1 if adjustTab else 0)
                            )
                            % 4
                        )
                    else:
                        offset += 1
                else:
                    break

                pos += 1

            lastLineEmpty = pos >= max

            oldBSCount.append(state.bsCount[nextLine])
            state.bsCount[nextLine] = (
                state.sCount[nextLine] + 1 + (1 if spaceAfterMarker else 0)
            )

            oldSCount.append(state.sCount[nextLine])
            state.sCount[nextLine] = offset - initial

            oldTShift.append(state.tShift[nextLine])
            state.tShift[nextLine] = pos - state.bMarks[nextLine]

            nextLine += 1
            continue

        # Case 2: line is not inside the blockquote, and the last line was empty.
        if lastLineEmpty:
            break

        # Case 3: another tag found.
        terminate = False

        for terminatorRule in terminatorRules:
            if terminatorRule(state, nextLine, endLine, True):
                terminate = True
                break

        if terminate:
            # Quirk to enforce "hard termination mode" for paragraphs;
            # normally if you call `tokenize(state, startLine, nextLine)`,
            # paragraphs will look below nextLine for paragraph continuation,
            # but if blockquote is terminated by another tag, they shouldn't
            state.lineMax = nextLine

            if state.blkIndent != 0:
                # state.blkIndent was non-zero, we now set it to zero,
                # so we need to re-calculate all offsets to appear as
                # if indent wasn't changed
                oldBMarks.append(state.bMarks[nextLine])
                oldBSCount.append(state.bsCount[nextLine])
                oldTShift.append(state.tShift[nextLine])
                oldSCount.append(state.sCount[nextLine])
                state.sCount[nextLine] -= state.blkIndent

            break

        oldBMarks.append(state.bMarks[nextLine])
        oldBSCount.append(state.bsCount[nextLine])
        oldTShift.append(state.tShift[nextLine])
        oldSCount.append(state.sCount[nextLine])

        # A negative indentation means that this is a paragraph continuation
        #
        state.sCount[nextLine] = -1

        nextLine += 1

    oldIndent = state.blkIndent
    state.blkIndent = 0

    token = state.push("blockquote_open", "blockquote", 1)
    token.markup = ">"
    token.map = lines = [startLine, 0]

    state.md.block.tokenize(state, startLine, nextLine)

    token = state.push("blockquote_close", "blockquote", -1)
    token.markup = ">"

    state.lineMax = oldLineMax
    state.parentType = oldParentType
    lines[1] = state.line

    # Restore original tShift; this might not be necessary since the parser
    # has already been here, but just to make sure we can do that.
    for i, item in enumerate(oldTShift):
        state.bMarks[i + startLine] = oldBMarks[i]
        state.tShift[i + startLine] = item
        state.sCount[i + startLine] = oldSCount[i]
        state.bsCount[i + startLine] = oldBSCount[i]

    state.blkIndent = oldIndent

    return True

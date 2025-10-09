"""
Parse link label

this function assumes that first character ("[") already matches
returns the end of the label

"""
from markdown_it.rules_inline import StateInline


def parseLinkLabel(state: StateInline, start: int, disableNested: bool = False) -> int:
    labelEnd = -1
    oldPos = state.pos
    found = False

    state.pos = start + 1
    level = 1

    while state.pos < state.posMax:
        marker = state.src[state.pos]
        if marker == "]":
            level -= 1
            if level == 0:
                found = True
                break

        prevPos = state.pos
        state.md.inline.skipToken(state)
        if marker == "[":
            if prevPos == state.pos - 1:
                # increase level if we find text `[`,
                # which is not a part of any token
                level += 1
            elif disableNested:
                state.pos = oldPos
                return -1
    if found:
        labelEnd = state.pos

    # restore old state
    state.pos = oldPos

    return labelEnd

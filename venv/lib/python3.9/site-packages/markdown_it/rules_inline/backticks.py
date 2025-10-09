# Parse backticks
import re

from .state_inline import StateInline

regex = re.compile("^ (.+) $")


def backtick(state: StateInline, silent: bool) -> bool:
    pos = state.pos

    if state.src[pos] != "`":
        return False

    start = pos
    pos += 1
    maximum = state.posMax

    # scan marker length
    while pos < maximum and (state.src[pos] == "`"):
        pos += 1

    marker = state.src[start:pos]
    openerLength = len(marker)

    if state.backticksScanned and state.backticks.get(openerLength, 0) <= start:
        if not silent:
            state.pending += marker
        state.pos += openerLength
        return True

    matchStart = matchEnd = pos

    # Nothing found in the cache, scan until the end of the line (or until marker is found)
    while True:
        try:
            matchStart = state.src.index("`", matchEnd)
        except ValueError:
            break
        matchEnd = matchStart + 1

        # scan marker length
        while matchEnd < maximum and (state.src[matchEnd] == "`"):
            matchEnd += 1

        closerLength = matchEnd - matchStart

        if closerLength == openerLength:
            # Found matching closer length.
            if not silent:
                token = state.push("code_inline", "code", 0)
                token.markup = marker
                token.content = state.src[pos:matchStart].replace("\n", " ")
                if (
                    token.content.startswith(" ")
                    and token.content.endswith(" ")
                    and len(token.content.strip()) > 0
                ):
                    token.content = token.content[1:-1]
            state.pos = matchEnd
            return True

        # Some different length found, put it in cache as upper limit of where closer can be found
        state.backticks[closerLength] = matchStart

    # Scanned through the end, didn't find anything
    state.backticksScanned = True

    if not silent:
        state.pending += marker
    state.pos += openerLength
    return True

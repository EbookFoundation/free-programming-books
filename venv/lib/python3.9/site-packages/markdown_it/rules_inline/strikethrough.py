# ~~strike through~~
from __future__ import annotations

from .state_inline import Delimiter, StateInline


def tokenize(state: StateInline, silent: bool) -> bool:
    """Insert each marker as a separate text token, and add it to delimiter list"""
    start = state.pos
    ch = state.src[start]

    if silent:
        return False

    if ch != "~":
        return False

    scanned = state.scanDelims(state.pos, True)
    length = scanned.length

    if length < 2:
        return False

    if length % 2:
        token = state.push("text", "", 0)
        token.content = ch
        length -= 1

    i = 0
    while i < length:
        token = state.push("text", "", 0)
        token.content = ch + ch
        state.delimiters.append(
            Delimiter(
                marker=ord(ch),
                length=0,  # disable "rule of 3" length checks meant for emphasis
                token=len(state.tokens) - 1,
                end=-1,
                open=scanned.can_open,
                close=scanned.can_close,
            )
        )

        i += 2

    state.pos += scanned.length

    return True


def _postProcess(state: StateInline, delimiters: list[Delimiter]) -> None:
    loneMarkers = []
    maximum = len(delimiters)

    i = 0
    while i < maximum:
        startDelim = delimiters[i]

        if startDelim.marker != 0x7E:  # /* ~ */
            i += 1
            continue

        if startDelim.end == -1:
            i += 1
            continue

        endDelim = delimiters[startDelim.end]

        token = state.tokens[startDelim.token]
        token.type = "s_open"
        token.tag = "s"
        token.nesting = 1
        token.markup = "~~"
        token.content = ""

        token = state.tokens[endDelim.token]
        token.type = "s_close"
        token.tag = "s"
        token.nesting = -1
        token.markup = "~~"
        token.content = ""

        if (
            state.tokens[endDelim.token - 1].type == "text"
            and state.tokens[endDelim.token - 1].content == "~"
        ):
            loneMarkers.append(endDelim.token - 1)

        i += 1

    # If a marker sequence has an odd number of characters, it's split
    # like this: `~~~~~` -> `~` + `~~` + `~~`, leaving one marker at the
    # start of the sequence.
    #
    # So, we have to move all those markers after subsequent s_close tags.
    #
    while loneMarkers:
        i = loneMarkers.pop()
        j = i + 1

        while (j < len(state.tokens)) and (state.tokens[j].type == "s_close"):
            j += 1

        j -= 1

        if i != j:
            token = state.tokens[j]
            state.tokens[j] = state.tokens[i]
            state.tokens[i] = token


def postProcess(state: StateInline) -> None:
    """Walk through delimiter list and replace text tokens with tags."""
    tokens_meta = state.tokens_meta
    maximum = len(state.tokens_meta)
    _postProcess(state, state.delimiters)

    curr = 0
    while curr < maximum:
        try:
            curr_meta = tokens_meta[curr]
        except IndexError:
            pass
        else:
            if curr_meta and "delimiters" in curr_meta:
                _postProcess(state, curr_meta["delimiters"])
        curr += 1

"""Proceess '\n'."""
from ..common.utils import charStrAt, isStrSpace
from .state_inline import StateInline


def newline(state: StateInline, silent: bool) -> bool:
    pos = state.pos

    if state.src[pos] != "\n":
        return False

    pmax = len(state.pending) - 1
    maximum = state.posMax

    # '  \n' -> hardbreak
    # Lookup in pending chars is bad practice! Don't copy to other rules!
    # Pending string is stored in concat mode, indexed lookups will cause
    # conversion to flat mode.
    if not silent:
        if pmax >= 0 and charStrAt(state.pending, pmax) == " ":
            if pmax >= 1 and charStrAt(state.pending, pmax - 1) == " ":
                # Find whitespaces tail of pending chars.
                ws = pmax - 1
                while ws >= 1 and charStrAt(state.pending, ws - 1) == " ":
                    ws -= 1
                state.pending = state.pending[:ws]

                state.push("hardbreak", "br", 0)
            else:
                state.pending = state.pending[:-1]
                state.push("softbreak", "br", 0)

        else:
            state.push("softbreak", "br", 0)

    pos += 1

    # skip heading spaces for next line
    while pos < maximum and isStrSpace(state.src[pos]):
        pos += 1

    state.pos = pos
    return True

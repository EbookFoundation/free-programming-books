# Skip text characters for text token, place those to pending buffer
# and increment current pos
from .state_inline import StateInline

# Rule to skip pure text
# '{}$%@~+=:' reserved for extensions

# !!!! Don't confuse with "Markdown ASCII Punctuation" chars
# http://spec.commonmark.org/0.15/#ascii-punctuation-character


_TerminatorChars = {
    "\n",
    "!",
    "#",
    "$",
    "%",
    "&",
    "*",
    "+",
    "-",
    ":",
    "<",
    "=",
    ">",
    "@",
    "[",
    "\\",
    "]",
    "^",
    "_",
    "`",
    "{",
    "}",
    "~",
}


def text(state: StateInline, silent: bool) -> bool:
    pos = state.pos
    posMax = state.posMax
    while (pos < posMax) and state.src[pos] not in _TerminatorChars:
        pos += 1

    if pos == state.pos:
        return False

    if not silent:
        state.pending += state.src[state.pos : pos]

    state.pos = pos

    return True

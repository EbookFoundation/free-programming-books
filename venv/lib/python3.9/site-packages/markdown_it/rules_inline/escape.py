"""
Process escaped chars and hardbreaks
"""
from ..common.utils import isStrSpace
from .state_inline import StateInline


def escape(state: StateInline, silent: bool) -> bool:
    """Process escaped chars and hardbreaks."""
    pos = state.pos
    maximum = state.posMax

    if state.src[pos] != "\\":
        return False

    pos += 1

    # '\' at the end of the inline block
    if pos >= maximum:
        return False

    ch1 = state.src[pos]
    ch1_ord = ord(ch1)
    if ch1 == "\n":
        if not silent:
            state.push("hardbreak", "br", 0)
        pos += 1
        # skip leading whitespaces from next line
        while pos < maximum:
            ch = state.src[pos]
            if not isStrSpace(ch):
                break
            pos += 1

        state.pos = pos
        return True

    escapedStr = state.src[pos]

    if ch1_ord >= 0xD800 and ch1_ord <= 0xDBFF and pos + 1 < maximum:
        ch2 = state.src[pos + 1]
        ch2_ord = ord(ch2)
        if ch2_ord >= 0xDC00 and ch2_ord <= 0xDFFF:
            escapedStr += ch2
            pos += 1

    origStr = "\\" + escapedStr

    if not silent:
        token = state.push("text_special", "", 0)
        token.content = escapedStr if ch1 in _ESCAPED else origStr
        token.markup = origStr
        token.info = "escape"

    state.pos = pos + 1
    return True


_ESCAPED = {
    "!",
    '"',
    "#",
    "$",
    "%",
    "&",
    "'",
    "(",
    ")",
    "*",
    "+",
    ",",
    "-",
    ".",
    "/",
    ":",
    ";",
    "<",
    "=",
    ">",
    "?",
    "@",
    "[",
    "\\",
    "]",
    "^",
    "_",
    "`",
    "{",
    "|",
    "}",
    "~",
}

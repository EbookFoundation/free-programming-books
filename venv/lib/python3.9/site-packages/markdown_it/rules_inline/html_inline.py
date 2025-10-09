# Process html tags
from ..common.html_re import HTML_TAG_RE
from ..common.utils import isLinkClose, isLinkOpen
from .state_inline import StateInline


def isLetter(ch: int) -> bool:
    lc = ch | 0x20  # to lower case
    # /* a */ and /* z */
    return (lc >= 0x61) and (lc <= 0x7A)


def html_inline(state: StateInline, silent: bool) -> bool:
    pos = state.pos

    if not state.md.options.get("html", None):
        return False

    # Check start
    maximum = state.posMax
    if state.src[pos] != "<" or pos + 2 >= maximum:
        return False

    # Quick fail on second char
    ch = state.src[pos + 1]
    if ch not in ("!", "?", "/") and not isLetter(ord(ch)):  # /* / */
        return False

    match = HTML_TAG_RE.search(state.src[pos:])
    if not match:
        return False

    if not silent:
        token = state.push("html_inline", "", 0)
        token.content = state.src[pos : pos + len(match.group(0))]

        if isLinkOpen(token.content):
            state.linkLevel += 1
        if isLinkClose(token.content):
            state.linkLevel -= 1

    state.pos += len(match.group(0))
    return True

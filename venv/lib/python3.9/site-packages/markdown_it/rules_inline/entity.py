# Process html entity - &#123;, &#xAF;, &quot;, ...
import re

from ..common.entities import entities
from ..common.utils import fromCodePoint, isValidEntityCode
from .state_inline import StateInline

DIGITAL_RE = re.compile(r"^&#((?:x[a-f0-9]{1,6}|[0-9]{1,7}));", re.IGNORECASE)
NAMED_RE = re.compile(r"^&([a-z][a-z0-9]{1,31});", re.IGNORECASE)


def entity(state: StateInline, silent: bool) -> bool:
    pos = state.pos
    maximum = state.posMax

    if state.src[pos] != "&":
        return False

    if pos + 1 >= maximum:
        return False

    if state.src[pos + 1] == "#":
        if match := DIGITAL_RE.search(state.src[pos:]):
            if not silent:
                match1 = match.group(1)
                code = (
                    int(match1[1:], 16) if match1[0].lower() == "x" else int(match1, 10)
                )

                token = state.push("text_special", "", 0)
                token.content = (
                    fromCodePoint(code)
                    if isValidEntityCode(code)
                    else fromCodePoint(0xFFFD)
                )
                token.markup = match.group(0)
                token.info = "entity"

            state.pos += len(match.group(0))
            return True

    else:
        if (match := NAMED_RE.search(state.src[pos:])) and match.group(1) in entities:
            if not silent:
                token = state.push("text_special", "", 0)
                token.content = entities[match.group(1)]
                token.markup = match.group(0)
                token.info = "entity"

            state.pos += len(match.group(0))
            return True

    return False

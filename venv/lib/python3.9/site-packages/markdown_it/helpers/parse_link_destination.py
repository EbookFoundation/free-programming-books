"""
Parse link destination
"""

from ..common.utils import charCodeAt, unescapeAll


class _Result:
    __slots__ = ("ok", "pos", "lines", "str")

    def __init__(self) -> None:
        self.ok = False
        self.pos = 0
        self.lines = 0
        self.str = ""


def parseLinkDestination(string: str, pos: int, maximum: int) -> _Result:
    lines = 0
    start = pos
    result = _Result()

    if charCodeAt(string, pos) == 0x3C:  # /* < */
        pos += 1
        while pos < maximum:
            code = charCodeAt(string, pos)
            if code == 0x0A:  # /* \n */)
                return result
            if code == 0x3C:  # / * < * /
                return result
            if code == 0x3E:  # /* > */) {
                result.pos = pos + 1
                result.str = unescapeAll(string[start + 1 : pos])
                result.ok = True
                return result

            if code == 0x5C and pos + 1 < maximum:  # \
                pos += 2
                continue

            pos += 1

        # no closing '>'
        return result

    # this should be ... } else { ... branch

    level = 0
    while pos < maximum:
        code = charCodeAt(string, pos)

        if code is None or code == 0x20:
            break

        # ascii control characters
        if code < 0x20 or code == 0x7F:
            break

        if code == 0x5C and pos + 1 < maximum:
            if charCodeAt(string, pos + 1) == 0x20:
                break
            pos += 2
            continue

        if code == 0x28:  # /* ( */)
            level += 1
            if level > 32:
                return result

        if code == 0x29:  # /* ) */)
            if level == 0:
                break
            level -= 1

        pos += 1

    if start == pos:
        return result
    if level != 0:
        return result

    result.str = unescapeAll(string[start:pos])
    result.lines = lines
    result.pos = pos
    result.ok = True
    return result

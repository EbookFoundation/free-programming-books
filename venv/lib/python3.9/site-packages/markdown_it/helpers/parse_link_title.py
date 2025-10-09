"""Parse link title
"""
from ..common.utils import charCodeAt, unescapeAll


class _Result:
    __slots__ = ("ok", "pos", "lines", "str")

    def __init__(self) -> None:
        self.ok = False
        self.pos = 0
        self.lines = 0
        self.str = ""

    def __str__(self) -> str:
        return self.str


def parseLinkTitle(string: str, pos: int, maximum: int) -> _Result:
    lines = 0
    start = pos
    result = _Result()

    if pos >= maximum:
        return result

    marker = charCodeAt(string, pos)

    # /* " */  /* ' */  /* ( */
    if marker != 0x22 and marker != 0x27 and marker != 0x28:
        return result

    pos += 1

    # if opening marker is "(", switch it to closing marker ")"
    if marker == 0x28:
        marker = 0x29

    while pos < maximum:
        code = charCodeAt(string, pos)
        if code == marker:
            title = string[start + 1 : pos]
            title = unescapeAll(title)
            result.pos = pos + 1
            result.lines = lines
            result.str = title
            result.ok = True
            return result
        elif code == 0x28 and marker == 0x29:  # /* ( */  /* ) */
            return result
        elif code == 0x0A:
            lines += 1
        elif code == 0x5C and pos + 1 < maximum:  # /* \ */
            pos += 1
            if charCodeAt(string, pos) == 0x0A:
                lines += 1

        pos += 1

    return result

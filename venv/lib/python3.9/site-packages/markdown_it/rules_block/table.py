# GFM table, https://github.github.com/gfm/#tables-extension-
from __future__ import annotations

import re

from ..common.utils import charStrAt, isStrSpace
from .state_block import StateBlock

headerLineRe = re.compile(r"^:?-+:?$")
enclosingPipesRe = re.compile(r"^\||\|$")


def getLine(state: StateBlock, line: int) -> str:
    pos = state.bMarks[line] + state.tShift[line]
    maximum = state.eMarks[line]

    # return state.src.substr(pos, max - pos)
    return state.src[pos:maximum]


def escapedSplit(string: str) -> list[str]:
    result: list[str] = []
    pos = 0
    max = len(string)
    isEscaped = False
    lastPos = 0
    current = ""
    ch = charStrAt(string, pos)

    while pos < max:
        if ch == "|":
            if not isEscaped:
                # pipe separating cells, '|'
                result.append(current + string[lastPos:pos])
                current = ""
                lastPos = pos + 1
            else:
                # escaped pipe, '\|'
                current += string[lastPos : pos - 1]
                lastPos = pos

        isEscaped = ch == "\\"
        pos += 1

        ch = charStrAt(string, pos)

    result.append(current + string[lastPos:])

    return result


def table(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    tbodyLines = None

    # should have at least two lines
    if startLine + 2 > endLine:
        return False

    nextLine = startLine + 1

    if state.sCount[nextLine] < state.blkIndent:
        return False

    if state.is_code_block(nextLine):
        return False

    # first character of the second line should be '|', '-', ':',
    # and no other characters are allowed but spaces;
    # basically, this is the equivalent of /^[-:|][-:|\s]*$/ regexp

    pos = state.bMarks[nextLine] + state.tShift[nextLine]
    if pos >= state.eMarks[nextLine]:
        return False
    first_ch = state.src[pos]
    pos += 1
    if first_ch not in ("|", "-", ":"):
        return False

    if pos >= state.eMarks[nextLine]:
        return False
    second_ch = state.src[pos]
    pos += 1
    if second_ch not in ("|", "-", ":") and not isStrSpace(second_ch):
        return False

    # if first character is '-', then second character must not be a space
    # (due to parsing ambiguity with list)
    if first_ch == "-" and isStrSpace(second_ch):
        return False

    while pos < state.eMarks[nextLine]:
        ch = state.src[pos]

        if ch not in ("|", "-", ":") and not isStrSpace(ch):
            return False

        pos += 1

    lineText = getLine(state, startLine + 1)

    columns = lineText.split("|")
    aligns = []
    for i in range(len(columns)):
        t = columns[i].strip()
        if not t:
            # allow empty columns before and after table, but not in between columns;
            # e.g. allow ` |---| `, disallow ` ---||--- `
            if i == 0 or i == len(columns) - 1:
                continue
            else:
                return False

        if not headerLineRe.search(t):
            return False
        if charStrAt(t, len(t) - 1) == ":":
            aligns.append("center" if charStrAt(t, 0) == ":" else "right")
        elif charStrAt(t, 0) == ":":
            aligns.append("left")
        else:
            aligns.append("")

    lineText = getLine(state, startLine).strip()
    if "|" not in lineText:
        return False
    if state.is_code_block(startLine):
        return False
    columns = escapedSplit(lineText)
    if columns and columns[0] == "":
        columns.pop(0)
    if columns and columns[-1] == "":
        columns.pop()

    # header row will define an amount of columns in the entire table,
    # and align row should be exactly the same (the rest of the rows can differ)
    columnCount = len(columns)
    if columnCount == 0 or columnCount != len(aligns):
        return False

    if silent:
        return True

    oldParentType = state.parentType
    state.parentType = "table"

    # use 'blockquote' lists for termination because it's
    # the most similar to tables
    terminatorRules = state.md.block.ruler.getRules("blockquote")

    token = state.push("table_open", "table", 1)
    token.map = tableLines = [startLine, 0]

    token = state.push("thead_open", "thead", 1)
    token.map = [startLine, startLine + 1]

    token = state.push("tr_open", "tr", 1)
    token.map = [startLine, startLine + 1]

    for i in range(len(columns)):
        token = state.push("th_open", "th", 1)
        if aligns[i]:
            token.attrs = {"style": "text-align:" + aligns[i]}

        token = state.push("inline", "", 0)
        # note in markdown-it this map was removed in v12.0.0 however, we keep it,
        # since it is helpful to propagate to children tokens
        token.map = [startLine, startLine + 1]
        token.content = columns[i].strip()
        token.children = []

        token = state.push("th_close", "th", -1)

    token = state.push("tr_close", "tr", -1)
    token = state.push("thead_close", "thead", -1)

    nextLine = startLine + 2
    while nextLine < endLine:
        if state.sCount[nextLine] < state.blkIndent:
            break

        terminate = False
        for i in range(len(terminatorRules)):
            if terminatorRules[i](state, nextLine, endLine, True):
                terminate = True
                break

        if terminate:
            break
        lineText = getLine(state, nextLine).strip()
        if not lineText:
            break
        if state.is_code_block(nextLine):
            break
        columns = escapedSplit(lineText)
        if columns and columns[0] == "":
            columns.pop(0)
        if columns and columns[-1] == "":
            columns.pop()

        if nextLine == startLine + 2:
            token = state.push("tbody_open", "tbody", 1)
            token.map = tbodyLines = [startLine + 2, 0]

        token = state.push("tr_open", "tr", 1)
        token.map = [nextLine, nextLine + 1]

        for i in range(columnCount):
            token = state.push("td_open", "td", 1)
            if aligns[i]:
                token.attrs = {"style": "text-align:" + aligns[i]}

            token = state.push("inline", "", 0)
            # note in markdown-it this map was removed in v12.0.0 however, we keep it,
            # since it is helpful to propagate to children tokens
            token.map = [nextLine, nextLine + 1]
            try:
                token.content = columns[i].strip() if columns[i] else ""
            except IndexError:
                token.content = ""
            token.children = []

            token = state.push("td_close", "td", -1)

        token = state.push("tr_close", "tr", -1)

        nextLine += 1

    if tbodyLines:
        token = state.push("tbody_close", "tbody", -1)
        tbodyLines[1] = nextLine

    token = state.push("table_close", "table", -1)

    tableLines[1] = nextLine
    state.parentType = oldParentType
    state.line = nextLine
    return True

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ..common.utils import isStrSpace
from ..ruler import StateBase
from ..token import Token
from ..utils import EnvType

if TYPE_CHECKING:
    from markdown_it.main import MarkdownIt


class StateBlock(StateBase):
    def __init__(
        self, src: str, md: MarkdownIt, env: EnvType, tokens: list[Token]
    ) -> None:
        self.src = src

        # link to parser instance
        self.md = md

        self.env = env

        #
        # Internal state variables
        #

        self.tokens = tokens

        self.bMarks: list[int] = []  # line begin offsets for fast jumps
        self.eMarks: list[int] = []  # line end offsets for fast jumps
        # offsets of the first non-space characters (tabs not expanded)
        self.tShift: list[int] = []
        self.sCount: list[int] = []  # indents for each line (tabs expanded)

        # An amount of virtual spaces (tabs expanded) between beginning
        # of each line (bMarks) and real beginning of that line.
        #
        # It exists only as a hack because blockquotes override bMarks
        # losing information in the process.
        #
        # It's used only when expanding tabs, you can think about it as
        # an initial tab length, e.g. bsCount=21 applied to string `\t123`
        # means first tab should be expanded to 4-21%4 === 3 spaces.
        #
        self.bsCount: list[int] = []

        # block parser variables
        self.blkIndent = 0  # required block content indent (for example, if we are
        # inside a list, it would be positioned after list marker)
        self.line = 0  # line index in src
        self.lineMax = 0  # lines count
        self.tight = False  # loose/tight mode for lists
        self.ddIndent = -1  # indent of the current dd block (-1 if there isn't any)
        self.listIndent = -1  # indent of the current list block (-1 if there isn't any)

        # can be 'blockquote', 'list', 'root', 'paragraph' or 'reference'
        # used in lists to determine if they interrupt a paragraph
        self.parentType = "root"

        self.level = 0

        # renderer
        self.result = ""

        # Create caches
        # Generate markers.
        indent_found = False

        start = pos = indent = offset = 0
        length = len(self.src)

        for pos, character in enumerate(self.src):
            if not indent_found:
                if isStrSpace(character):
                    indent += 1

                    if character == "\t":
                        offset += 4 - offset % 4
                    else:
                        offset += 1
                    continue
                else:
                    indent_found = True

            if character == "\n" or pos == length - 1:
                if character != "\n":
                    pos += 1
                self.bMarks.append(start)
                self.eMarks.append(pos)
                self.tShift.append(indent)
                self.sCount.append(offset)
                self.bsCount.append(0)

                indent_found = False
                indent = 0
                offset = 0
                start = pos + 1

        # Push fake entry to simplify cache bounds checks
        self.bMarks.append(length)
        self.eMarks.append(length)
        self.tShift.append(0)
        self.sCount.append(0)
        self.bsCount.append(0)

        self.lineMax = len(self.bMarks) - 1  # don't count last fake line

        # pre-check if code blocks are enabled, to speed up is_code_block method
        self._code_enabled = "code" in self.md["block"].ruler.get_active_rules()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(line={self.line},level={self.level},tokens={len(self.tokens)})"
        )

    def push(self, ttype: str, tag: str, nesting: Literal[-1, 0, 1]) -> Token:
        """Push new token to "stream"."""
        token = Token(ttype, tag, nesting)
        token.block = True
        if nesting < 0:
            self.level -= 1  # closing tag
        token.level = self.level
        if nesting > 0:
            self.level += 1  # opening tag
        self.tokens.append(token)
        return token

    def isEmpty(self, line: int) -> bool:
        """."""
        return (self.bMarks[line] + self.tShift[line]) >= self.eMarks[line]

    def skipEmptyLines(self, from_pos: int) -> int:
        """."""
        while from_pos < self.lineMax:
            try:
                if (self.bMarks[from_pos] + self.tShift[from_pos]) < self.eMarks[
                    from_pos
                ]:
                    break
            except IndexError:
                pass
            from_pos += 1
        return from_pos

    def skipSpaces(self, pos: int) -> int:
        """Skip spaces from given position."""
        while True:
            try:
                current = self.src[pos]
            except IndexError:
                break
            if not isStrSpace(current):
                break
            pos += 1
        return pos

    def skipSpacesBack(self, pos: int, minimum: int) -> int:
        """Skip spaces from given position in reverse."""
        if pos <= minimum:
            return pos
        while pos > minimum:
            pos -= 1
            if not isStrSpace(self.src[pos]):
                return pos + 1
        return pos

    def skipChars(self, pos: int, code: int) -> int:
        """Skip character code from given position."""
        while True:
            try:
                current = self.srcCharCode[pos]
            except IndexError:
                break
            if current != code:
                break
            pos += 1
        return pos

    def skipCharsStr(self, pos: int, ch: str) -> int:
        """Skip character string from given position."""
        while True:
            try:
                current = self.src[pos]
            except IndexError:
                break
            if current != ch:
                break
            pos += 1
        return pos

    def skipCharsBack(self, pos: int, code: int, minimum: int) -> int:
        """Skip character code reverse from given position - 1."""
        if pos <= minimum:
            return pos
        while pos > minimum:
            pos -= 1
            if code != self.srcCharCode[pos]:
                return pos + 1
        return pos

    def skipCharsStrBack(self, pos: int, ch: str, minimum: int) -> int:
        """Skip character string reverse from given position - 1."""
        if pos <= minimum:
            return pos
        while pos > minimum:
            pos -= 1
            if ch != self.src[pos]:
                return pos + 1
        return pos

    def getLines(self, begin: int, end: int, indent: int, keepLastLF: bool) -> str:
        """Cut lines range from source."""
        line = begin
        if begin >= end:
            return ""

        queue = [""] * (end - begin)

        i = 1
        while line < end:
            lineIndent = 0
            lineStart = first = self.bMarks[line]
            last = (
                self.eMarks[line] + 1
                if line + 1 < end or keepLastLF
                else self.eMarks[line]
            )

            while (first < last) and (lineIndent < indent):
                ch = self.src[first]
                if isStrSpace(ch):
                    if ch == "\t":
                        lineIndent += 4 - (lineIndent + self.bsCount[line]) % 4
                    else:
                        lineIndent += 1
                elif first - lineStart < self.tShift[line]:
                    lineIndent += 1
                else:
                    break
                first += 1

            if lineIndent > indent:
                # partially expanding tabs in code blocks, e.g '\t\tfoobar'
                # with indent=2 becomes '  \tfoobar'
                queue[i - 1] = (" " * (lineIndent - indent)) + self.src[first:last]
            else:
                queue[i - 1] = self.src[first:last]

            line += 1
            i += 1

        return "".join(queue)

    def is_code_block(self, line: int) -> bool:
        """Check if line is a code block,
        i.e. the code block rule is enabled and text is indented by more than 3 spaces.
        """
        return self._code_enabled and (self.sCount[line] - self.blkIndent) >= 4

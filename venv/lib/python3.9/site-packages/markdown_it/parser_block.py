"""Block-level tokenizer."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from . import rules_block
from .ruler import Ruler
from .rules_block.state_block import StateBlock
from .token import Token
from .utils import EnvType

if TYPE_CHECKING:
    from markdown_it import MarkdownIt

LOGGER = logging.getLogger(__name__)


RuleFuncBlockType = Callable[[StateBlock, int, int, bool], bool]
"""(state: StateBlock, startLine: int, endLine: int, silent: bool) -> matched: bool)

`silent` disables token generation, useful for lookahead.
"""

_rules: list[tuple[str, RuleFuncBlockType, list[str]]] = [
    # First 2 params - rule name & source. Secondary array - list of rules,
    # which can be terminated by this one.
    ("table", rules_block.table, ["paragraph", "reference"]),
    ("code", rules_block.code, []),
    ("fence", rules_block.fence, ["paragraph", "reference", "blockquote", "list"]),
    (
        "blockquote",
        rules_block.blockquote,
        ["paragraph", "reference", "blockquote", "list"],
    ),
    ("hr", rules_block.hr, ["paragraph", "reference", "blockquote", "list"]),
    ("list", rules_block.list_block, ["paragraph", "reference", "blockquote"]),
    ("reference", rules_block.reference, []),
    ("html_block", rules_block.html_block, ["paragraph", "reference", "blockquote"]),
    ("heading", rules_block.heading, ["paragraph", "reference", "blockquote"]),
    ("lheading", rules_block.lheading, []),
    ("paragraph", rules_block.paragraph, []),
]


class ParserBlock:
    """
    ParserBlock#ruler -> Ruler

    [[Ruler]] instance. Keep configuration of block rules.
    """

    def __init__(self) -> None:
        self.ruler = Ruler[RuleFuncBlockType]()
        for name, rule, alt in _rules:
            self.ruler.push(name, rule, {"alt": alt})

    def tokenize(self, state: StateBlock, startLine: int, endLine: int) -> None:
        """Generate tokens for input range."""
        rules = self.ruler.getRules("")
        line = startLine
        maxNesting = state.md.options.maxNesting
        hasEmptyLines = False

        while line < endLine:
            state.line = line = state.skipEmptyLines(line)
            if line >= endLine:
                break
            if state.sCount[line] < state.blkIndent:
                # Termination condition for nested calls.
                # Nested calls currently used for blockquotes & lists
                break
            if state.level >= maxNesting:
                # If nesting level exceeded - skip tail to the end.
                # That's not ordinary situation and we should not care about content.
                state.line = endLine
                break

            # Try all possible rules.
            # On success, rule should:
            # - update `state.line`
            # - update `state.tokens`
            # - return True
            for rule in rules:
                if rule(state, line, endLine, False):
                    break

            # set state.tight if we had an empty line before current tag
            # i.e. latest empty line should not count
            state.tight = not hasEmptyLines

            line = state.line

            # paragraph might "eat" one newline after it in nested lists
            if (line - 1) < endLine and state.isEmpty(line - 1):
                hasEmptyLines = True

            if line < endLine and state.isEmpty(line):
                hasEmptyLines = True
                line += 1
                state.line = line

    def parse(
        self, src: str, md: MarkdownIt, env: EnvType, outTokens: list[Token]
    ) -> list[Token] | None:
        """Process input string and push block tokens into `outTokens`."""
        if not src:
            return None
        state = StateBlock(src, md, env, outTokens)
        self.tokenize(state, state.line, state.lineMax)
        return state.tokens

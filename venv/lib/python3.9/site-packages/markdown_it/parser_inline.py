"""Tokenizes paragraph content.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from . import rules_inline
from .ruler import Ruler
from .rules_inline.state_inline import StateInline
from .token import Token
from .utils import EnvType

if TYPE_CHECKING:
    from markdown_it import MarkdownIt


# Parser rules
RuleFuncInlineType = Callable[[StateInline, bool], bool]
"""(state: StateInline, silent: bool) -> matched: bool)

`silent` disables token generation, useful for lookahead.
"""
_rules: list[tuple[str, RuleFuncInlineType]] = [
    ("text", rules_inline.text),
    ("linkify", rules_inline.linkify),
    ("newline", rules_inline.newline),
    ("escape", rules_inline.escape),
    ("backticks", rules_inline.backtick),
    ("strikethrough", rules_inline.strikethrough.tokenize),
    ("emphasis", rules_inline.emphasis.tokenize),
    ("link", rules_inline.link),
    ("image", rules_inline.image),
    ("autolink", rules_inline.autolink),
    ("html_inline", rules_inline.html_inline),
    ("entity", rules_inline.entity),
]

# Note `rule2` ruleset was created specifically for emphasis/strikethrough
# post-processing and may be changed in the future.
#
# Don't use this for anything except pairs (plugins working with `balance_pairs`).
#
RuleFuncInline2Type = Callable[[StateInline], None]
_rules2: list[tuple[str, RuleFuncInline2Type]] = [
    ("balance_pairs", rules_inline.link_pairs),
    ("strikethrough", rules_inline.strikethrough.postProcess),
    ("emphasis", rules_inline.emphasis.postProcess),
    # rules for pairs separate '**' into its own text tokens, which may be left unused,
    # rule below merges unused segments back with the rest of the text
    ("fragments_join", rules_inline.fragments_join),
]


class ParserInline:
    def __init__(self) -> None:
        self.ruler = Ruler[RuleFuncInlineType]()
        for name, rule in _rules:
            self.ruler.push(name, rule)
        # Second ruler used for post-processing (e.g. in emphasis-like rules)
        self.ruler2 = Ruler[RuleFuncInline2Type]()
        for name, rule2 in _rules2:
            self.ruler2.push(name, rule2)

    def skipToken(self, state: StateInline) -> None:
        """Skip single token by running all rules in validation mode;
        returns `True` if any rule reported success
        """
        ok = False
        pos = state.pos
        rules = self.ruler.getRules("")
        maxNesting = state.md.options["maxNesting"]
        cache = state.cache

        if pos in cache:
            state.pos = cache[pos]
            return

        if state.level < maxNesting:
            for rule in rules:
                #  Increment state.level and decrement it later to limit recursion.
                # It's harmless to do here, because no tokens are created.
                # But ideally, we'd need a separate private state variable for this purpose.
                state.level += 1
                ok = rule(state, True)
                state.level -= 1
                if ok:
                    break
        else:
            # Too much nesting, just skip until the end of the paragraph.
            #
            # NOTE: this will cause links to behave incorrectly in the following case,
            #       when an amount of `[` is exactly equal to `maxNesting + 1`:
            #
            #       [[[[[[[[[[[[[[[[[[[[[foo]()
            #
            # TODO: remove this workaround when CM standard will allow nested links
            #       (we can replace it by preventing links from being parsed in
            #       validation mode)
            #
            state.pos = state.posMax

        if not ok:
            state.pos += 1
        cache[pos] = state.pos

    def tokenize(self, state: StateInline) -> None:
        """Generate tokens for input range."""
        ok = False
        rules = self.ruler.getRules("")
        end = state.posMax
        maxNesting = state.md.options["maxNesting"]

        while state.pos < end:
            # Try all possible rules.
            # On success, rule should:
            #
            # - update `state.pos`
            # - update `state.tokens`
            # - return true

            if state.level < maxNesting:
                for rule in rules:
                    ok = rule(state, False)
                    if ok:
                        break

            if ok:
                if state.pos >= end:
                    break
                continue

            state.pending += state.src[state.pos]
            state.pos += 1

        if state.pending:
            state.pushPending()

    def parse(
        self, src: str, md: MarkdownIt, env: EnvType, tokens: list[Token]
    ) -> list[Token]:
        """Process input string and push inline tokens into `tokens`"""
        state = StateInline(src, md, env, tokens)
        self.tokenize(state)
        rules2 = self.ruler2.getRules("")
        for rule in rules2:
            rule(state)
        return state.tokens

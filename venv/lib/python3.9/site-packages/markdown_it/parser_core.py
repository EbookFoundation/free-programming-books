"""
 * class Core
 *
 * Top-level rules executor. Glues block/inline parsers and does intermediate
 * transformations.
"""
from __future__ import annotations

from typing import Callable

from .ruler import Ruler
from .rules_core import (
    block,
    inline,
    linkify,
    normalize,
    replace,
    smartquotes,
    text_join,
)
from .rules_core.state_core import StateCore

RuleFuncCoreType = Callable[[StateCore], None]

_rules: list[tuple[str, RuleFuncCoreType]] = [
    ("normalize", normalize),
    ("block", block),
    ("inline", inline),
    ("linkify", linkify),
    ("replacements", replace),
    ("smartquotes", smartquotes),
    ("text_join", text_join),
]


class ParserCore:
    def __init__(self) -> None:
        self.ruler = Ruler[RuleFuncCoreType]()
        for name, rule in _rules:
            self.ruler.push(name, rule)

    def process(self, state: StateCore) -> None:
        """Executes core chain rules."""
        for rule in self.ruler.getRules(""):
            rule(state)

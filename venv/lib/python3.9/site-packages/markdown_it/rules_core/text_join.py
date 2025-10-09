"""Join raw text tokens with the rest of the text

This is set as a separate rule to provide an opportunity for plugins
to run text replacements after text join, but before escape join.

For example, `\\:)` shouldn't be replaced with an emoji.
"""
from __future__ import annotations

from ..token import Token
from .state_core import StateCore


def text_join(state: StateCore) -> None:
    """Join raw text for escape sequences (`text_special`) tokens with the rest of the text"""

    for inline_token in state.tokens[:]:
        if inline_token.type != "inline":
            continue

        # convert text_special to text and join all adjacent text nodes
        new_tokens: list[Token] = []
        for child_token in inline_token.children or []:
            if child_token.type == "text_special":
                child_token.type = "text"
            if (
                child_token.type == "text"
                and new_tokens
                and new_tokens[-1].type == "text"
            ):
                new_tokens[-1].content += child_token.content
            else:
                new_tokens.append(child_token)
        inline_token.children = new_tokens

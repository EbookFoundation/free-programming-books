from ..token import Token
from .state_core import StateCore


def block(state: StateCore) -> None:
    if state.inlineMode:
        token = Token("inline", "", 0)
        token.content = state.src
        token.map = [0, 1]
        token.children = []
        state.tokens.append(token)
    else:
        state.md.block.parse(state.src, state.md, state.env, state.tokens)

from .state_inline import StateInline


def fragments_join(state: StateInline) -> None:
    """
    Clean up tokens after emphasis and strikethrough postprocessing:
    merge adjacent text nodes into one and re-calculate all token levels

    This is necessary because initially emphasis delimiter markers (``*, _, ~``)
    are treated as their own separate text tokens. Then emphasis rule either
    leaves them as text (needed to merge with adjacent text) or turns them
    into opening/closing tags (which messes up levels inside).
    """
    level = 0
    maximum = len(state.tokens)

    curr = last = 0
    while curr < maximum:
        # re-calculate levels after emphasis/strikethrough turns some text nodes
        # into opening/closing tags
        if state.tokens[curr].nesting < 0:
            level -= 1  # closing tag
        state.tokens[curr].level = level
        if state.tokens[curr].nesting > 0:
            level += 1  # opening tag

        if (
            state.tokens[curr].type == "text"
            and curr + 1 < maximum
            and state.tokens[curr + 1].type == "text"
        ):
            # collapse two adjacent text nodes
            state.tokens[curr + 1].content = (
                state.tokens[curr].content + state.tokens[curr + 1].content
            )
        else:
            if curr != last:
                state.tokens[last] = state.tokens[curr]
            last += 1
        curr += 1

    if curr != last:
        del state.tokens[last:]

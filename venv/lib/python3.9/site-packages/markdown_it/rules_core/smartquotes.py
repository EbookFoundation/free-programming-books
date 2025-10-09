"""Convert straight quotation marks to typographic ones
"""
from __future__ import annotations

import re
from typing import Any

from ..common.utils import charCodeAt, isMdAsciiPunct, isPunctChar, isWhiteSpace
from ..token import Token
from .state_core import StateCore

QUOTE_TEST_RE = re.compile(r"['\"]")
QUOTE_RE = re.compile(r"['\"]")
APOSTROPHE = "\u2019"  # ’


def replaceAt(string: str, index: int, ch: str) -> str:
    # When the index is negative, the behavior is different from the js version.
    # But basically, the index will not be negative.
    assert index >= 0
    return string[:index] + ch + string[index + 1 :]


def process_inlines(tokens: list[Token], state: StateCore) -> None:
    stack: list[dict[str, Any]] = []

    for i, token in enumerate(tokens):
        thisLevel = token.level

        j = 0
        for j in range(len(stack))[::-1]:
            if stack[j]["level"] <= thisLevel:
                break
        else:
            # When the loop is terminated without a "break".
            # Subtract 1 to get the same index as the js version.
            j -= 1

        stack = stack[: j + 1]

        if token.type != "text":
            continue

        text = token.content
        pos = 0
        maximum = len(text)

        while pos < maximum:
            goto_outer = False
            lastIndex = pos
            t = QUOTE_RE.search(text[lastIndex:])
            if not t:
                break

            canOpen = canClose = True
            pos = t.start(0) + lastIndex + 1
            isSingle = t.group(0) == "'"

            # Find previous character,
            # default to space if it's the beginning of the line
            lastChar: None | int = 0x20

            if t.start(0) + lastIndex - 1 >= 0:
                lastChar = charCodeAt(text, t.start(0) + lastIndex - 1)
            else:
                for j in range(i)[::-1]:
                    if tokens[j].type == "softbreak" or tokens[j].type == "hardbreak":
                        break
                    # should skip all tokens except 'text', 'html_inline' or 'code_inline'
                    if not tokens[j].content:
                        continue

                    lastChar = charCodeAt(tokens[j].content, len(tokens[j].content) - 1)
                    break

            # Find next character,
            # default to space if it's the end of the line
            nextChar: None | int = 0x20

            if pos < maximum:
                nextChar = charCodeAt(text, pos)
            else:
                for j in range(i + 1, len(tokens)):
                    # nextChar defaults to 0x20
                    if tokens[j].type == "softbreak" or tokens[j].type == "hardbreak":
                        break
                    # should skip all tokens except 'text', 'html_inline' or 'code_inline'
                    if not tokens[j].content:
                        continue

                    nextChar = charCodeAt(tokens[j].content, 0)
                    break

            isLastPunctChar = lastChar is not None and (
                isMdAsciiPunct(lastChar) or isPunctChar(chr(lastChar))
            )
            isNextPunctChar = nextChar is not None and (
                isMdAsciiPunct(nextChar) or isPunctChar(chr(nextChar))
            )

            isLastWhiteSpace = lastChar is not None and isWhiteSpace(lastChar)
            isNextWhiteSpace = nextChar is not None and isWhiteSpace(nextChar)

            if isNextWhiteSpace:  # noqa: SIM114
                canOpen = False
            elif isNextPunctChar and not (isLastWhiteSpace or isLastPunctChar):
                canOpen = False

            if isLastWhiteSpace:  # noqa: SIM114
                canClose = False
            elif isLastPunctChar and not (isNextWhiteSpace or isNextPunctChar):
                canClose = False

            if nextChar == 0x22 and t.group(0) == '"':  # 0x22: "  # noqa: SIM102
                if (
                    lastChar is not None and lastChar >= 0x30 and lastChar <= 0x39
                ):  # 0x30: 0, 0x39: 9
                    # special case: 1"" - count first quote as an inch
                    canClose = canOpen = False

            if canOpen and canClose:
                # Replace quotes in the middle of punctuation sequence, but not
                # in the middle of the words, i.e.:
                #
                # 1. foo " bar " baz - not replaced
                # 2. foo-"-bar-"-baz - replaced
                # 3. foo"bar"baz     - not replaced
                canOpen = isLastPunctChar
                canClose = isNextPunctChar

            if not canOpen and not canClose:
                # middle of word
                if isSingle:
                    token.content = replaceAt(
                        token.content, t.start(0) + lastIndex, APOSTROPHE
                    )
                continue

            if canClose:
                # this could be a closing quote, rewind the stack to get a match
                for j in range(len(stack))[::-1]:
                    item = stack[j]
                    if stack[j]["level"] < thisLevel:
                        break
                    if item["single"] == isSingle and stack[j]["level"] == thisLevel:
                        item = stack[j]

                        if isSingle:
                            openQuote = state.md.options.quotes[2]
                            closeQuote = state.md.options.quotes[3]
                        else:
                            openQuote = state.md.options.quotes[0]
                            closeQuote = state.md.options.quotes[1]

                        # replace token.content *before* tokens[item.token].content,
                        # because, if they are pointing at the same token, replaceAt
                        # could mess up indices when quote length != 1
                        token.content = replaceAt(
                            token.content, t.start(0) + lastIndex, closeQuote
                        )
                        tokens[item["token"]].content = replaceAt(
                            tokens[item["token"]].content, item["pos"], openQuote
                        )

                        pos += len(closeQuote) - 1
                        if item["token"] == i:
                            pos += len(openQuote) - 1

                        text = token.content
                        maximum = len(text)

                        stack = stack[:j]
                        goto_outer = True
                        break
                if goto_outer:
                    goto_outer = False
                    continue

            if canOpen:
                stack.append(
                    {
                        "token": i,
                        "pos": t.start(0) + lastIndex,
                        "single": isSingle,
                        "level": thisLevel,
                    }
                )
            elif canClose and isSingle:
                token.content = replaceAt(
                    token.content, t.start(0) + lastIndex, APOSTROPHE
                )


def smartquotes(state: StateCore) -> None:
    if not state.md.options.typographer:
        return

    for token in state.tokens:
        if token.type != "inline" or not QUOTE_RE.search(token.content):
            continue
        if token.children is not None:
            process_inlines(token.children, state)

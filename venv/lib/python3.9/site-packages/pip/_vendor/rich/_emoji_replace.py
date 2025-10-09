from typing import Callable, Match, Optional
import re

from ._emoji_codes import EMOJI


_ReStringMatch = Match[str]  # regex match object
_ReSubCallable = Callable[[_ReStringMatch], str]  # Callable invoked by re.sub
_EmojiSubMethod = Callable[[_ReSubCallable, str], str]  # Sub method of a compiled re


def _emoji_replace(
    text: str,
    default_variant: Optional[str] = None,
    _emoji_sub: _EmojiSubMethod = re.compile(r"(:(\S*?)(?:(?:\-)(emoji|text))?:)").sub,
) -> str:
    """Replace emoji code in text."""
    get_emoji = EMOJI.__getitem__
    variants = {"text": "\uFE0E", "emoji": "\uFE0F"}
    get_variant = variants.get
    default_variant_code = variants.get(default_variant, "") if default_variant else ""

    def do_replace(match: Match[str]) -> str:
        emoji_code, emoji_name, variant = match.groups()
        try:
            return get_emoji(emoji_name.lower()) + get_variant(
                variant, default_variant_code
            )
        except KeyError:
            return emoji_code

    return _emoji_sub(do_replace, text)

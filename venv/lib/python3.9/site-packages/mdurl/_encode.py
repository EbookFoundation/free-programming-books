from __future__ import annotations

from collections.abc import Sequence
from string import ascii_letters, digits, hexdigits
from urllib.parse import quote as encode_uri_component

ASCII_LETTERS_AND_DIGITS = ascii_letters + digits

ENCODE_DEFAULT_CHARS = ";/?:@&=+$,-_.!~*'()#"
ENCODE_COMPONENT_CHARS = "-_.!~*'()"

encode_cache: dict[str, list[str]] = {}


# Create a lookup array where anything but characters in `chars` string
# and alphanumeric chars is percent-encoded.
def get_encode_cache(exclude: str) -> Sequence[str]:
    if exclude in encode_cache:
        return encode_cache[exclude]

    cache: list[str] = []
    encode_cache[exclude] = cache

    for i in range(128):
        ch = chr(i)

        if ch in ASCII_LETTERS_AND_DIGITS:
            # always allow unencoded alphanumeric characters
            cache.append(ch)
        else:
            cache.append("%" + ("0" + hex(i)[2:].upper())[-2:])

    for i in range(len(exclude)):
        cache[ord(exclude[i])] = exclude[i]

    return cache


# Encode unsafe characters with percent-encoding, skipping already
# encoded sequences.
#
#  - string       - string to encode
#  - exclude      - list of characters to ignore (in addition to a-zA-Z0-9)
#  - keepEscaped  - don't encode '%' in a correct escape sequence (default: true)
def encode(
    string: str, exclude: str = ENCODE_DEFAULT_CHARS, *, keep_escaped: bool = True
) -> str:
    result = ""

    cache = get_encode_cache(exclude)

    l = len(string)  # noqa: E741
    i = 0
    while i < l:
        code = ord(string[i])

        #                              %
        if keep_escaped and code == 0x25 and i + 2 < l:
            if all(c in hexdigits for c in string[i + 1 : i + 3]):
                result += string[i : i + 3]
                i += 2
                i += 1  # JS for loop statement3
                continue

        if code < 128:
            result += cache[code]
            i += 1  # JS for loop statement3
            continue

        if code >= 0xD800 and code <= 0xDFFF:
            if code >= 0xD800 and code <= 0xDBFF and i + 1 < l:
                next_code = ord(string[i + 1])
                if next_code >= 0xDC00 and next_code <= 0xDFFF:
                    result += encode_uri_component(string[i] + string[i + 1])
                    i += 1
                    i += 1  # JS for loop statement3
                    continue
            result += "%EF%BF%BD"
            i += 1  # JS for loop statement3
            continue

        result += encode_uri_component(string[i])
        i += 1  # JS for loop statement3

    return result

# Copyright 2014 Mathias Bynens <https://mathiasbynens.be/>
# Copyright 2021 Taneli Hukkinen
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import codecs
import re
from typing import Callable

REGEX_SEPARATORS = re.compile(r"[\x2E\u3002\uFF0E\uFF61]")
REGEX_NON_ASCII = re.compile(r"[^\0-\x7E]")


def encode(uni: str) -> str:
    return codecs.encode(uni, encoding="punycode").decode()


def decode(ascii: str) -> str:
    return codecs.decode(ascii, encoding="punycode")  # type: ignore


def map_domain(string: str, fn: Callable[[str], str]) -> str:
    parts = string.split("@")
    result = ""
    if len(parts) > 1:
        # In email addresses, only the domain name should be punycoded. Leave
        # the local part (i.e. everything up to `@`) intact.
        result = parts[0] + "@"
        string = parts[1]
    labels = REGEX_SEPARATORS.split(string)
    encoded = ".".join(fn(label) for label in labels)
    return result + encoded


def to_unicode(obj: str) -> str:
    def mapping(obj: str) -> str:
        if obj.startswith("xn--"):
            return decode(obj[4:].lower())
        return obj

    return map_domain(obj, mapping)


def to_ascii(obj: str) -> str:
    def mapping(obj: str) -> str:
        if REGEX_NON_ASCII.search(obj):
            return "xn--" + encode(obj)
        return obj

    return map_domain(obj, mapping)

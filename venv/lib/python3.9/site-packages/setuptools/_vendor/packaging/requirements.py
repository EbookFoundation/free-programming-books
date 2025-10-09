# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.
from __future__ import absolute_import, division, print_function

import string
import re

from setuptools.extern.pyparsing import stringStart, stringEnd, originalTextFor, ParseException
from setuptools.extern.pyparsing import ZeroOrMore, Word, Optional, Regex, Combine
from setuptools.extern.pyparsing import Literal as L  # noqa
from urllib import parse as urlparse

from ._typing import TYPE_CHECKING
from .markers import MARKER_EXPR, Marker
from .specifiers import LegacySpecifier, Specifier, SpecifierSet

if TYPE_CHECKING:  # pragma: no cover
    from typing import List


class InvalidRequirement(ValueError):
    """
    An invalid requirement was found, users should refer to PEP 508.
    """


ALPHANUM = Word(string.ascii_letters + string.digits)

LBRACKET = L("[").suppress()
RBRACKET = L("]").suppress()
LPAREN = L("(").suppress()
RPAREN = L(")").suppress()
COMMA = L(",").suppress()
SEMICOLON = L(";").suppress()
AT = L("@").suppress()

PUNCTUATION = Word("-_.")
IDENTIFIER_END = ALPHANUM | (ZeroOrMore(PUNCTUATION) + ALPHANUM)
IDENTIFIER = Combine(ALPHANUM + ZeroOrMore(IDENTIFIER_END))

NAME = IDENTIFIER("name")
EXTRA = IDENTIFIER

URI = Regex(r"[^ ]+")("url")
URL = AT + URI

EXTRAS_LIST = EXTRA + ZeroOrMore(COMMA + EXTRA)
EXTRAS = (LBRACKET + Optional(EXTRAS_LIST) + RBRACKET)("extras")

VERSION_PEP440 = Regex(Specifier._regex_str, re.VERBOSE | re.IGNORECASE)
VERSION_LEGACY = Regex(LegacySpecifier._regex_str, re.VERBOSE | re.IGNORECASE)

VERSION_ONE = VERSION_PEP440 ^ VERSION_LEGACY
VERSION_MANY = Combine(
    VERSION_ONE + ZeroOrMore(COMMA + VERSION_ONE), joinString=",", adjacent=False
)("_raw_spec")
_VERSION_SPEC = Optional(((LPAREN + VERSION_MANY + RPAREN) | VERSION_MANY))
_VERSION_SPEC.setParseAction(lambda s, l, t: t._raw_spec or "")

VERSION_SPEC = originalTextFor(_VERSION_SPEC)("specifier")
VERSION_SPEC.setParseAction(lambda s, l, t: t[1])

MARKER_EXPR = originalTextFor(MARKER_EXPR())("marker")
MARKER_EXPR.setParseAction(
    lambda s, l, t: Marker(s[t._original_start : t._original_end])
)
MARKER_SEPARATOR = SEMICOLON
MARKER = MARKER_SEPARATOR + MARKER_EXPR

VERSION_AND_MARKER = VERSION_SPEC + Optional(MARKER)
URL_AND_MARKER = URL + Optional(MARKER)

NAMED_REQUIREMENT = NAME + Optional(EXTRAS) + (URL_AND_MARKER | VERSION_AND_MARKER)

REQUIREMENT = stringStart + NAMED_REQUIREMENT + stringEnd
# setuptools.extern.pyparsing isn't thread safe during initialization, so we do it eagerly, see
# issue #104
REQUIREMENT.parseString("x[]")


class Requirement(object):
    """Parse a requirement.

    Parse a given requirement string into its parts, such as name, specifier,
    URL, and extras. Raises InvalidRequirement on a badly-formed requirement
    string.
    """

    # TODO: Can we test whether something is contained within a requirement?
    #       If so how do we do that? Do we need to test against the _name_ of
    #       the thing as well as the version? What about the markers?
    # TODO: Can we normalize the name and extra name?

    def __init__(self, requirement_string):
        # type: (str) -> None
        try:
            req = REQUIREMENT.parseString(requirement_string)
        except ParseException as e:
            raise InvalidRequirement(
                'Parse error at "{0!r}": {1}'.format(
                    requirement_string[e.loc : e.loc + 8], e.msg
                )
            )

        self.name = req.name
        if req.url:
            parsed_url = urlparse.urlparse(req.url)
            if parsed_url.scheme == "file":
                if urlparse.urlunparse(parsed_url) != req.url:
                    raise InvalidRequirement("Invalid URL given")
            elif not (parsed_url.scheme and parsed_url.netloc) or (
                not parsed_url.scheme and not parsed_url.netloc
            ):
                raise InvalidRequirement("Invalid URL: {0}".format(req.url))
            self.url = req.url
        else:
            self.url = None
        self.extras = set(req.extras.asList() if req.extras else [])
        self.specifier = SpecifierSet(req.specifier)
        self.marker = req.marker if req.marker else None

    def __str__(self):
        # type: () -> str
        parts = [self.name]  # type: List[str]

        if self.extras:
            parts.append("[{0}]".format(",".join(sorted(self.extras))))

        if self.specifier:
            parts.append(str(self.specifier))

        if self.url:
            parts.append("@ {0}".format(self.url))
            if self.marker:
                parts.append(" ")

        if self.marker:
            parts.append("; {0}".format(self.marker))

        return "".join(parts)

    def __repr__(self):
        # type: () -> str
        return "<Requirement({0!r})>".format(str(self))

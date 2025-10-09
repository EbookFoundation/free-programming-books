# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.
from __future__ import absolute_import, division, print_function

import collections
import itertools
import re

from ._structures import Infinity, NegativeInfinity
from ._typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from typing import Callable, Iterator, List, Optional, SupportsInt, Tuple, Union

    from ._structures import InfinityType, NegativeInfinityType

    InfiniteTypes = Union[InfinityType, NegativeInfinityType]
    PrePostDevType = Union[InfiniteTypes, Tuple[str, int]]
    SubLocalType = Union[InfiniteTypes, int, str]
    LocalType = Union[
        NegativeInfinityType,
        Tuple[
            Union[
                SubLocalType,
                Tuple[SubLocalType, str],
                Tuple[NegativeInfinityType, SubLocalType],
            ],
            ...,
        ],
    ]
    CmpKey = Tuple[
        int, Tuple[int, ...], PrePostDevType, PrePostDevType, PrePostDevType, LocalType
    ]
    LegacyCmpKey = Tuple[int, Tuple[str, ...]]
    VersionComparisonMethod = Callable[
        [Union[CmpKey, LegacyCmpKey], Union[CmpKey, LegacyCmpKey]], bool
    ]

__all__ = ["parse", "Version", "LegacyVersion", "InvalidVersion", "VERSION_PATTERN"]


_Version = collections.namedtuple(
    "_Version", ["epoch", "release", "dev", "pre", "post", "local"]
)


def parse(version):
    # type: (str) -> Union[LegacyVersion, Version]
    """
    Parse the given version string and return either a :class:`Version` object
    or a :class:`LegacyVersion` object depending on if the given version is
    a valid PEP 440 version or a legacy version.
    """
    try:
        return Version(version)
    except InvalidVersion:
        return LegacyVersion(version)


class InvalidVersion(ValueError):
    """
    An invalid version was found, users should refer to PEP 440.
    """


class _BaseVersion(object):
    _key = None  # type: Union[CmpKey, LegacyCmpKey]

    def __hash__(self):
        # type: () -> int
        return hash(self._key)

    def __lt__(self, other):
        # type: (_BaseVersion) -> bool
        return self._compare(other, lambda s, o: s < o)

    def __le__(self, other):
        # type: (_BaseVersion) -> bool
        return self._compare(other, lambda s, o: s <= o)

    def __eq__(self, other):
        # type: (object) -> bool
        return self._compare(other, lambda s, o: s == o)

    def __ge__(self, other):
        # type: (_BaseVersion) -> bool
        return self._compare(other, lambda s, o: s >= o)

    def __gt__(self, other):
        # type: (_BaseVersion) -> bool
        return self._compare(other, lambda s, o: s > o)

    def __ne__(self, other):
        # type: (object) -> bool
        return self._compare(other, lambda s, o: s != o)

    def _compare(self, other, method):
        # type: (object, VersionComparisonMethod) -> Union[bool, NotImplemented]
        if not isinstance(other, _BaseVersion):
            return NotImplemented

        return method(self._key, other._key)


class LegacyVersion(_BaseVersion):
    def __init__(self, version):
        # type: (str) -> None
        self._version = str(version)
        self._key = _legacy_cmpkey(self._version)

    def __str__(self):
        # type: () -> str
        return self._version

    def __repr__(self):
        # type: () -> str
        return "<LegacyVersion({0})>".format(repr(str(self)))

    @property
    def public(self):
        # type: () -> str
        return self._version

    @property
    def base_version(self):
        # type: () -> str
        return self._version

    @property
    def epoch(self):
        # type: () -> int
        return -1

    @property
    def release(self):
        # type: () -> None
        return None

    @property
    def pre(self):
        # type: () -> None
        return None

    @property
    def post(self):
        # type: () -> None
        return None

    @property
    def dev(self):
        # type: () -> None
        return None

    @property
    def local(self):
        # type: () -> None
        return None

    @property
    def is_prerelease(self):
        # type: () -> bool
        return False

    @property
    def is_postrelease(self):
        # type: () -> bool
        return False

    @property
    def is_devrelease(self):
        # type: () -> bool
        return False


_legacy_version_component_re = re.compile(r"(\d+ | [a-z]+ | \.| -)", re.VERBOSE)

_legacy_version_replacement_map = {
    "pre": "c",
    "preview": "c",
    "-": "final-",
    "rc": "c",
    "dev": "@",
}


def _parse_version_parts(s):
    # type: (str) -> Iterator[str]
    for part in _legacy_version_component_re.split(s):
        part = _legacy_version_replacement_map.get(part, part)

        if not part or part == ".":
            continue

        if part[:1] in "0123456789":
            # pad for numeric comparison
            yield part.zfill(8)
        else:
            yield "*" + part

    # ensure that alpha/beta/candidate are before final
    yield "*final"


def _legacy_cmpkey(version):
    # type: (str) -> LegacyCmpKey

    # We hardcode an epoch of -1 here. A PEP 440 version can only have a epoch
    # greater than or equal to 0. This will effectively put the LegacyVersion,
    # which uses the defacto standard originally implemented by setuptools,
    # as before all PEP 440 versions.
    epoch = -1

    # This scheme is taken from pkg_resources.parse_version setuptools prior to
    # it's adoption of the packaging library.
    parts = []  # type: List[str]
    for part in _parse_version_parts(version.lower()):
        if part.startswith("*"):
            # remove "-" before a prerelease tag
            if part < "*final":
                while parts and parts[-1] == "*final-":
                    parts.pop()

            # remove trailing zeros from each series of numeric parts
            while parts and parts[-1] == "00000000":
                parts.pop()

        parts.append(part)

    return epoch, tuple(parts)


# Deliberately not anchored to the start and end of the string, to make it
# easier for 3rd party code to reuse
VERSION_PATTERN = r"""
    v?
    (?:
        (?:(?P<epoch>[0-9]+)!)?                           # epoch
        (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
        (?P<pre>                                          # pre-release
            [-_\.]?
            (?P<pre_l>(a|b|c|rc|alpha|beta|pre|preview))
            [-_\.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<post>                                         # post release
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_\.]?
                (?P<post_l>post|rev|r)
                [-_\.]?
                (?P<post_n2>[0-9]+)?
            )
        )?
        (?P<dev>                                          # dev release
            [-_\.]?
            (?P<dev_l>dev)
            [-_\.]?
            (?P<dev_n>[0-9]+)?
        )?
    )
    (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
"""


class Version(_BaseVersion):

    _regex = re.compile(r"^\s*" + VERSION_PATTERN + r"\s*$", re.VERBOSE | re.IGNORECASE)

    def __init__(self, version):
        # type: (str) -> None

        # Validate the version and parse it into pieces
        match = self._regex.search(version)
        if not match:
            raise InvalidVersion("Invalid version: '{0}'".format(version))

        # Store the parsed out pieces of the version
        self._version = _Version(
            epoch=int(match.group("epoch")) if match.group("epoch") else 0,
            release=tuple(int(i) for i in match.group("release").split(".")),
            pre=_parse_letter_version(match.group("pre_l"), match.group("pre_n")),
            post=_parse_letter_version(
                match.group("post_l"), match.group("post_n1") or match.group("post_n2")
            ),
            dev=_parse_letter_version(match.group("dev_l"), match.group("dev_n")),
            local=_parse_local_version(match.group("local")),
        )

        # Generate a key which will be used for sorting
        self._key = _cmpkey(
            self._version.epoch,
            self._version.release,
            self._version.pre,
            self._version.post,
            self._version.dev,
            self._version.local,
        )

    def __repr__(self):
        # type: () -> str
        return "<Version({0})>".format(repr(str(self)))

    def __str__(self):
        # type: () -> str
        parts = []

        # Epoch
        if self.epoch != 0:
            parts.append("{0}!".format(self.epoch))

        # Release segment
        parts.append(".".join(str(x) for x in self.release))

        # Pre-release
        if self.pre is not None:
            parts.append("".join(str(x) for x in self.pre))

        # Post-release
        if self.post is not None:
            parts.append(".post{0}".format(self.post))

        # Development release
        if self.dev is not None:
            parts.append(".dev{0}".format(self.dev))

        # Local version segment
        if self.local is not None:
            parts.append("+{0}".format(self.local))

        return "".join(parts)

    @property
    def epoch(self):
        # type: () -> int
        _epoch = self._version.epoch  # type: int
        return _epoch

    @property
    def release(self):
        # type: () -> Tuple[int, ...]
        _release = self._version.release  # type: Tuple[int, ...]
        return _release

    @property
    def pre(self):
        # type: () -> Optional[Tuple[str, int]]
        _pre = self._version.pre  # type: Optional[Tuple[str, int]]
        return _pre

    @property
    def post(self):
        # type: () -> Optional[Tuple[str, int]]
        return self._version.post[1] if self._version.post else None

    @property
    def dev(self):
        # type: () -> Optional[Tuple[str, int]]
        return self._version.dev[1] if self._version.dev else None

    @property
    def local(self):
        # type: () -> Optional[str]
        if self._version.local:
            return ".".join(str(x) for x in self._version.local)
        else:
            return None

    @property
    def public(self):
        # type: () -> str
        return str(self).split("+", 1)[0]

    @property
    def base_version(self):
        # type: () -> str
        parts = []

        # Epoch
        if self.epoch != 0:
            parts.append("{0}!".format(self.epoch))

        # Release segment
        parts.append(".".join(str(x) for x in self.release))

        return "".join(parts)

    @property
    def is_prerelease(self):
        # type: () -> bool
        return self.dev is not None or self.pre is not None

    @property
    def is_postrelease(self):
        # type: () -> bool
        return self.post is not None

    @property
    def is_devrelease(self):
        # type: () -> bool
        return self.dev is not None

    @property
    def major(self):
        # type: () -> int
        return self.release[0] if len(self.release) >= 1 else 0

    @property
    def minor(self):
        # type: () -> int
        return self.release[1] if len(self.release) >= 2 else 0

    @property
    def micro(self):
        # type: () -> int
        return self.release[2] if len(self.release) >= 3 else 0


def _parse_letter_version(
    letter,  # type: str
    number,  # type: Union[str, bytes, SupportsInt]
):
    # type: (...) -> Optional[Tuple[str, int]]

    if letter:
        # We consider there to be an implicit 0 in a pre-release if there is
        # not a numeral associated with it.
        if number is None:
            number = 0

        # We normalize any letters to their lower case form
        letter = letter.lower()

        # We consider some words to be alternate spellings of other words and
        # in those cases we want to normalize the spellings to our preferred
        # spelling.
        if letter == "alpha":
            letter = "a"
        elif letter == "beta":
            letter = "b"
        elif letter in ["c", "pre", "preview"]:
            letter = "rc"
        elif letter in ["rev", "r"]:
            letter = "post"

        return letter, int(number)
    if not letter and number:
        # We assume if we are given a number, but we are not given a letter
        # then this is using the implicit post release syntax (e.g. 1.0-1)
        letter = "post"

        return letter, int(number)

    return None


_local_version_separators = re.compile(r"[\._-]")


def _parse_local_version(local):
    # type: (str) -> Optional[LocalType]
    """
    Takes a string like abc.1.twelve and turns it into ("abc", 1, "twelve").
    """
    if local is not None:
        return tuple(
            part.lower() if not part.isdigit() else int(part)
            for part in _local_version_separators.split(local)
        )
    return None


def _cmpkey(
    epoch,  # type: int
    release,  # type: Tuple[int, ...]
    pre,  # type: Optional[Tuple[str, int]]
    post,  # type: Optional[Tuple[str, int]]
    dev,  # type: Optional[Tuple[str, int]]
    local,  # type: Optional[Tuple[SubLocalType]]
):
    # type: (...) -> CmpKey

    # When we compare a release version, we want to compare it with all of the
    # trailing zeros removed. So we'll use a reverse the list, drop all the now
    # leading zeros until we come to something non zero, then take the rest
    # re-reverse it back into the correct order and make it a tuple and use
    # that for our sorting key.
    _release = tuple(
        reversed(list(itertools.dropwhile(lambda x: x == 0, reversed(release))))
    )

    # We need to "trick" the sorting algorithm to put 1.0.dev0 before 1.0a0.
    # We'll do this by abusing the pre segment, but we _only_ want to do this
    # if there is not a pre or a post segment. If we have one of those then
    # the normal sorting rules will handle this case correctly.
    if pre is None and post is None and dev is not None:
        _pre = NegativeInfinity  # type: PrePostDevType
    # Versions without a pre-release (except as noted above) should sort after
    # those with one.
    elif pre is None:
        _pre = Infinity
    else:
        _pre = pre

    # Versions without a post segment should sort before those with one.
    if post is None:
        _post = NegativeInfinity  # type: PrePostDevType

    else:
        _post = post

    # Versions without a development segment should sort after those with one.
    if dev is None:
        _dev = Infinity  # type: PrePostDevType

    else:
        _dev = dev

    if local is None:
        # Versions without a local segment should sort before those with one.
        _local = NegativeInfinity  # type: LocalType
    else:
        # Versions with a local segment need that segment parsed to implement
        # the sorting rules in PEP440.
        # - Alpha numeric segments sort before numeric segments
        # - Alpha numeric segments sort lexicographically
        # - Numeric segments sort numerically
        # - Shorter versions sort before longer versions when the prefixes
        #   match exactly
        _local = tuple(
            (i, "") if isinstance(i, int) else (NegativeInfinity, i) for i in local
        )

    return epoch, _release, _pre, _post, _dev, _local

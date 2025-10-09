# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.
from __future__ import absolute_import, division, print_function


class InfinityType(object):
    def __repr__(self):
        # type: () -> str
        return "Infinity"

    def __hash__(self):
        # type: () -> int
        return hash(repr(self))

    def __lt__(self, other):
        # type: (object) -> bool
        return False

    def __le__(self, other):
        # type: (object) -> bool
        return False

    def __eq__(self, other):
        # type: (object) -> bool
        return isinstance(other, self.__class__)

    def __ne__(self, other):
        # type: (object) -> bool
        return not isinstance(other, self.__class__)

    def __gt__(self, other):
        # type: (object) -> bool
        return True

    def __ge__(self, other):
        # type: (object) -> bool
        return True

    def __neg__(self):
        # type: (object) -> NegativeInfinityType
        return NegativeInfinity


Infinity = InfinityType()


class NegativeInfinityType(object):
    def __repr__(self):
        # type: () -> str
        return "-Infinity"

    def __hash__(self):
        # type: () -> int
        return hash(repr(self))

    def __lt__(self, other):
        # type: (object) -> bool
        return True

    def __le__(self, other):
        # type: (object) -> bool
        return True

    def __eq__(self, other):
        # type: (object) -> bool
        return isinstance(other, self.__class__)

    def __ne__(self, other):
        # type: (object) -> bool
        return not isinstance(other, self.__class__)

    def __gt__(self, other):
        # type: (object) -> bool
        return False

    def __ge__(self, other):
        # type: (object) -> bool
        return False

    def __neg__(self):
        # type: (object) -> InfinityType
        return Infinity


NegativeInfinity = NegativeInfinityType()

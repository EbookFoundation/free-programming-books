# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.
from __future__ import absolute_import, division, print_function

import sys

from ._typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Dict, Tuple, Type


PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

# flake8: noqa

if PY3:
    string_types = (str,)
else:
    string_types = (basestring,)


def with_metaclass(meta, *bases):
    # type: (Type[Any], Tuple[Type[Any], ...]) -> Any
    """
    Create a base class with a metaclass.
    """
    # This requires a bit of explanation: the basic idea is to make a dummy
    # metaclass for one level of class instantiation that replaces itself with
    # the actual metaclass.
    class metaclass(meta):  # type: ignore
        def __new__(cls, name, this_bases, d):
            # type: (Type[Any], str, Tuple[Any], Dict[Any, Any]) -> Any
            return meta(name, bases, d)

    return type.__new__(metaclass, "temporary_class", (), {})

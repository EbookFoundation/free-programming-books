"""
For types associated with installation schemes.

For a general overview of available schemes and their context, see
https://docs.python.org/3/install/index.html#alternate-installation.
"""

from dataclasses import dataclass

SCHEME_KEYS = ["platlib", "purelib", "headers", "scripts", "data"]


@dataclass(frozen=True)
class Scheme:
    """A Scheme holds paths which are used as the base directories for
    artifacts associated with a Python package.
    """

    __slots__ = SCHEME_KEYS

    platlib: str
    purelib: str
    headers: str
    scripts: str
    data: str

from __future__ import annotations

import functools
import logging

from pip._vendor.packaging import specifiers, version
from pip._vendor.packaging.requirements import Requirement

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=32)
def check_requires_python(
    requires_python: str | None, version_info: tuple[int, ...]
) -> bool:
    """
    Check if the given Python version matches a "Requires-Python" specifier.

    :param version_info: A 3-tuple of ints representing a Python
        major-minor-micro version to check (e.g. `sys.version_info[:3]`).

    :return: `True` if the given Python version satisfies the requirement.
        Otherwise, return `False`.

    :raises InvalidSpecifier: If `requires_python` has an invalid format.
    """
    if requires_python is None:
        # The package provides no information
        return True
    requires_python_specifier = specifiers.SpecifierSet(requires_python)

    python_version = version.parse(".".join(map(str, version_info)))
    return python_version in requires_python_specifier


@functools.lru_cache(maxsize=10000)
def get_requirement(req_string: str) -> Requirement:
    """Construct a packaging.Requirement object with caching"""
    # Parsing requirement strings is expensive, and is also expected to happen
    # with a low diversity of different arguments (at least relative the number
    # constructed). This method adds a cache to requirement object creation to
    # minimize repeated parsing of the same string to construct equivalent
    # Requirement objects.
    return Requirement(req_string)

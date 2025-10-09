from __future__ import annotations

import contextlib
import functools
import os
import sys
from typing import Literal, Protocol, cast

from pip._internal.utils.deprecation import deprecated
from pip._internal.utils.misc import strtobool

from .base import BaseDistribution, BaseEnvironment, FilesystemWheel, MemoryWheel, Wheel

__all__ = [
    "BaseDistribution",
    "BaseEnvironment",
    "FilesystemWheel",
    "MemoryWheel",
    "Wheel",
    "get_default_environment",
    "get_environment",
    "get_wheel_distribution",
    "select_backend",
]


def _should_use_importlib_metadata() -> bool:
    """Whether to use the ``importlib.metadata`` or ``pkg_resources`` backend.

    By default, pip uses ``importlib.metadata`` on Python 3.11+, and
    ``pkg_resources`` otherwise. Up to Python 3.13, This can be
    overridden by a couple of ways:

    * If environment variable ``_PIP_USE_IMPORTLIB_METADATA`` is set, it
      dictates whether ``importlib.metadata`` is used, for Python <3.14.
    * On Python 3.11, 3.12 and 3.13, Python distributors can patch
      ``importlib.metadata`` to add a global constant
      ``_PIP_USE_IMPORTLIB_METADATA = False``. This makes pip use
      ``pkg_resources`` (unless the user set the aforementioned environment
      variable to *True*).

    On Python 3.14+, the ``pkg_resources`` backend cannot be used.
    """
    if sys.version_info >= (3, 14):
        # On Python >=3.14 we only support importlib.metadata.
        return True
    with contextlib.suppress(KeyError, ValueError):
        # On Python <3.14, if the environment variable is set, we obey what it says.
        return bool(strtobool(os.environ["_PIP_USE_IMPORTLIB_METADATA"]))
    if sys.version_info < (3, 11):
        # On Python <3.11, we always use pkg_resources, unless the environment
        # variable was set.
        return False
    # On Python 3.11, 3.12 and 3.13, we check if the global constant is set.
    import importlib.metadata

    return bool(getattr(importlib.metadata, "_PIP_USE_IMPORTLIB_METADATA", True))


def _emit_pkg_resources_deprecation_if_needed() -> None:
    if sys.version_info < (3, 11):
        # All pip versions supporting Python<=3.11 will support pkg_resources,
        # and pkg_resources is the default for these, so let's not bother users.
        return

    import importlib.metadata

    if hasattr(importlib.metadata, "_PIP_USE_IMPORTLIB_METADATA"):
        # The Python distributor has set the global constant, so we don't
        # warn, since it is not a user decision.
        return

    # The user has decided to use pkg_resources, so we warn.
    deprecated(
        reason="Using the pkg_resources metadata backend is deprecated.",
        replacement=(
            "to use the default importlib.metadata backend, "
            "by unsetting the _PIP_USE_IMPORTLIB_METADATA environment variable"
        ),
        gone_in="26.3",
        issue=13317,
    )


class Backend(Protocol):
    NAME: Literal["importlib", "pkg_resources"]
    Distribution: type[BaseDistribution]
    Environment: type[BaseEnvironment]


@functools.cache
def select_backend() -> Backend:
    if _should_use_importlib_metadata():
        from . import importlib

        return cast(Backend, importlib)

    _emit_pkg_resources_deprecation_if_needed()

    from . import pkg_resources

    return cast(Backend, pkg_resources)


def get_default_environment() -> BaseEnvironment:
    """Get the default representation for the current environment.

    This returns an Environment instance from the chosen backend. The default
    Environment instance should be built from ``sys.path`` and may use caching
    to share instance state across calls.
    """
    return select_backend().Environment.default()


def get_environment(paths: list[str] | None) -> BaseEnvironment:
    """Get a representation of the environment specified by ``paths``.

    This returns an Environment instance from the chosen backend based on the
    given import paths. The backend must build a fresh instance representing
    the state of installed distributions when this function is called.
    """
    return select_backend().Environment.from_paths(paths)


def get_directory_distribution(directory: str) -> BaseDistribution:
    """Get the distribution metadata representation in the specified directory.

    This returns a Distribution instance from the chosen backend based on
    the given on-disk ``.dist-info`` directory.
    """
    return select_backend().Distribution.from_directory(directory)


def get_wheel_distribution(wheel: Wheel, canonical_name: str) -> BaseDistribution:
    """Get the representation of the specified wheel's distribution metadata.

    This returns a Distribution instance from the chosen backend based on
    the given wheel's ``.dist-info`` directory.

    :param canonical_name: Normalized project name of the given wheel.
    """
    return select_backend().Distribution.from_wheel(wheel, canonical_name)


def get_metadata_distribution(
    metadata_contents: bytes,
    filename: str,
    canonical_name: str,
) -> BaseDistribution:
    """Get the dist representation of the specified METADATA file contents.

    This returns a Distribution instance from the chosen backend sourced from the data
    in `metadata_contents`.

    :param metadata_contents: Contents of a METADATA file within a dist, or one served
                              via PEP 658.
    :param filename: Filename for the dist this metadata represents.
    :param canonical_name: Normalized project name of the given dist.
    """
    return select_backend().Distribution.from_metadata_file_contents(
        metadata_contents,
        filename,
        canonical_name,
    )

from __future__ import annotations

import importlib.metadata
import os
from typing import Any, Protocol, cast

from pip._vendor.packaging.utils import NormalizedName, canonicalize_name


class BadMetadata(ValueError):
    def __init__(self, dist: importlib.metadata.Distribution, *, reason: str) -> None:
        self.dist = dist
        self.reason = reason

    def __str__(self) -> str:
        return f"Bad metadata in {self.dist} ({self.reason})"


class BasePath(Protocol):
    """A protocol that various path objects conform.

    This exists because importlib.metadata uses both ``pathlib.Path`` and
    ``zipfile.Path``, and we need a common base for type hints (Union does not
    work well since ``zipfile.Path`` is too new for our linter setup).

    This does not mean to be exhaustive, but only contains things that present
    in both classes *that we need*.
    """

    @property
    def name(self) -> str:
        raise NotImplementedError()

    @property
    def parent(self) -> BasePath:
        raise NotImplementedError()


def get_info_location(d: importlib.metadata.Distribution) -> BasePath | None:
    """Find the path to the distribution's metadata directory.

    HACK: This relies on importlib.metadata's private ``_path`` attribute. Not
    all distributions exist on disk, so importlib.metadata is correct to not
    expose the attribute as public. But pip's code base is old and not as clean,
    so we do this to avoid having to rewrite too many things. Hopefully we can
    eliminate this some day.
    """
    return getattr(d, "_path", None)


def parse_name_and_version_from_info_directory(
    dist: importlib.metadata.Distribution,
) -> tuple[str | None, str | None]:
    """Get a name and version from the metadata directory name.

    This is much faster than reading distribution metadata.
    """
    info_location = get_info_location(dist)
    if info_location is None:
        return None, None

    stem, suffix = os.path.splitext(info_location.name)
    if suffix == ".dist-info":
        name, sep, version = stem.partition("-")
        if sep:
            return name, version

    if suffix == ".egg-info":
        name = stem.split("-", 1)[0]
        return name, None

    return None, None


def get_dist_canonical_name(dist: importlib.metadata.Distribution) -> NormalizedName:
    """Get the distribution's normalized name.

    The ``name`` attribute is only available in Python 3.10 or later. We are
    targeting exactly that, but Mypy does not know this.
    """
    if name := parse_name_and_version_from_info_directory(dist)[0]:
        return canonicalize_name(name)

    name = cast(Any, dist).name
    if not isinstance(name, str):
        raise BadMetadata(dist, reason="invalid metadata entry 'name'")
    return canonicalize_name(name)

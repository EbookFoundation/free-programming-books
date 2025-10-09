from __future__ import annotations

import importlib.metadata
import logging
import os
import pathlib
import sys
import zipfile
from collections.abc import Iterator, Sequence
from typing import Optional

from pip._vendor.packaging.utils import (
    InvalidWheelFilename,
    NormalizedName,
    canonicalize_name,
    parse_wheel_filename,
)

from pip._internal.metadata.base import BaseDistribution, BaseEnvironment
from pip._internal.utils.filetypes import WHEEL_EXTENSION

from ._compat import BadMetadata, BasePath, get_dist_canonical_name, get_info_location
from ._dists import Distribution

logger = logging.getLogger(__name__)


def _looks_like_wheel(location: str) -> bool:
    if not location.endswith(WHEEL_EXTENSION):
        return False
    if not os.path.isfile(location):
        return False
    try:
        parse_wheel_filename(os.path.basename(location))
    except InvalidWheelFilename:
        return False
    return zipfile.is_zipfile(location)


class _DistributionFinder:
    """Finder to locate distributions.

    The main purpose of this class is to memoize found distributions' names, so
    only one distribution is returned for each package name. At lot of pip code
    assumes this (because it is setuptools's behavior), and not doing the same
    can potentially cause a distribution in lower precedence path to override a
    higher precedence one if the caller is not careful.

    Eventually we probably want to make it possible to see lower precedence
    installations as well. It's useful feature, after all.
    """

    FoundResult = tuple[importlib.metadata.Distribution, Optional[BasePath]]

    def __init__(self) -> None:
        self._found_names: set[NormalizedName] = set()

    def _find_impl(self, location: str) -> Iterator[FoundResult]:
        """Find distributions in a location."""
        # Skip looking inside a wheel. Since a package inside a wheel is not
        # always valid (due to .data directories etc.), its .dist-info entry
        # should not be considered an installed distribution.
        if _looks_like_wheel(location):
            return
        # To know exactly where we find a distribution, we have to feed in the
        # paths one by one, instead of dumping the list to importlib.metadata.
        for dist in importlib.metadata.distributions(path=[location]):
            info_location = get_info_location(dist)
            try:
                name = get_dist_canonical_name(dist)
            except BadMetadata as e:
                logger.warning("Skipping %s due to %s", info_location, e.reason)
                continue
            if name in self._found_names:
                continue
            self._found_names.add(name)
            yield dist, info_location

    def find(self, location: str) -> Iterator[BaseDistribution]:
        """Find distributions in a location.

        The path can be either a directory, or a ZIP archive.
        """
        for dist, info_location in self._find_impl(location):
            if info_location is None:
                installed_location: BasePath | None = None
            else:
                installed_location = info_location.parent
            yield Distribution(dist, info_location, installed_location)

    def find_legacy_editables(self, location: str) -> Iterator[BaseDistribution]:
        """Read location in egg-link files and return distributions in there.

        The path should be a directory; otherwise this returns nothing. This
        follows how setuptools does this for compatibility. The first non-empty
        line in the egg-link is read as a path (resolved against the egg-link's
        containing directory if relative). Distributions found at that linked
        location are returned.
        """
        path = pathlib.Path(location)
        if not path.is_dir():
            return
        for child in path.iterdir():
            if child.suffix != ".egg-link":
                continue
            with child.open() as f:
                lines = (line.strip() for line in f)
                target_rel = next((line for line in lines if line), "")
            if not target_rel:
                continue
            target_location = str(path.joinpath(target_rel))
            for dist, info_location in self._find_impl(target_location):
                yield Distribution(dist, info_location, path)


class Environment(BaseEnvironment):
    def __init__(self, paths: Sequence[str]) -> None:
        self._paths = paths

    @classmethod
    def default(cls) -> BaseEnvironment:
        return cls(sys.path)

    @classmethod
    def from_paths(cls, paths: list[str] | None) -> BaseEnvironment:
        if paths is None:
            return cls(sys.path)
        return cls(paths)

    def _iter_distributions(self) -> Iterator[BaseDistribution]:
        finder = _DistributionFinder()
        for location in self._paths:
            yield from finder.find(location)
            yield from finder.find_legacy_editables(location)

    def get_distribution(self, name: str) -> BaseDistribution | None:
        canonical_name = canonicalize_name(name)
        matches = (
            distribution
            for distribution in self.iter_all_distributions()
            if distribution.canonical_name == canonical_name
        )
        return next(matches, None)

from __future__ import annotations

import email.message
import email.parser
import logging
import os
import zipfile
from collections.abc import Collection, Iterable, Iterator, Mapping
from typing import (
    NamedTuple,
)

from pip._vendor import pkg_resources
from pip._vendor.packaging.requirements import Requirement
from pip._vendor.packaging.utils import NormalizedName, canonicalize_name
from pip._vendor.packaging.version import Version
from pip._vendor.packaging.version import parse as parse_version

from pip._internal.exceptions import InvalidWheel, NoneMetadataError, UnsupportedWheel
from pip._internal.utils.egg_link import egg_link_path_from_location
from pip._internal.utils.misc import display_path, normalize_path
from pip._internal.utils.wheel import parse_wheel, read_wheel_metadata_file

from .base import (
    BaseDistribution,
    BaseEntryPoint,
    BaseEnvironment,
    InfoPath,
    Wheel,
)

__all__ = ["NAME", "Distribution", "Environment"]

logger = logging.getLogger(__name__)

NAME = "pkg_resources"


class EntryPoint(NamedTuple):
    name: str
    value: str
    group: str


class InMemoryMetadata:
    """IMetadataProvider that reads metadata files from a dictionary.

    This also maps metadata decoding exceptions to our internal exception type.
    """

    def __init__(self, metadata: Mapping[str, bytes], wheel_name: str) -> None:
        self._metadata = metadata
        self._wheel_name = wheel_name

    def has_metadata(self, name: str) -> bool:
        return name in self._metadata

    def get_metadata(self, name: str) -> str:
        try:
            return self._metadata[name].decode()
        except UnicodeDecodeError as e:
            # Augment the default error with the origin of the file.
            raise UnsupportedWheel(
                f"Error decoding metadata for {self._wheel_name}: {e} in {name} file"
            )

    def get_metadata_lines(self, name: str) -> Iterable[str]:
        return pkg_resources.yield_lines(self.get_metadata(name))

    def metadata_isdir(self, name: str) -> bool:
        return False

    def metadata_listdir(self, name: str) -> list[str]:
        return []

    def run_script(self, script_name: str, namespace: str) -> None:
        pass


class Distribution(BaseDistribution):
    def __init__(self, dist: pkg_resources.Distribution) -> None:
        self._dist = dist
        # This is populated lazily, to avoid loading metadata for all possible
        # distributions eagerly.
        self.__extra_mapping: Mapping[NormalizedName, str] | None = None

    @property
    def _extra_mapping(self) -> Mapping[NormalizedName, str]:
        if self.__extra_mapping is None:
            self.__extra_mapping = {
                canonicalize_name(extra): extra for extra in self._dist.extras
            }

        return self.__extra_mapping

    @classmethod
    def from_directory(cls, directory: str) -> BaseDistribution:
        dist_dir = directory.rstrip(os.sep)

        # Build a PathMetadata object, from path to metadata. :wink:
        base_dir, dist_dir_name = os.path.split(dist_dir)
        metadata = pkg_resources.PathMetadata(base_dir, dist_dir)

        # Determine the correct Distribution object type.
        if dist_dir.endswith(".egg-info"):
            dist_cls = pkg_resources.Distribution
            dist_name = os.path.splitext(dist_dir_name)[0]
        else:
            assert dist_dir.endswith(".dist-info")
            dist_cls = pkg_resources.DistInfoDistribution
            dist_name = os.path.splitext(dist_dir_name)[0].split("-")[0]

        dist = dist_cls(base_dir, project_name=dist_name, metadata=metadata)
        return cls(dist)

    @classmethod
    def from_metadata_file_contents(
        cls,
        metadata_contents: bytes,
        filename: str,
        project_name: str,
    ) -> BaseDistribution:
        metadata_dict = {
            "METADATA": metadata_contents,
        }
        dist = pkg_resources.DistInfoDistribution(
            location=filename,
            metadata=InMemoryMetadata(metadata_dict, filename),
            project_name=project_name,
        )
        return cls(dist)

    @classmethod
    def from_wheel(cls, wheel: Wheel, name: str) -> BaseDistribution:
        try:
            with wheel.as_zipfile() as zf:
                info_dir, _ = parse_wheel(zf, name)
                metadata_dict = {
                    path.split("/", 1)[-1]: read_wheel_metadata_file(zf, path)
                    for path in zf.namelist()
                    if path.startswith(f"{info_dir}/")
                }
        except zipfile.BadZipFile as e:
            raise InvalidWheel(wheel.location, name) from e
        except UnsupportedWheel as e:
            raise UnsupportedWheel(f"{name} has an invalid wheel, {e}")
        dist = pkg_resources.DistInfoDistribution(
            location=wheel.location,
            metadata=InMemoryMetadata(metadata_dict, wheel.location),
            project_name=name,
        )
        return cls(dist)

    @property
    def location(self) -> str | None:
        return self._dist.location

    @property
    def installed_location(self) -> str | None:
        egg_link = egg_link_path_from_location(self.raw_name)
        if egg_link:
            location = egg_link
        elif self.location:
            location = self.location
        else:
            return None
        return normalize_path(location)

    @property
    def info_location(self) -> str | None:
        return self._dist.egg_info

    @property
    def installed_by_distutils(self) -> bool:
        # A distutils-installed distribution is provided by FileMetadata. This
        # provider has a "path" attribute not present anywhere else. Not the
        # best introspection logic, but pip has been doing this for a long time.
        try:
            return bool(self._dist._provider.path)
        except AttributeError:
            return False

    @property
    def canonical_name(self) -> NormalizedName:
        return canonicalize_name(self._dist.project_name)

    @property
    def version(self) -> Version:
        return parse_version(self._dist.version)

    @property
    def raw_version(self) -> str:
        return self._dist.version

    def is_file(self, path: InfoPath) -> bool:
        return self._dist.has_metadata(str(path))

    def iter_distutils_script_names(self) -> Iterator[str]:
        yield from self._dist.metadata_listdir("scripts")

    def read_text(self, path: InfoPath) -> str:
        name = str(path)
        if not self._dist.has_metadata(name):
            raise FileNotFoundError(name)
        content = self._dist.get_metadata(name)
        if content is None:
            raise NoneMetadataError(self, name)
        return content

    def iter_entry_points(self) -> Iterable[BaseEntryPoint]:
        for group, entries in self._dist.get_entry_map().items():
            for name, entry_point in entries.items():
                name, _, value = str(entry_point).partition("=")
                yield EntryPoint(name=name.strip(), value=value.strip(), group=group)

    def _metadata_impl(self) -> email.message.Message:
        """
        :raises NoneMetadataError: if the distribution reports `has_metadata()`
            True but `get_metadata()` returns None.
        """
        if isinstance(self._dist, pkg_resources.DistInfoDistribution):
            metadata_name = "METADATA"
        else:
            metadata_name = "PKG-INFO"
        try:
            metadata = self.read_text(metadata_name)
        except FileNotFoundError:
            if self.location:
                displaying_path = display_path(self.location)
            else:
                displaying_path = repr(self.location)
            logger.warning("No metadata found in %s", displaying_path)
            metadata = ""
        feed_parser = email.parser.FeedParser()
        feed_parser.feed(metadata)
        return feed_parser.close()

    def iter_dependencies(self, extras: Collection[str] = ()) -> Iterable[Requirement]:
        if extras:
            relevant_extras = set(self._extra_mapping) & set(
                map(canonicalize_name, extras)
            )
            extras = [self._extra_mapping[extra] for extra in relevant_extras]
        return self._dist.requires(extras)

    def iter_provided_extras(self) -> Iterable[NormalizedName]:
        return self._extra_mapping.keys()


class Environment(BaseEnvironment):
    def __init__(self, ws: pkg_resources.WorkingSet) -> None:
        self._ws = ws

    @classmethod
    def default(cls) -> BaseEnvironment:
        return cls(pkg_resources.working_set)

    @classmethod
    def from_paths(cls, paths: list[str] | None) -> BaseEnvironment:
        return cls(pkg_resources.WorkingSet(paths))

    def _iter_distributions(self) -> Iterator[BaseDistribution]:
        for dist in self._ws:
            yield Distribution(dist)

    def _search_distribution(self, name: str) -> BaseDistribution | None:
        """Find a distribution matching the ``name`` in the environment.

        This searches from *all* distributions available in the environment, to
        match the behavior of ``pkg_resources.get_distribution()``.
        """
        canonical_name = canonicalize_name(name)
        for dist in self.iter_all_distributions():
            if dist.canonical_name == canonical_name:
                return dist
        return None

    def get_distribution(self, name: str) -> BaseDistribution | None:
        # Search the distribution by looking through the working set.
        dist = self._search_distribution(name)
        if dist:
            return dist

        # If distribution could not be found, call working_set.require to
        # update the working set, and try to find the distribution again.
        # This might happen for e.g. when you install a package twice, once
        # using setup.py develop and again using setup.py install. Now when
        # running pip uninstall twice, the package gets removed from the
        # working set in the first uninstall, so we have to populate the
        # working set again so that pip knows about it and the packages gets
        # picked up and is successfully uninstalled the second time too.
        try:
            # We didn't pass in any version specifiers, so this can never
            # raise pkg_resources.VersionConflict.
            self._ws.require(name)
        except pkg_resources.DistributionNotFound:
            return None
        return self._search_distribution(name)

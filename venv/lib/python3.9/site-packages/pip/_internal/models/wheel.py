"""Represents a wheel file and provides access to the various parts of the
name that have meaning.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from pip._vendor.packaging.tags import Tag
from pip._vendor.packaging.utils import BuildTag, parse_wheel_filename
from pip._vendor.packaging.utils import (
    InvalidWheelFilename as _PackagingInvalidWheelFilename,
)

from pip._internal.exceptions import InvalidWheelFilename
from pip._internal.utils.deprecation import deprecated


class Wheel:
    """A wheel file"""

    legacy_wheel_file_re = re.compile(
        r"""^(?P<namever>(?P<name>[^\s-]+?)-(?P<ver>[^\s-]*?))
        ((-(?P<build>\d[^-]*?))?-(?P<pyver>[^\s-]+?)-(?P<abi>[^\s-]+?)-(?P<plat>[^\s-]+?)
        \.whl|\.dist-info)$""",
        re.VERBOSE,
    )

    def __init__(self, filename: str) -> None:
        self.filename = filename

        # To make mypy happy specify type hints that can come from either
        # parse_wheel_filename or the legacy_wheel_file_re match.
        self.name: str
        self._build_tag: BuildTag | None = None

        try:
            wheel_info = parse_wheel_filename(filename)
            self.name, _version, self._build_tag, self.file_tags = wheel_info
            self.version = str(_version)
        except _PackagingInvalidWheelFilename as e:
            # Check if the wheel filename is in the legacy format
            legacy_wheel_info = self.legacy_wheel_file_re.match(filename)
            if not legacy_wheel_info:
                raise InvalidWheelFilename(e.args[0]) from None

            deprecated(
                reason=(
                    f"Wheel filename {filename!r} is not correctly normalised. "
                    "Future versions of pip will raise the following error:\n"
                    f"{e.args[0]}\n\n"
                ),
                replacement=(
                    "to rename the wheel to use a correctly normalised "
                    "name (this may require updating the version in "
                    "the project metadata)"
                ),
                gone_in="25.3",
                issue=12938,
            )

            self.name = legacy_wheel_info.group("name").replace("_", "-")
            self.version = legacy_wheel_info.group("ver").replace("_", "-")

            # Generate the file tags from the legacy wheel filename
            pyversions = legacy_wheel_info.group("pyver").split(".")
            abis = legacy_wheel_info.group("abi").split(".")
            plats = legacy_wheel_info.group("plat").split(".")
            self.file_tags = frozenset(
                Tag(interpreter=py, abi=abi, platform=plat)
                for py in pyversions
                for abi in abis
                for plat in plats
            )

    @property
    def build_tag(self) -> BuildTag:
        if self._build_tag is not None:
            return self._build_tag

        # Parse the build tag from the legacy wheel filename
        legacy_wheel_info = self.legacy_wheel_file_re.match(self.filename)
        assert legacy_wheel_info is not None, "guaranteed by filename validation"
        build_tag = legacy_wheel_info.group("build")
        match = re.match(r"^(\d+)(.*)$", build_tag)
        assert match is not None, "guaranteed by filename validation"
        build_tag_groups = match.groups()
        self._build_tag = (int(build_tag_groups[0]), build_tag_groups[1])

        return self._build_tag

    def get_formatted_file_tags(self) -> list[str]:
        """Return the wheel's tags as a sorted list of strings."""
        return sorted(str(tag) for tag in self.file_tags)

    def support_index_min(self, tags: list[Tag]) -> int:
        """Return the lowest index that one of the wheel's file_tag combinations
        achieves in the given list of supported tags.

        For example, if there are 8 supported tags and one of the file tags
        is first in the list, then return 0.

        :param tags: the PEP 425 tags to check the wheel against, in order
            with most preferred first.

        :raises ValueError: If none of the wheel's file tags match one of
            the supported tags.
        """
        try:
            return next(i for i, t in enumerate(tags) if t in self.file_tags)
        except StopIteration:
            raise ValueError()

    def find_most_preferred_tag(
        self, tags: list[Tag], tag_to_priority: dict[Tag, int]
    ) -> int:
        """Return the priority of the most preferred tag that one of the wheel's file
        tag combinations achieves in the given list of supported tags using the given
        tag_to_priority mapping, where lower priorities are more-preferred.

        This is used in place of support_index_min in some cases in order to avoid
        an expensive linear scan of a large list of tags.

        :param tags: the PEP 425 tags to check the wheel against.
        :param tag_to_priority: a mapping from tag to priority of that tag, where
            lower is more preferred.

        :raises ValueError: If none of the wheel's file tags match one of
            the supported tags.
        """
        return min(
            tag_to_priority[tag] for tag in self.file_tags if tag in tag_to_priority
        )

    def supported(self, tags: Iterable[Tag]) -> bool:
        """Return whether the wheel is compatible with one of the given tags.

        :param tags: the PEP 425 tags to check the wheel against.
        """
        return not self.file_tags.isdisjoint(tags)

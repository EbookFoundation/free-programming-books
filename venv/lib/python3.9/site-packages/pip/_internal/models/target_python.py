from __future__ import annotations

import sys

from pip._vendor.packaging.tags import Tag

from pip._internal.utils.compatibility_tags import get_supported, version_info_to_nodot
from pip._internal.utils.misc import normalize_version_info


class TargetPython:
    """
    Encapsulates the properties of a Python interpreter one is targeting
    for a package install, download, etc.
    """

    __slots__ = [
        "_given_py_version_info",
        "abis",
        "implementation",
        "platforms",
        "py_version",
        "py_version_info",
        "_valid_tags",
        "_valid_tags_set",
    ]

    def __init__(
        self,
        platforms: list[str] | None = None,
        py_version_info: tuple[int, ...] | None = None,
        abis: list[str] | None = None,
        implementation: str | None = None,
    ) -> None:
        """
        :param platforms: A list of strings or None. If None, searches for
            packages that are supported by the current system. Otherwise, will
            find packages that can be built on the platforms passed in. These
            packages will only be downloaded for distribution: they will
            not be built locally.
        :param py_version_info: An optional tuple of ints representing the
            Python version information to use (e.g. `sys.version_info[:3]`).
            This can have length 1, 2, or 3 when provided.
        :param abis: A list of strings or None. This is passed to
            compatibility_tags.py's get_supported() function as is.
        :param implementation: A string or None. This is passed to
            compatibility_tags.py's get_supported() function as is.
        """
        # Store the given py_version_info for when we call get_supported().
        self._given_py_version_info = py_version_info

        if py_version_info is None:
            py_version_info = sys.version_info[:3]
        else:
            py_version_info = normalize_version_info(py_version_info)

        py_version = ".".join(map(str, py_version_info[:2]))

        self.abis = abis
        self.implementation = implementation
        self.platforms = platforms
        self.py_version = py_version
        self.py_version_info = py_version_info

        # This is used to cache the return value of get_(un)sorted_tags.
        self._valid_tags: list[Tag] | None = None
        self._valid_tags_set: set[Tag] | None = None

    def format_given(self) -> str:
        """
        Format the given, non-None attributes for display.
        """
        display_version = None
        if self._given_py_version_info is not None:
            display_version = ".".join(
                str(part) for part in self._given_py_version_info
            )

        key_values = [
            ("platforms", self.platforms),
            ("version_info", display_version),
            ("abis", self.abis),
            ("implementation", self.implementation),
        ]
        return " ".join(
            f"{key}={value!r}" for key, value in key_values if value is not None
        )

    def get_sorted_tags(self) -> list[Tag]:
        """
        Return the supported PEP 425 tags to check wheel candidates against.

        The tags are returned in order of preference (most preferred first).
        """
        if self._valid_tags is None:
            # Pass versions=None if no py_version_info was given since
            # versions=None uses special default logic.
            py_version_info = self._given_py_version_info
            if py_version_info is None:
                version = None
            else:
                version = version_info_to_nodot(py_version_info)

            tags = get_supported(
                version=version,
                platforms=self.platforms,
                abis=self.abis,
                impl=self.implementation,
            )
            self._valid_tags = tags

        return self._valid_tags

    def get_unsorted_tags(self) -> set[Tag]:
        """Exactly the same as get_sorted_tags, but returns a set.

        This is important for performance.
        """
        if self._valid_tags_set is None:
            self._valid_tags_set = set(self.get_sorted_tags())

        return self._valid_tags_set

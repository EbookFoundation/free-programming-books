from __future__ import annotations

import contextlib
import hashlib
import logging
import os
from collections.abc import Generator
from types import TracebackType

from pip._internal.req.req_install import InstallRequirement
from pip._internal.utils.temp_dir import TempDirectory

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def update_env_context_manager(**changes: str) -> Generator[None, None, None]:
    target = os.environ

    # Save values from the target and change them.
    non_existent_marker = object()
    saved_values: dict[str, object | str] = {}
    for name, new_value in changes.items():
        try:
            saved_values[name] = target[name]
        except KeyError:
            saved_values[name] = non_existent_marker
        target[name] = new_value

    try:
        yield
    finally:
        # Restore original values in the target.
        for name, original_value in saved_values.items():
            if original_value is non_existent_marker:
                del target[name]
            else:
                assert isinstance(original_value, str)  # for mypy
                target[name] = original_value


@contextlib.contextmanager
def get_build_tracker() -> Generator[BuildTracker, None, None]:
    root = os.environ.get("PIP_BUILD_TRACKER")
    with contextlib.ExitStack() as ctx:
        if root is None:
            root = ctx.enter_context(TempDirectory(kind="build-tracker")).path
            ctx.enter_context(update_env_context_manager(PIP_BUILD_TRACKER=root))
            logger.debug("Initialized build tracking at %s", root)

        with BuildTracker(root) as tracker:
            yield tracker


class TrackerId(str):
    """Uniquely identifying string provided to the build tracker."""


class BuildTracker:
    """Ensure that an sdist cannot request itself as a setup requirement.

    When an sdist is prepared, it identifies its setup requirements in the
    context of ``BuildTracker.track()``. If a requirement shows up recursively, this
    raises an exception.

    This stops fork bombs embedded in malicious packages."""

    def __init__(self, root: str) -> None:
        self._root = root
        self._entries: dict[TrackerId, InstallRequirement] = {}
        logger.debug("Created build tracker: %s", self._root)

    def __enter__(self) -> BuildTracker:
        logger.debug("Entered build tracker: %s", self._root)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.cleanup()

    def _entry_path(self, key: TrackerId) -> str:
        hashed = hashlib.sha224(key.encode()).hexdigest()
        return os.path.join(self._root, hashed)

    def add(self, req: InstallRequirement, key: TrackerId) -> None:
        """Add an InstallRequirement to build tracking."""

        # Get the file to write information about this requirement.
        entry_path = self._entry_path(key)

        # Try reading from the file. If it exists and can be read from, a build
        # is already in progress, so a LookupError is raised.
        try:
            with open(entry_path) as fp:
                contents = fp.read()
        except FileNotFoundError:
            pass
        else:
            message = f"{req.link} is already being built: {contents}"
            raise LookupError(message)

        # If we're here, req should really not be building already.
        assert key not in self._entries

        # Start tracking this requirement.
        with open(entry_path, "w", encoding="utf-8") as fp:
            fp.write(str(req))
        self._entries[key] = req

        logger.debug("Added %s to build tracker %r", req, self._root)

    def remove(self, req: InstallRequirement, key: TrackerId) -> None:
        """Remove an InstallRequirement from build tracking."""

        # Delete the created file and the corresponding entry.
        os.unlink(self._entry_path(key))
        del self._entries[key]

        logger.debug("Removed %s from build tracker %r", req, self._root)

    def cleanup(self) -> None:
        for key, req in list(self._entries.items()):
            self.remove(req, key)

        logger.debug("Removed build tracker: %r", self._root)

    @contextlib.contextmanager
    def track(self, req: InstallRequirement, key: str) -> Generator[None, None, None]:
        """Ensure that `key` cannot install itself as a setup requirement.

        :raises LookupError: If `key` was already provided in a parent invocation of
                             the context introduced by this method."""
        tracker_id = TrackerId(key)
        self.add(req, tracker_id)
        yield
        self.remove(req, tracker_id)

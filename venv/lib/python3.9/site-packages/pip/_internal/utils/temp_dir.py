from __future__ import annotations

import errno
import itertools
import logging
import os.path
import tempfile
import traceback
from collections.abc import Generator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import (
    Any,
    Callable,
    TypeVar,
)

from pip._internal.utils.misc import enum, rmtree

logger = logging.getLogger(__name__)

_T = TypeVar("_T", bound="TempDirectory")


# Kinds of temporary directories. Only needed for ones that are
# globally-managed.
tempdir_kinds = enum(
    BUILD_ENV="build-env",
    EPHEM_WHEEL_CACHE="ephem-wheel-cache",
    REQ_BUILD="req-build",
)


_tempdir_manager: ExitStack | None = None


@contextmanager
def global_tempdir_manager() -> Generator[None, None, None]:
    global _tempdir_manager
    with ExitStack() as stack:
        old_tempdir_manager, _tempdir_manager = _tempdir_manager, stack
        try:
            yield
        finally:
            _tempdir_manager = old_tempdir_manager


class TempDirectoryTypeRegistry:
    """Manages temp directory behavior"""

    def __init__(self) -> None:
        self._should_delete: dict[str, bool] = {}

    def set_delete(self, kind: str, value: bool) -> None:
        """Indicate whether a TempDirectory of the given kind should be
        auto-deleted.
        """
        self._should_delete[kind] = value

    def get_delete(self, kind: str) -> bool:
        """Get configured auto-delete flag for a given TempDirectory type,
        default True.
        """
        return self._should_delete.get(kind, True)


_tempdir_registry: TempDirectoryTypeRegistry | None = None


@contextmanager
def tempdir_registry() -> Generator[TempDirectoryTypeRegistry, None, None]:
    """Provides a scoped global tempdir registry that can be used to dictate
    whether directories should be deleted.
    """
    global _tempdir_registry
    old_tempdir_registry = _tempdir_registry
    _tempdir_registry = TempDirectoryTypeRegistry()
    try:
        yield _tempdir_registry
    finally:
        _tempdir_registry = old_tempdir_registry


class _Default:
    pass


_default = _Default()


class TempDirectory:
    """Helper class that owns and cleans up a temporary directory.

    This class can be used as a context manager or as an OO representation of a
    temporary directory.

    Attributes:
        path
            Location to the created temporary directory
        delete
            Whether the directory should be deleted when exiting
            (when used as a contextmanager)

    Methods:
        cleanup()
            Deletes the temporary directory

    When used as a context manager, if the delete attribute is True, on
    exiting the context the temporary directory is deleted.
    """

    def __init__(
        self,
        path: str | None = None,
        delete: bool | None | _Default = _default,
        kind: str = "temp",
        globally_managed: bool = False,
        ignore_cleanup_errors: bool = True,
    ):
        super().__init__()

        if delete is _default:
            if path is not None:
                # If we were given an explicit directory, resolve delete option
                # now.
                delete = False
            else:
                # Otherwise, we wait until cleanup and see what
                # tempdir_registry says.
                delete = None

        # The only time we specify path is in for editables where it
        # is the value of the --src option.
        if path is None:
            path = self._create(kind)

        self._path = path
        self._deleted = False
        self.delete = delete
        self.kind = kind
        self.ignore_cleanup_errors = ignore_cleanup_errors

        if globally_managed:
            assert _tempdir_manager is not None
            _tempdir_manager.enter_context(self)

    @property
    def path(self) -> str:
        assert not self._deleted, f"Attempted to access deleted path: {self._path}"
        return self._path

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.path!r}>"

    def __enter__(self: _T) -> _T:
        return self

    def __exit__(self, exc: Any, value: Any, tb: Any) -> None:
        if self.delete is not None:
            delete = self.delete
        elif _tempdir_registry:
            delete = _tempdir_registry.get_delete(self.kind)
        else:
            delete = True

        if delete:
            self.cleanup()

    def _create(self, kind: str) -> str:
        """Create a temporary directory and store its path in self.path"""
        # We realpath here because some systems have their default tmpdir
        # symlinked to another directory.  This tends to confuse build
        # scripts, so we canonicalize the path by traversing potential
        # symlinks here.
        path = os.path.realpath(tempfile.mkdtemp(prefix=f"pip-{kind}-"))
        logger.debug("Created temporary directory: %s", path)
        return path

    def cleanup(self) -> None:
        """Remove the temporary directory created and reset state"""
        self._deleted = True
        if not os.path.exists(self._path):
            return

        errors: list[BaseException] = []

        def onerror(
            func: Callable[..., Any],
            path: Path,
            exc_val: BaseException,
        ) -> None:
            """Log a warning for a `rmtree` error and continue"""
            formatted_exc = "\n".join(
                traceback.format_exception_only(type(exc_val), exc_val)
            )
            formatted_exc = formatted_exc.rstrip()  # remove trailing new line
            if func in (os.unlink, os.remove, os.rmdir):
                logger.debug(
                    "Failed to remove a temporary file '%s' due to %s.\n",
                    path,
                    formatted_exc,
                )
            else:
                logger.debug("%s failed with %s.", func.__qualname__, formatted_exc)
            errors.append(exc_val)

        if self.ignore_cleanup_errors:
            try:
                # first try with @retry; retrying to handle ephemeral errors
                rmtree(self._path, ignore_errors=False)
            except OSError:
                # last pass ignore/log all errors
                rmtree(self._path, onexc=onerror)
            if errors:
                logger.warning(
                    "Failed to remove contents in a temporary directory '%s'.\n"
                    "You can safely remove it manually.",
                    self._path,
                )
        else:
            rmtree(self._path)


class AdjacentTempDirectory(TempDirectory):
    """Helper class that creates a temporary directory adjacent to a real one.

    Attributes:
        original
            The original directory to create a temp directory for.
        path
            After calling create() or entering, contains the full
            path to the temporary directory.
        delete
            Whether the directory should be deleted when exiting
            (when used as a contextmanager)

    """

    # The characters that may be used to name the temp directory
    # We always prepend a ~ and then rotate through these until
    # a usable name is found.
    # pkg_resources raises a different error for .dist-info folder
    # with leading '-' and invalid metadata
    LEADING_CHARS = "-~.=%0123456789"

    def __init__(self, original: str, delete: bool | None = None) -> None:
        self.original = original.rstrip("/\\")
        super().__init__(delete=delete)

    @classmethod
    def _generate_names(cls, name: str) -> Generator[str, None, None]:
        """Generates a series of temporary names.

        The algorithm replaces the leading characters in the name
        with ones that are valid filesystem characters, but are not
        valid package names (for both Python and pip definitions of
        package).
        """
        for i in range(1, len(name)):
            for candidate in itertools.combinations_with_replacement(
                cls.LEADING_CHARS, i - 1
            ):
                new_name = "~" + "".join(candidate) + name[i:]
                if new_name != name:
                    yield new_name

        # If we make it this far, we will have to make a longer name
        for i in range(len(cls.LEADING_CHARS)):
            for candidate in itertools.combinations_with_replacement(
                cls.LEADING_CHARS, i
            ):
                new_name = "~" + "".join(candidate) + name
                if new_name != name:
                    yield new_name

    def _create(self, kind: str) -> str:
        root, name = os.path.split(self.original)
        for candidate in self._generate_names(name):
            path = os.path.join(root, candidate)
            try:
                os.mkdir(path)
            except OSError as ex:
                # Continue if the name exists already
                if ex.errno != errno.EEXIST:
                    raise
            else:
                path = os.path.realpath(path)
                break
        else:
            # Final fallback on the default behavior.
            path = os.path.realpath(tempfile.mkdtemp(prefix=f"pip-{kind}-"))

        logger.debug("Created temporary directory: %s", path)
        return path

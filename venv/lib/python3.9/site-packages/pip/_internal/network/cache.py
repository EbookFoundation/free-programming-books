"""HTTP cache implementation."""

from __future__ import annotations

import os
import shutil
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from typing import Any, BinaryIO, Callable

from pip._vendor.cachecontrol.cache import SeparateBodyBaseCache
from pip._vendor.cachecontrol.caches import SeparateBodyFileCache
from pip._vendor.requests.models import Response

from pip._internal.utils.filesystem import adjacent_tmp_file, replace
from pip._internal.utils.misc import ensure_dir


def is_from_cache(response: Response) -> bool:
    return getattr(response, "from_cache", False)


@contextmanager
def suppressed_cache_errors() -> Generator[None, None, None]:
    """If we can't access the cache then we can just skip caching and process
    requests as if caching wasn't enabled.
    """
    try:
        yield
    except OSError:
        pass


class SafeFileCache(SeparateBodyBaseCache):
    """
    A file based cache which is safe to use even when the target directory may
    not be accessible or writable.

    There is a race condition when two processes try to write and/or read the
    same entry at the same time, since each entry consists of two separate
    files (https://github.com/psf/cachecontrol/issues/324).  We therefore have
    additional logic that makes sure that both files to be present before
    returning an entry; this fixes the read side of the race condition.

    For the write side, we assume that the server will only ever return the
    same data for the same URL, which ought to be the case for files pip is
    downloading.  PyPI does not have a mechanism to swap out a wheel for
    another wheel, for example.  If this assumption is not true, the
    CacheControl issue will need to be fixed.
    """

    def __init__(self, directory: str) -> None:
        assert directory is not None, "Cache directory must not be None."
        super().__init__()
        self.directory = directory

    def _get_cache_path(self, name: str) -> str:
        # From cachecontrol.caches.file_cache.FileCache._fn, brought into our
        # class for backwards-compatibility and to avoid using a non-public
        # method.
        hashed = SeparateBodyFileCache.encode(name)
        parts = list(hashed[:5]) + [hashed]
        return os.path.join(self.directory, *parts)

    def get(self, key: str) -> bytes | None:
        # The cache entry is only valid if both metadata and body exist.
        metadata_path = self._get_cache_path(key)
        body_path = metadata_path + ".body"
        if not (os.path.exists(metadata_path) and os.path.exists(body_path)):
            return None
        with suppressed_cache_errors():
            with open(metadata_path, "rb") as f:
                return f.read()

    def _write_to_file(self, path: str, writer_func: Callable[[BinaryIO], Any]) -> None:
        """Common file writing logic with proper permissions and atomic replacement."""
        with suppressed_cache_errors():
            ensure_dir(os.path.dirname(path))

            with adjacent_tmp_file(path) as f:
                writer_func(f)
                # Inherit the read/write permissions of the cache directory
                # to enable multi-user cache use-cases.
                mode = (
                    os.stat(self.directory).st_mode
                    & 0o666  # select read/write permissions of cache directory
                    | 0o600  # set owner read/write permissions
                )
                # Change permissions only if there is no risk of following a symlink.
                if os.chmod in os.supports_fd:
                    os.chmod(f.fileno(), mode)
                elif os.chmod in os.supports_follow_symlinks:
                    os.chmod(f.name, mode, follow_symlinks=False)

            replace(f.name, path)

    def _write(self, path: str, data: bytes) -> None:
        self._write_to_file(path, lambda f: f.write(data))

    def _write_from_io(self, path: str, source_file: BinaryIO) -> None:
        self._write_to_file(path, lambda f: shutil.copyfileobj(source_file, f))

    def set(
        self, key: str, value: bytes, expires: int | datetime | None = None
    ) -> None:
        path = self._get_cache_path(key)
        self._write(path, value)

    def delete(self, key: str) -> None:
        path = self._get_cache_path(key)
        with suppressed_cache_errors():
            os.remove(path)
        with suppressed_cache_errors():
            os.remove(path + ".body")

    def get_body(self, key: str) -> BinaryIO | None:
        # The cache entry is only valid if both metadata and body exist.
        metadata_path = self._get_cache_path(key)
        body_path = metadata_path + ".body"
        if not (os.path.exists(metadata_path) and os.path.exists(body_path)):
            return None
        with suppressed_cache_errors():
            return open(body_path, "rb")

    def set_body(self, key: str, body: bytes) -> None:
        path = self._get_cache_path(key) + ".body"
        self._write(path, body)

    def set_body_from_io(self, key: str, body_file: BinaryIO) -> None:
        """Set the body of the cache entry from a file object."""
        path = self._get_cache_path(key) + ".body"
        self._write_from_io(path, body_file)

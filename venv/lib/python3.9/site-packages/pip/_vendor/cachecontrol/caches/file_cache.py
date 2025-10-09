# SPDX-FileCopyrightText: 2015 Eric Larson
#
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import os
import tempfile
from textwrap import dedent
from typing import IO, TYPE_CHECKING
from pathlib import Path

from pip._vendor.cachecontrol.cache import BaseCache, SeparateBodyBaseCache
from pip._vendor.cachecontrol.controller import CacheController

if TYPE_CHECKING:
    from datetime import datetime

    from filelock import BaseFileLock


class _FileCacheMixin:
    """Shared implementation for both FileCache variants."""

    def __init__(
        self,
        directory: str | Path,
        forever: bool = False,
        filemode: int = 0o0600,
        dirmode: int = 0o0700,
        lock_class: type[BaseFileLock] | None = None,
    ) -> None:
        try:
            if lock_class is None:
                from filelock import FileLock

                lock_class = FileLock
        except ImportError:
            notice = dedent(
                """
            NOTE: In order to use the FileCache you must have
            filelock installed. You can install it via pip:
              pip install cachecontrol[filecache]
            """
            )
            raise ImportError(notice)

        self.directory = directory
        self.forever = forever
        self.filemode = filemode
        self.dirmode = dirmode
        self.lock_class = lock_class

    @staticmethod
    def encode(x: str) -> str:
        return hashlib.sha224(x.encode()).hexdigest()

    def _fn(self, name: str) -> str:
        # NOTE: This method should not change as some may depend on it.
        #       See: https://github.com/ionrock/cachecontrol/issues/63
        hashed = self.encode(name)
        parts = list(hashed[:5]) + [hashed]
        return os.path.join(self.directory, *parts)

    def get(self, key: str) -> bytes | None:
        name = self._fn(key)
        try:
            with open(name, "rb") as fh:
                return fh.read()

        except FileNotFoundError:
            return None

    def set(
        self, key: str, value: bytes, expires: int | datetime | None = None
    ) -> None:
        name = self._fn(key)
        self._write(name, value)

    def _write(self, path: str, data: bytes) -> None:
        """
        Safely write the data to the given path.
        """
        # Make sure the directory exists
        dirname = os.path.dirname(path)
        os.makedirs(dirname, self.dirmode, exist_ok=True)

        with self.lock_class(path + ".lock"):
            # Write our actual file
            (fd, name) = tempfile.mkstemp(dir=dirname)
            try:
                os.write(fd, data)
            finally:
                os.close(fd)
            os.chmod(name, self.filemode)
            os.replace(name, path)

    def _delete(self, key: str, suffix: str) -> None:
        name = self._fn(key) + suffix
        if not self.forever:
            try:
                os.remove(name)
            except FileNotFoundError:
                pass


class FileCache(_FileCacheMixin, BaseCache):
    """
    Traditional FileCache: body is stored in memory, so not suitable for large
    downloads.
    """

    def delete(self, key: str) -> None:
        self._delete(key, "")


class SeparateBodyFileCache(_FileCacheMixin, SeparateBodyBaseCache):
    """
    Memory-efficient FileCache: body is stored in a separate file, reducing
    peak memory usage.
    """

    def get_body(self, key: str) -> IO[bytes] | None:
        name = self._fn(key) + ".body"
        try:
            return open(name, "rb")
        except FileNotFoundError:
            return None

    def set_body(self, key: str, body: bytes) -> None:
        name = self._fn(key) + ".body"
        self._write(name, body)

    def delete(self, key: str) -> None:
        self._delete(key, "")
        self._delete(key, ".body")


def url_to_file_path(url: str, filecache: FileCache) -> str:
    """Return the file cache path based on the URL.

    This does not ensure the file exists!
    """
    key = CacheController.cache_url(url)
    return filecache._fn(key)

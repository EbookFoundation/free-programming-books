# SPDX-FileCopyrightText: 2015 Eric Larson
#
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import mmap
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from http.client import HTTPResponse


class CallbackFileWrapper:
    """
    Small wrapper around a fp object which will tee everything read into a
    buffer, and when that file is closed it will execute a callback with the
    contents of that buffer.

    All attributes are proxied to the underlying file object.

    This class uses members with a double underscore (__) leading prefix so as
    not to accidentally shadow an attribute.

    The data is stored in a temporary file until it is all available.  As long
    as the temporary files directory is disk-based (sometimes it's a
    memory-backed-``tmpfs`` on Linux), data will be unloaded to disk if memory
    pressure is high.  For small files the disk usually won't be used at all,
    it'll all be in the filesystem memory cache, so there should be no
    performance impact.
    """

    def __init__(
        self, fp: HTTPResponse, callback: Callable[[bytes], None] | None
    ) -> None:
        self.__buf = NamedTemporaryFile("rb+", delete=True)
        self.__fp = fp
        self.__callback = callback

    def __getattr__(self, name: str) -> Any:
        # The vagaries of garbage collection means that self.__fp is
        # not always set.  By using __getattribute__ and the private
        # name[0] allows looking up the attribute value and raising an
        # AttributeError when it doesn't exist. This stop things from
        # infinitely recursing calls to getattr in the case where
        # self.__fp hasn't been set.
        #
        # [0] https://docs.python.org/2/reference/expressions.html#atom-identifiers
        fp = self.__getattribute__("_CallbackFileWrapper__fp")
        return getattr(fp, name)

    def __is_fp_closed(self) -> bool:
        try:
            return self.__fp.fp is None

        except AttributeError:
            pass

        try:
            closed: bool = self.__fp.closed
            return closed

        except AttributeError:
            pass

        # We just don't cache it then.
        # TODO: Add some logging here...
        return False

    def _close(self) -> None:
        if self.__callback:
            if self.__buf.tell() == 0:
                # Empty file:
                result = b""
            else:
                # Return the data without actually loading it into memory,
                # relying on Python's buffer API and mmap(). mmap() just gives
                # a view directly into the filesystem's memory cache, so it
                # doesn't result in duplicate memory use.
                self.__buf.seek(0, 0)
                result = memoryview(
                    mmap.mmap(self.__buf.fileno(), 0, access=mmap.ACCESS_READ)
                )
            self.__callback(result)

        # We assign this to None here, because otherwise we can get into
        # really tricky problems where the CPython interpreter dead locks
        # because the callback is holding a reference to something which
        # has a __del__ method. Setting this to None breaks the cycle
        # and allows the garbage collector to do it's thing normally.
        self.__callback = None

        # Closing the temporary file releases memory and frees disk space.
        # Important when caching big files.
        self.__buf.close()

    def read(self, amt: int | None = None) -> bytes:
        data: bytes = self.__fp.read(amt)
        if data:
            # We may be dealing with b'', a sign that things are over:
            # it's passed e.g. after we've already closed self.__buf.
            self.__buf.write(data)
        if self.__is_fp_closed():
            self._close()

        return data

    def _safe_read(self, amt: int) -> bytes:
        data: bytes = self.__fp._safe_read(amt)  # type: ignore[attr-defined]
        if amt == 2 and data == b"\r\n":
            # urllib executes this read to toss the CRLF at the end
            # of the chunk.
            return data

        self.__buf.write(data)
        if self.__is_fp_closed():
            self._close()

        return data

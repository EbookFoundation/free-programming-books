# SPDX-FileCopyrightText: 2015 Eric Larson
#
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations


from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pip._vendor.cachecontrol.cache import BaseCache

if TYPE_CHECKING:
    from redis import Redis


class RedisCache(BaseCache):
    def __init__(self, conn: Redis[bytes]) -> None:
        self.conn = conn

    def get(self, key: str) -> bytes | None:
        return self.conn.get(key)

    def set(
        self, key: str, value: bytes, expires: int | datetime | None = None
    ) -> None:
        if not expires:
            self.conn.set(key, value)
        elif isinstance(expires, datetime):
            now_utc = datetime.now(timezone.utc)
            if expires.tzinfo is None:
                now_utc = now_utc.replace(tzinfo=None)
            delta = expires - now_utc
            self.conn.setex(key, int(delta.total_seconds()), value)
        else:
            self.conn.setex(key, expires, value)

    def delete(self, key: str) -> None:
        self.conn.delete(key)

    def clear(self) -> None:
        """Helper for clearing all the keys in a database. Use with
        caution!"""
        for key in self.conn.keys():
            self.conn.delete(key)

    def close(self) -> None:
        """Redis uses connection pooling, no need to close the connection."""
        pass

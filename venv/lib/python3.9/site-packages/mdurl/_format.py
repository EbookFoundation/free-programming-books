from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mdurl._url import URL


def format(url: URL) -> str:  # noqa: A001
    result = ""

    result += url.protocol or ""
    result += "//" if url.slashes else ""
    result += url.auth + "@" if url.auth else ""

    if url.hostname and ":" in url.hostname:
        # ipv6 address
        result += "[" + url.hostname + "]"
    else:
        result += url.hostname or ""

    result += ":" + url.port if url.port else ""
    result += url.pathname or ""
    result += url.search or ""
    result += url.hash or ""

    return result

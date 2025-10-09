from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
import re
from urllib.parse import quote, unquote, urlparse, urlunparse  # noqa: F401

import mdurl

from .. import _punycode

RECODE_HOSTNAME_FOR = ("http:", "https:", "mailto:")


def normalizeLink(url: str) -> str:
    """Normalize destination URLs in links

    ::

        [label]:   destination   'title'
                ^^^^^^^^^^^
    """
    parsed = mdurl.parse(url, slashes_denote_host=True)

    # Encode hostnames in urls like:
    # `http://host/`, `https://host/`, `mailto:user@host`, `//host/`
    #
    # We don't encode unknown schemas, because it's likely that we encode
    # something we shouldn't (e.g. `skype:name` treated as `skype:host`)
    #
    if parsed.hostname and (
        not parsed.protocol or parsed.protocol in RECODE_HOSTNAME_FOR
    ):
        with suppress(Exception):
            parsed = parsed._replace(hostname=_punycode.to_ascii(parsed.hostname))

    return mdurl.encode(mdurl.format(parsed))


def normalizeLinkText(url: str) -> str:
    """Normalize autolink content

    ::

        <destination>
         ~~~~~~~~~~~
    """
    parsed = mdurl.parse(url, slashes_denote_host=True)

    # Encode hostnames in urls like:
    # `http://host/`, `https://host/`, `mailto:user@host`, `//host/`
    #
    # We don't encode unknown schemas, because it's likely that we encode
    # something we shouldn't (e.g. `skype:name` treated as `skype:host`)
    #
    if parsed.hostname and (
        not parsed.protocol or parsed.protocol in RECODE_HOSTNAME_FOR
    ):
        with suppress(Exception):
            parsed = parsed._replace(hostname=_punycode.to_unicode(parsed.hostname))

    # add '%' to exclude list because of https://github.com/markdown-it/markdown-it/issues/720
    return mdurl.decode(mdurl.format(parsed), mdurl.DECODE_DEFAULT_CHARS + "%")


BAD_PROTO_RE = re.compile(r"^(vbscript|javascript|file|data):")
GOOD_DATA_RE = re.compile(r"^data:image\/(gif|png|jpeg|webp);")


def validateLink(url: str, validator: Callable[[str], bool] | None = None) -> bool:
    """Validate URL link is allowed in output.

    This validator can prohibit more than really needed to prevent XSS.
    It's a tradeoff to keep code simple and to be secure by default.

    Note: url should be normalized at this point, and existing entities decoded.
    """
    if validator is not None:
        return validator(url)
    url = url.strip().lower()
    return bool(GOOD_DATA_RE.search(url)) if BAD_PROTO_RE.search(url) else True

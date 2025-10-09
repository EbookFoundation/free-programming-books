import itertools
import logging
import os
import posixpath
import urllib.parse
from dataclasses import dataclass

from pip._vendor.packaging.utils import canonicalize_name

from pip._internal.models.index import PyPI
from pip._internal.utils.compat import has_tls
from pip._internal.utils.misc import normalize_path, redact_auth_from_url

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchScope:
    """
    Encapsulates the locations that pip is configured to search.
    """

    __slots__ = ["find_links", "index_urls", "no_index"]

    find_links: list[str]
    index_urls: list[str]
    no_index: bool

    @classmethod
    def create(
        cls,
        find_links: list[str],
        index_urls: list[str],
        no_index: bool,
    ) -> "SearchScope":
        """
        Create a SearchScope object after normalizing the `find_links`.
        """
        # Build find_links. If an argument starts with ~, it may be
        # a local file relative to a home directory. So try normalizing
        # it and if it exists, use the normalized version.
        # This is deliberately conservative - it might be fine just to
        # blindly normalize anything starting with a ~...
        built_find_links: list[str] = []
        for link in find_links:
            if link.startswith("~"):
                new_link = normalize_path(link)
                if os.path.exists(new_link):
                    link = new_link
            built_find_links.append(link)

        # If we don't have TLS enabled, then WARN if anyplace we're looking
        # relies on TLS.
        if not has_tls():
            for link in itertools.chain(index_urls, built_find_links):
                parsed = urllib.parse.urlparse(link)
                if parsed.scheme == "https":
                    logger.warning(
                        "pip is configured with locations that require "
                        "TLS/SSL, however the ssl module in Python is not "
                        "available."
                    )
                    break

        return cls(
            find_links=built_find_links,
            index_urls=index_urls,
            no_index=no_index,
        )

    def get_formatted_locations(self) -> str:
        lines = []
        redacted_index_urls = []
        if self.index_urls and self.index_urls != [PyPI.simple_url]:
            for url in self.index_urls:
                redacted_index_url = redact_auth_from_url(url)

                # Parse the URL
                purl = urllib.parse.urlsplit(redacted_index_url)

                # URL is generally invalid if scheme and netloc is missing
                # there are issues with Python and URL parsing, so this test
                # is a bit crude. See bpo-20271, bpo-23505. Python doesn't
                # always parse invalid URLs correctly - it should raise
                # exceptions for malformed URLs
                if not purl.scheme and not purl.netloc:
                    logger.warning(
                        'The index url "%s" seems invalid, please provide a scheme.',
                        redacted_index_url,
                    )

                redacted_index_urls.append(redacted_index_url)

            lines.append(
                "Looking in indexes: {}".format(", ".join(redacted_index_urls))
            )

        if self.find_links:
            lines.append(
                "Looking in links: {}".format(
                    ", ".join(redact_auth_from_url(url) for url in self.find_links)
                )
            )
        return "\n".join(lines)

    def get_index_urls_locations(self, project_name: str) -> list[str]:
        """Returns the locations found via self.index_urls

        Checks the url_name on the main (first in the list) index and
        use this url_name to produce all locations
        """

        def mkurl_pypi_url(url: str) -> str:
            loc = posixpath.join(
                url, urllib.parse.quote(canonicalize_name(project_name))
            )
            # For maximum compatibility with easy_install, ensure the path
            # ends in a trailing slash.  Although this isn't in the spec
            # (and PyPI can handle it without the slash) some other index
            # implementations might break if they relied on easy_install's
            # behavior.
            if not loc.endswith("/"):
                loc = loc + "/"
            return loc

        return [mkurl_pypi_url(url) for url in self.index_urls]

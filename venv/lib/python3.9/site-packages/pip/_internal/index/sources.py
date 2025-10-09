from __future__ import annotations

import logging
import mimetypes
import os
from collections import defaultdict
from collections.abc import Iterable
from typing import Callable

from pip._vendor.packaging.utils import (
    InvalidSdistFilename,
    InvalidWheelFilename,
    canonicalize_name,
    parse_sdist_filename,
    parse_wheel_filename,
)

from pip._internal.models.candidate import InstallationCandidate
from pip._internal.models.link import Link
from pip._internal.utils.urls import path_to_url, url_to_path
from pip._internal.vcs import is_url

logger = logging.getLogger(__name__)

FoundCandidates = Iterable[InstallationCandidate]
FoundLinks = Iterable[Link]
CandidatesFromPage = Callable[[Link], Iterable[InstallationCandidate]]
PageValidator = Callable[[Link], bool]


class LinkSource:
    @property
    def link(self) -> Link | None:
        """Returns the underlying link, if there's one."""
        raise NotImplementedError()

    def page_candidates(self) -> FoundCandidates:
        """Candidates found by parsing an archive listing HTML file."""
        raise NotImplementedError()

    def file_links(self) -> FoundLinks:
        """Links found by specifying archives directly."""
        raise NotImplementedError()


def _is_html_file(file_url: str) -> bool:
    return mimetypes.guess_type(file_url, strict=False)[0] == "text/html"


class _FlatDirectoryToUrls:
    """Scans directory and caches results"""

    def __init__(self, path: str) -> None:
        self._path = path
        self._page_candidates: list[str] = []
        self._project_name_to_urls: dict[str, list[str]] = defaultdict(list)
        self._scanned_directory = False

    def _scan_directory(self) -> None:
        """Scans directory once and populates both page_candidates
        and project_name_to_urls at the same time
        """
        for entry in os.scandir(self._path):
            url = path_to_url(entry.path)
            if _is_html_file(url):
                self._page_candidates.append(url)
                continue

            # File must have a valid wheel or sdist name,
            # otherwise not worth considering as a package
            try:
                project_filename = parse_wheel_filename(entry.name)[0]
            except InvalidWheelFilename:
                try:
                    project_filename = parse_sdist_filename(entry.name)[0]
                except InvalidSdistFilename:
                    continue

            self._project_name_to_urls[project_filename].append(url)
        self._scanned_directory = True

    @property
    def page_candidates(self) -> list[str]:
        if not self._scanned_directory:
            self._scan_directory()

        return self._page_candidates

    @property
    def project_name_to_urls(self) -> dict[str, list[str]]:
        if not self._scanned_directory:
            self._scan_directory()

        return self._project_name_to_urls


class _FlatDirectorySource(LinkSource):
    """Link source specified by ``--find-links=<path-to-dir>``.

    This looks the content of the directory, and returns:

    * ``page_candidates``: Links listed on each HTML file in the directory.
    * ``file_candidates``: Archives in the directory.
    """

    _paths_to_urls: dict[str, _FlatDirectoryToUrls] = {}

    def __init__(
        self,
        candidates_from_page: CandidatesFromPage,
        path: str,
        project_name: str,
    ) -> None:
        self._candidates_from_page = candidates_from_page
        self._project_name = canonicalize_name(project_name)

        # Get existing instance of _FlatDirectoryToUrls if it exists
        if path in self._paths_to_urls:
            self._path_to_urls = self._paths_to_urls[path]
        else:
            self._path_to_urls = _FlatDirectoryToUrls(path=path)
            self._paths_to_urls[path] = self._path_to_urls

    @property
    def link(self) -> Link | None:
        return None

    def page_candidates(self) -> FoundCandidates:
        for url in self._path_to_urls.page_candidates:
            yield from self._candidates_from_page(Link(url))

    def file_links(self) -> FoundLinks:
        for url in self._path_to_urls.project_name_to_urls[self._project_name]:
            yield Link(url)


class _LocalFileSource(LinkSource):
    """``--find-links=<path-or-url>`` or ``--[extra-]index-url=<path-or-url>``.

    If a URL is supplied, it must be a ``file:`` URL. If a path is supplied to
    the option, it is converted to a URL first. This returns:

    * ``page_candidates``: Links listed on an HTML file.
    * ``file_candidates``: The non-HTML file.
    """

    def __init__(
        self,
        candidates_from_page: CandidatesFromPage,
        link: Link,
    ) -> None:
        self._candidates_from_page = candidates_from_page
        self._link = link

    @property
    def link(self) -> Link | None:
        return self._link

    def page_candidates(self) -> FoundCandidates:
        if not _is_html_file(self._link.url):
            return
        yield from self._candidates_from_page(self._link)

    def file_links(self) -> FoundLinks:
        if _is_html_file(self._link.url):
            return
        yield self._link


class _RemoteFileSource(LinkSource):
    """``--find-links=<url>`` or ``--[extra-]index-url=<url>``.

    This returns:

    * ``page_candidates``: Links listed on an HTML file.
    * ``file_candidates``: The non-HTML file.
    """

    def __init__(
        self,
        candidates_from_page: CandidatesFromPage,
        page_validator: PageValidator,
        link: Link,
    ) -> None:
        self._candidates_from_page = candidates_from_page
        self._page_validator = page_validator
        self._link = link

    @property
    def link(self) -> Link | None:
        return self._link

    def page_candidates(self) -> FoundCandidates:
        if not self._page_validator(self._link):
            return
        yield from self._candidates_from_page(self._link)

    def file_links(self) -> FoundLinks:
        yield self._link


class _IndexDirectorySource(LinkSource):
    """``--[extra-]index-url=<path-to-directory>``.

    This is treated like a remote URL; ``candidates_from_page`` contains logic
    for this by appending ``index.html`` to the link.
    """

    def __init__(
        self,
        candidates_from_page: CandidatesFromPage,
        link: Link,
    ) -> None:
        self._candidates_from_page = candidates_from_page
        self._link = link

    @property
    def link(self) -> Link | None:
        return self._link

    def page_candidates(self) -> FoundCandidates:
        yield from self._candidates_from_page(self._link)

    def file_links(self) -> FoundLinks:
        return ()


def build_source(
    location: str,
    *,
    candidates_from_page: CandidatesFromPage,
    page_validator: PageValidator,
    expand_dir: bool,
    cache_link_parsing: bool,
    project_name: str,
) -> tuple[str | None, LinkSource | None]:
    path: str | None = None
    url: str | None = None
    if os.path.exists(location):  # Is a local path.
        url = path_to_url(location)
        path = location
    elif location.startswith("file:"):  # A file: URL.
        url = location
        path = url_to_path(location)
    elif is_url(location):
        url = location

    if url is None:
        msg = (
            "Location '%s' is ignored: "
            "it is either a non-existing path or lacks a specific scheme."
        )
        logger.warning(msg, location)
        return (None, None)

    if path is None:
        source: LinkSource = _RemoteFileSource(
            candidates_from_page=candidates_from_page,
            page_validator=page_validator,
            link=Link(url, cache_link_parsing=cache_link_parsing),
        )
        return (url, source)

    if os.path.isdir(path):
        if expand_dir:
            source = _FlatDirectorySource(
                candidates_from_page=candidates_from_page,
                path=path,
                project_name=project_name,
            )
        else:
            source = _IndexDirectorySource(
                candidates_from_page=candidates_from_page,
                link=Link(url, cache_link_parsing=cache_link_parsing),
            )
        return (url, source)
    elif os.path.isfile(path):
        source = _LocalFileSource(
            candidates_from_page=candidates_from_page,
            link=Link(url, cache_link_parsing=cache_link_parsing),
        )
        return (url, source)
    logger.warning(
        "Location '%s' is ignored: it is neither a file nor a directory.",
        location,
    )
    return (url, None)

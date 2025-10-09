"""Download files with progress indicators."""

from __future__ import annotations

import email.message
import logging
import mimetypes
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from http import HTTPStatus
from typing import BinaryIO

from pip._vendor.requests import PreparedRequest
from pip._vendor.requests.models import Response
from pip._vendor.urllib3 import HTTPResponse as URLlib3Response
from pip._vendor.urllib3._collections import HTTPHeaderDict
from pip._vendor.urllib3.exceptions import ReadTimeoutError

from pip._internal.cli.progress_bars import BarType, get_download_progress_renderer
from pip._internal.exceptions import IncompleteDownloadError, NetworkConnectionError
from pip._internal.models.index import PyPI
from pip._internal.models.link import Link
from pip._internal.network.cache import SafeFileCache, is_from_cache
from pip._internal.network.session import CacheControlAdapter, PipSession
from pip._internal.network.utils import HEADERS, raise_for_status, response_chunks
from pip._internal.utils.misc import format_size, redact_auth_from_url, splitext

logger = logging.getLogger(__name__)


def _get_http_response_size(resp: Response) -> int | None:
    try:
        return int(resp.headers["content-length"])
    except (ValueError, KeyError, TypeError):
        return None


def _get_http_response_etag_or_last_modified(resp: Response) -> str | None:
    """
    Return either the ETag or Last-Modified header (or None if neither exists).
    The return value can be used in an If-Range header.
    """
    return resp.headers.get("etag", resp.headers.get("last-modified"))


def _log_download(
    resp: Response,
    link: Link,
    progress_bar: BarType,
    total_length: int | None,
    range_start: int | None = 0,
) -> Iterable[bytes]:
    if link.netloc == PyPI.file_storage_domain:
        url = link.show_url
    else:
        url = link.url_without_fragment

    logged_url = redact_auth_from_url(url)

    if total_length:
        if range_start:
            logged_url = (
                f"{logged_url} ({format_size(range_start)}/{format_size(total_length)})"
            )
        else:
            logged_url = f"{logged_url} ({format_size(total_length)})"

    if is_from_cache(resp):
        logger.info("Using cached %s", logged_url)
    elif range_start:
        logger.info("Resuming download %s", logged_url)
    else:
        logger.info("Downloading %s", logged_url)

    if logger.getEffectiveLevel() > logging.INFO:
        show_progress = False
    elif is_from_cache(resp):
        show_progress = False
    elif not total_length:
        show_progress = True
    elif total_length > (512 * 1024):
        show_progress = True
    else:
        show_progress = False

    chunks = response_chunks(resp)

    if not show_progress:
        return chunks

    renderer = get_download_progress_renderer(
        bar_type=progress_bar, size=total_length, initial_progress=range_start
    )
    return renderer(chunks)


def sanitize_content_filename(filename: str) -> str:
    """
    Sanitize the "filename" value from a Content-Disposition header.
    """
    return os.path.basename(filename)


def parse_content_disposition(content_disposition: str, default_filename: str) -> str:
    """
    Parse the "filename" value from a Content-Disposition header, and
    return the default filename if the result is empty.
    """
    m = email.message.Message()
    m["content-type"] = content_disposition
    filename = m.get_param("filename")
    if filename:
        # We need to sanitize the filename to prevent directory traversal
        # in case the filename contains ".." path parts.
        filename = sanitize_content_filename(str(filename))
    return filename or default_filename


def _get_http_response_filename(resp: Response, link: Link) -> str:
    """Get an ideal filename from the given HTTP response, falling back to
    the link filename if not provided.
    """
    filename = link.filename  # fallback
    # Have a look at the Content-Disposition header for a better guess
    content_disposition = resp.headers.get("content-disposition")
    if content_disposition:
        filename = parse_content_disposition(content_disposition, filename)
    ext: str | None = splitext(filename)[1]
    if not ext:
        ext = mimetypes.guess_extension(resp.headers.get("content-type", ""))
        if ext:
            filename += ext
    if not ext and link.url != resp.url:
        ext = os.path.splitext(resp.url)[1]
        if ext:
            filename += ext
    return filename


@dataclass
class _FileDownload:
    """Stores the state of a single link download."""

    link: Link
    output_file: BinaryIO
    size: int | None
    bytes_received: int = 0
    reattempts: int = 0

    def is_incomplete(self) -> bool:
        return bool(self.size is not None and self.bytes_received < self.size)

    def write_chunk(self, data: bytes) -> None:
        self.bytes_received += len(data)
        self.output_file.write(data)

    def reset_file(self) -> None:
        """Delete any saved data and reset progress to zero."""
        self.output_file.seek(0)
        self.output_file.truncate()
        self.bytes_received = 0


class Downloader:
    def __init__(
        self,
        session: PipSession,
        progress_bar: BarType,
        resume_retries: int,
    ) -> None:
        assert (
            resume_retries >= 0
        ), "Number of max resume retries must be bigger or equal to zero"
        self._session = session
        self._progress_bar = progress_bar
        self._resume_retries = resume_retries

    def batch(
        self, links: Iterable[Link], location: str
    ) -> Iterable[tuple[Link, tuple[str, str]]]:
        """Convenience method to download multiple links."""
        for link in links:
            filepath, content_type = self(link, location)
            yield link, (filepath, content_type)

    def __call__(self, link: Link, location: str) -> tuple[str, str]:
        """Download a link and save it under location."""
        resp = self._http_get(link)
        download_size = _get_http_response_size(resp)

        filepath = os.path.join(location, _get_http_response_filename(resp, link))
        with open(filepath, "wb") as content_file:
            download = _FileDownload(link, content_file, download_size)
            self._process_response(download, resp)
            if download.is_incomplete():
                self._attempt_resumes_or_redownloads(download, resp)

        content_type = resp.headers.get("Content-Type", "")
        return filepath, content_type

    def _process_response(self, download: _FileDownload, resp: Response) -> None:
        """Download and save chunks from a response."""
        chunks = _log_download(
            resp,
            download.link,
            self._progress_bar,
            download.size,
            range_start=download.bytes_received,
        )
        try:
            for chunk in chunks:
                download.write_chunk(chunk)
        except ReadTimeoutError as e:
            # If the download size is not known, then give up downloading the file.
            if download.size is None:
                raise e

            logger.warning("Connection timed out while downloading.")

    def _attempt_resumes_or_redownloads(
        self, download: _FileDownload, first_resp: Response
    ) -> None:
        """Attempt to resume/restart the download if connection was dropped."""

        while download.reattempts < self._resume_retries and download.is_incomplete():
            assert download.size is not None
            download.reattempts += 1
            logger.warning(
                "Attempting to resume incomplete download (%s/%s, attempt %d)",
                format_size(download.bytes_received),
                format_size(download.size),
                download.reattempts,
            )

            try:
                resume_resp = self._http_get_resume(download, should_match=first_resp)
                # Fallback: if the server responded with 200 (i.e., the file has
                # since been modified or range requests are unsupported) or any
                # other unexpected status, restart the download from the beginning.
                must_restart = resume_resp.status_code != HTTPStatus.PARTIAL_CONTENT
                if must_restart:
                    download.reset_file()
                    download.size = _get_http_response_size(resume_resp)
                    first_resp = resume_resp

                self._process_response(download, resume_resp)
            except (ConnectionError, ReadTimeoutError, OSError):
                continue

        # No more resume attempts. Raise an error if the download is still incomplete.
        if download.is_incomplete():
            os.remove(download.output_file.name)
            raise IncompleteDownloadError(download)

        # If we successfully completed the download via resume, manually cache it
        # as a complete response to enable future caching
        if download.reattempts > 0:
            self._cache_resumed_download(download, first_resp)

    def _cache_resumed_download(
        self, download: _FileDownload, original_response: Response
    ) -> None:
        """
        Manually cache a file that was successfully downloaded via resume retries.

        cachecontrol doesn't cache 206 (Partial Content) responses, since they
        are not complete files. This method manually adds the final file to the
        cache as though it was downloaded in a single request, so that future
        requests can use the cache.
        """
        url = download.link.url_without_fragment
        adapter = self._session.get_adapter(url)

        # Check if the adapter is the CacheControlAdapter (i.e. caching is enabled)
        if not isinstance(adapter, CacheControlAdapter):
            logger.debug(
                "Skipping resume download caching: no cache controller for %s", url
            )
            return

        # Check SafeFileCache is being used
        assert isinstance(
            adapter.cache, SafeFileCache
        ), "separate body cache not in use!"

        synthetic_request = PreparedRequest()
        synthetic_request.prepare(method="GET", url=url, headers={})

        synthetic_response_headers = HTTPHeaderDict()
        for key, value in original_response.headers.items():
            if key.lower() not in ["content-range", "content-length"]:
                synthetic_response_headers[key] = value
        synthetic_response_headers["content-length"] = str(download.size)

        synthetic_response = URLlib3Response(
            body="",
            headers=synthetic_response_headers,
            status=200,
            preload_content=False,
        )

        # Save metadata and then stream the file contents to cache.
        cache_url = adapter.controller.cache_url(url)
        metadata_blob = adapter.controller.serializer.dumps(
            synthetic_request, synthetic_response, b""
        )
        adapter.cache.set(cache_url, metadata_blob)
        download.output_file.flush()
        with open(download.output_file.name, "rb") as f:
            adapter.cache.set_body_from_io(cache_url, f)

        logger.debug(
            "Cached resumed download as complete response for future use: %s", url
        )

    def _http_get_resume(
        self, download: _FileDownload, should_match: Response
    ) -> Response:
        """Issue a HTTP range request to resume the download."""
        # To better understand the download resumption logic, see the mdn web docs:
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Range_requests
        headers = HEADERS.copy()
        headers["Range"] = f"bytes={download.bytes_received}-"
        # If possible, use a conditional range request to avoid corrupted
        # downloads caused by the remote file changing in-between.
        if identifier := _get_http_response_etag_or_last_modified(should_match):
            headers["If-Range"] = identifier
        return self._http_get(download.link, headers)

    def _http_get(self, link: Link, headers: Mapping[str, str] = HEADERS) -> Response:
        target_url = link.url_without_fragment
        try:
            resp = self._session.get(target_url, headers=headers, stream=True)
            raise_for_status(resp)
        except NetworkConnectionError as e:
            assert e.response is not None
            logger.critical(
                "HTTP error %s while getting %s", e.response.status_code, link
            )
            raise
        return resp

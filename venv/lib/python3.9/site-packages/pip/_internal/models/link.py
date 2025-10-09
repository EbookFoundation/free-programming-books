from __future__ import annotations

import functools
import itertools
import logging
import os
import posixpath
import re
import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    NamedTuple,
)

from pip._internal.utils.deprecation import deprecated
from pip._internal.utils.filetypes import WHEEL_EXTENSION
from pip._internal.utils.hashes import Hashes
from pip._internal.utils.misc import (
    pairwise,
    redact_auth_from_url,
    split_auth_from_netloc,
    splitext,
)
from pip._internal.utils.urls import path_to_url, url_to_path

if TYPE_CHECKING:
    from pip._internal.index.collector import IndexContent

logger = logging.getLogger(__name__)


# Order matters, earlier hashes have a precedence over later hashes for what
# we will pick to use.
_SUPPORTED_HASHES = ("sha512", "sha384", "sha256", "sha224", "sha1", "md5")


@dataclass(frozen=True)
class LinkHash:
    """Links to content may have embedded hash values. This class parses those.

    `name` must be any member of `_SUPPORTED_HASHES`.

    This class can be converted to and from `ArchiveInfo`. While ArchiveInfo intends to
    be JSON-serializable to conform to PEP 610, this class contains the logic for
    parsing a hash name and value for correctness, and then checking whether that hash
    conforms to a schema with `.is_hash_allowed()`."""

    name: str
    value: str

    _hash_url_fragment_re = re.compile(
        # NB: we do not validate that the second group (.*) is a valid hex
        # digest. Instead, we simply keep that string in this class, and then check it
        # against Hashes when hash-checking is needed. This is easier to debug than
        # proactively discarding an invalid hex digest, as we handle incorrect hashes
        # and malformed hashes in the same place.
        r"[#&]({choices})=([^&]*)".format(
            choices="|".join(re.escape(hash_name) for hash_name in _SUPPORTED_HASHES)
        ),
    )

    def __post_init__(self) -> None:
        assert self.name in _SUPPORTED_HASHES

    @classmethod
    @functools.cache
    def find_hash_url_fragment(cls, url: str) -> LinkHash | None:
        """Search a string for a checksum algorithm name and encoded output value."""
        match = cls._hash_url_fragment_re.search(url)
        if match is None:
            return None
        name, value = match.groups()
        return cls(name=name, value=value)

    def as_dict(self) -> dict[str, str]:
        return {self.name: self.value}

    def as_hashes(self) -> Hashes:
        """Return a Hashes instance which checks only for the current hash."""
        return Hashes({self.name: [self.value]})

    def is_hash_allowed(self, hashes: Hashes | None) -> bool:
        """
        Return True if the current hash is allowed by `hashes`.
        """
        if hashes is None:
            return False
        return hashes.is_hash_allowed(self.name, hex_digest=self.value)


@dataclass(frozen=True)
class MetadataFile:
    """Information about a core metadata file associated with a distribution."""

    hashes: dict[str, str] | None

    def __post_init__(self) -> None:
        if self.hashes is not None:
            assert all(name in _SUPPORTED_HASHES for name in self.hashes)


def supported_hashes(hashes: dict[str, str] | None) -> dict[str, str] | None:
    # Remove any unsupported hash types from the mapping. If this leaves no
    # supported hashes, return None
    if hashes is None:
        return None
    hashes = {n: v for n, v in hashes.items() if n in _SUPPORTED_HASHES}
    if not hashes:
        return None
    return hashes


def _clean_url_path_part(part: str) -> str:
    """
    Clean a "part" of a URL path (i.e. after splitting on "@" characters).
    """
    # We unquote prior to quoting to make sure nothing is double quoted.
    return urllib.parse.quote(urllib.parse.unquote(part))


def _clean_file_url_path(part: str) -> str:
    """
    Clean the first part of a URL path that corresponds to a local
    filesystem path (i.e. the first part after splitting on "@" characters).
    """
    # We unquote prior to quoting to make sure nothing is double quoted.
    # Also, on Windows the path part might contain a drive letter which
    # should not be quoted. On Linux where drive letters do not
    # exist, the colon should be quoted. We rely on urllib.request
    # to do the right thing here.
    ret = urllib.request.pathname2url(urllib.request.url2pathname(part))
    if ret.startswith("///"):
        # Remove any URL authority section, leaving only the URL path.
        ret = ret.removeprefix("//")
    return ret


# percent-encoded:                   /
_reserved_chars_re = re.compile("(@|%2F)", re.IGNORECASE)


def _clean_url_path(path: str, is_local_path: bool) -> str:
    """
    Clean the path portion of a URL.
    """
    if is_local_path:
        clean_func = _clean_file_url_path
    else:
        clean_func = _clean_url_path_part

    # Split on the reserved characters prior to cleaning so that
    # revision strings in VCS URLs are properly preserved.
    parts = _reserved_chars_re.split(path)

    cleaned_parts = []
    for to_clean, reserved in pairwise(itertools.chain(parts, [""])):
        cleaned_parts.append(clean_func(to_clean))
        # Normalize %xx escapes (e.g. %2f -> %2F)
        cleaned_parts.append(reserved.upper())

    return "".join(cleaned_parts)


def _ensure_quoted_url(url: str) -> str:
    """
    Make sure a link is fully quoted.
    For example, if ' ' occurs in the URL, it will be replaced with "%20",
    and without double-quoting other characters.
    """
    # Split the URL into parts according to the general structure
    # `scheme://netloc/path?query#fragment`.
    result = urllib.parse.urlsplit(url)
    # If the netloc is empty, then the URL refers to a local filesystem path.
    is_local_path = not result.netloc
    path = _clean_url_path(result.path, is_local_path=is_local_path)
    # Temporarily replace scheme with file to ensure the URL generated by
    # urlunsplit() contains an empty netloc (file://) as per RFC 1738.
    ret = urllib.parse.urlunsplit(result._replace(scheme="file", path=path))
    ret = result.scheme + ret[4:]  # Restore original scheme.
    return ret


def _absolute_link_url(base_url: str, url: str) -> str:
    """
    A faster implementation of urllib.parse.urljoin with a shortcut
    for absolute http/https URLs.
    """
    if url.startswith(("https://", "http://")):
        return url
    else:
        return urllib.parse.urljoin(base_url, url)


@functools.total_ordering
class Link:
    """Represents a parsed link from a Package Index's simple URL"""

    __slots__ = [
        "_parsed_url",
        "_url",
        "_path",
        "_hashes",
        "comes_from",
        "requires_python",
        "yanked_reason",
        "metadata_file_data",
        "cache_link_parsing",
        "egg_fragment",
    ]

    def __init__(
        self,
        url: str,
        comes_from: str | IndexContent | None = None,
        requires_python: str | None = None,
        yanked_reason: str | None = None,
        metadata_file_data: MetadataFile | None = None,
        cache_link_parsing: bool = True,
        hashes: Mapping[str, str] | None = None,
    ) -> None:
        """
        :param url: url of the resource pointed to (href of the link)
        :param comes_from: instance of IndexContent where the link was found,
            or string.
        :param requires_python: String containing the `Requires-Python`
            metadata field, specified in PEP 345. This may be specified by
            a data-requires-python attribute in the HTML link tag, as
            described in PEP 503.
        :param yanked_reason: the reason the file has been yanked, if the
            file has been yanked, or None if the file hasn't been yanked.
            This is the value of the "data-yanked" attribute, if present, in
            a simple repository HTML link. If the file has been yanked but
            no reason was provided, this should be the empty string. See
            PEP 592 for more information and the specification.
        :param metadata_file_data: the metadata attached to the file, or None if
            no such metadata is provided. This argument, if not None, indicates
            that a separate metadata file exists, and also optionally supplies
            hashes for that file.
        :param cache_link_parsing: A flag that is used elsewhere to determine
            whether resources retrieved from this link should be cached. PyPI
            URLs should generally have this set to False, for example.
        :param hashes: A mapping of hash names to digests to allow us to
            determine the validity of a download.
        """

        # The comes_from, requires_python, and metadata_file_data arguments are
        # only used by classmethods of this class, and are not used in client
        # code directly.

        # url can be a UNC windows share
        if url.startswith("\\\\"):
            url = path_to_url(url)

        self._parsed_url = urllib.parse.urlsplit(url)
        # Store the url as a private attribute to prevent accidentally
        # trying to set a new value.
        self._url = url
        # The .path property is hot, so calculate its value ahead of time.
        self._path = urllib.parse.unquote(self._parsed_url.path)

        link_hash = LinkHash.find_hash_url_fragment(url)
        hashes_from_link = {} if link_hash is None else link_hash.as_dict()
        if hashes is None:
            self._hashes = hashes_from_link
        else:
            self._hashes = {**hashes, **hashes_from_link}

        self.comes_from = comes_from
        self.requires_python = requires_python if requires_python else None
        self.yanked_reason = yanked_reason
        self.metadata_file_data = metadata_file_data

        self.cache_link_parsing = cache_link_parsing
        self.egg_fragment = self._egg_fragment()

    @classmethod
    def from_json(
        cls,
        file_data: dict[str, Any],
        page_url: str,
    ) -> Link | None:
        """
        Convert an pypi json document from a simple repository page into a Link.
        """
        file_url = file_data.get("url")
        if file_url is None:
            return None

        url = _ensure_quoted_url(_absolute_link_url(page_url, file_url))
        pyrequire = file_data.get("requires-python")
        yanked_reason = file_data.get("yanked")
        hashes = file_data.get("hashes", {})

        # PEP 714: Indexes must use the name core-metadata, but
        # clients should support the old name as a fallback for compatibility.
        metadata_info = file_data.get("core-metadata")
        if metadata_info is None:
            metadata_info = file_data.get("dist-info-metadata")

        # The metadata info value may be a boolean, or a dict of hashes.
        if isinstance(metadata_info, dict):
            # The file exists, and hashes have been supplied
            metadata_file_data = MetadataFile(supported_hashes(metadata_info))
        elif metadata_info:
            # The file exists, but there are no hashes
            metadata_file_data = MetadataFile(None)
        else:
            # False or not present: the file does not exist
            metadata_file_data = None

        # The Link.yanked_reason expects an empty string instead of a boolean.
        if yanked_reason and not isinstance(yanked_reason, str):
            yanked_reason = ""
        # The Link.yanked_reason expects None instead of False.
        elif not yanked_reason:
            yanked_reason = None

        return cls(
            url,
            comes_from=page_url,
            requires_python=pyrequire,
            yanked_reason=yanked_reason,
            hashes=hashes,
            metadata_file_data=metadata_file_data,
        )

    @classmethod
    def from_element(
        cls,
        anchor_attribs: dict[str, str | None],
        page_url: str,
        base_url: str,
    ) -> Link | None:
        """
        Convert an anchor element's attributes in a simple repository page to a Link.
        """
        href = anchor_attribs.get("href")
        if not href:
            return None

        url = _ensure_quoted_url(_absolute_link_url(base_url, href))
        pyrequire = anchor_attribs.get("data-requires-python")
        yanked_reason = anchor_attribs.get("data-yanked")

        # PEP 714: Indexes must use the name data-core-metadata, but
        # clients should support the old name as a fallback for compatibility.
        metadata_info = anchor_attribs.get("data-core-metadata")
        if metadata_info is None:
            metadata_info = anchor_attribs.get("data-dist-info-metadata")
        # The metadata info value may be the string "true", or a string of
        # the form "hashname=hashval"
        if metadata_info == "true":
            # The file exists, but there are no hashes
            metadata_file_data = MetadataFile(None)
        elif metadata_info is None:
            # The file does not exist
            metadata_file_data = None
        else:
            # The file exists, and hashes have been supplied
            hashname, sep, hashval = metadata_info.partition("=")
            if sep == "=":
                metadata_file_data = MetadataFile(supported_hashes({hashname: hashval}))
            else:
                # Error - data is wrong. Treat as no hashes supplied.
                logger.debug(
                    "Index returned invalid data-dist-info-metadata value: %s",
                    metadata_info,
                )
                metadata_file_data = MetadataFile(None)

        return cls(
            url,
            comes_from=page_url,
            requires_python=pyrequire,
            yanked_reason=yanked_reason,
            metadata_file_data=metadata_file_data,
        )

    def __str__(self) -> str:
        if self.requires_python:
            rp = f" (requires-python:{self.requires_python})"
        else:
            rp = ""
        if self.comes_from:
            return f"{self.redacted_url} (from {self.comes_from}){rp}"
        else:
            return self.redacted_url

    def __repr__(self) -> str:
        return f"<Link {self}>"

    def __hash__(self) -> int:
        return hash(self.url)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Link):
            return NotImplemented
        return self.url == other.url

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Link):
            return NotImplemented
        return self.url < other.url

    @property
    def url(self) -> str:
        return self._url

    @property
    def redacted_url(self) -> str:
        return redact_auth_from_url(self.url)

    @property
    def filename(self) -> str:
        path = self.path.rstrip("/")
        name = posixpath.basename(path)
        if not name:
            # Make sure we don't leak auth information if the netloc
            # includes a username and password.
            netloc, user_pass = split_auth_from_netloc(self.netloc)
            return netloc

        name = urllib.parse.unquote(name)
        assert name, f"URL {self._url!r} produced no filename"
        return name

    @property
    def file_path(self) -> str:
        return url_to_path(self.url)

    @property
    def scheme(self) -> str:
        return self._parsed_url.scheme

    @property
    def netloc(self) -> str:
        """
        This can contain auth information.
        """
        return self._parsed_url.netloc

    @property
    def path(self) -> str:
        return self._path

    def splitext(self) -> tuple[str, str]:
        return splitext(posixpath.basename(self.path.rstrip("/")))

    @property
    def ext(self) -> str:
        return self.splitext()[1]

    @property
    def url_without_fragment(self) -> str:
        scheme, netloc, path, query, fragment = self._parsed_url
        return urllib.parse.urlunsplit((scheme, netloc, path, query, ""))

    _egg_fragment_re = re.compile(r"[#&]egg=([^&]*)")

    # Per PEP 508.
    _project_name_re = re.compile(
        r"^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", re.IGNORECASE
    )

    def _egg_fragment(self) -> str | None:
        match = self._egg_fragment_re.search(self._url)
        if not match:
            return None

        # An egg fragment looks like a PEP 508 project name, along with
        # an optional extras specifier. Anything else is invalid.
        project_name = match.group(1)
        if not self._project_name_re.match(project_name):
            deprecated(
                reason=f"{self} contains an egg fragment with a non-PEP 508 name.",
                replacement="to use the req @ url syntax, and remove the egg fragment",
                gone_in="25.3",
                issue=13157,
            )

        return project_name

    _subdirectory_fragment_re = re.compile(r"[#&]subdirectory=([^&]*)")

    @property
    def subdirectory_fragment(self) -> str | None:
        match = self._subdirectory_fragment_re.search(self._url)
        if not match:
            return None
        return match.group(1)

    def metadata_link(self) -> Link | None:
        """Return a link to the associated core metadata file (if any)."""
        if self.metadata_file_data is None:
            return None
        metadata_url = f"{self.url_without_fragment}.metadata"
        if self.metadata_file_data.hashes is None:
            return Link(metadata_url)
        return Link(metadata_url, hashes=self.metadata_file_data.hashes)

    def as_hashes(self) -> Hashes:
        return Hashes({k: [v] for k, v in self._hashes.items()})

    @property
    def hash(self) -> str | None:
        return next(iter(self._hashes.values()), None)

    @property
    def hash_name(self) -> str | None:
        return next(iter(self._hashes), None)

    @property
    def show_url(self) -> str:
        return posixpath.basename(self._url.split("#", 1)[0].split("?", 1)[0])

    @property
    def is_file(self) -> bool:
        return self.scheme == "file"

    def is_existing_dir(self) -> bool:
        return self.is_file and os.path.isdir(self.file_path)

    @property
    def is_wheel(self) -> bool:
        return self.ext == WHEEL_EXTENSION

    @property
    def is_vcs(self) -> bool:
        from pip._internal.vcs import vcs

        return self.scheme in vcs.all_schemes

    @property
    def is_yanked(self) -> bool:
        return self.yanked_reason is not None

    @property
    def has_hash(self) -> bool:
        return bool(self._hashes)

    def is_hash_allowed(self, hashes: Hashes | None) -> bool:
        """
        Return True if the link has a hash and it is allowed by `hashes`.
        """
        if hashes is None:
            return False
        return any(hashes.is_hash_allowed(k, v) for k, v in self._hashes.items())


class _CleanResult(NamedTuple):
    """Convert link for equivalency check.

    This is used in the resolver to check whether two URL-specified requirements
    likely point to the same distribution and can be considered equivalent. This
    equivalency logic avoids comparing URLs literally, which can be too strict
    (e.g. "a=1&b=2" vs "b=2&a=1") and produce conflicts unexpecting to users.

    Currently this does three things:

    1. Drop the basic auth part. This is technically wrong since a server can
       serve different content based on auth, but if it does that, it is even
       impossible to guarantee two URLs without auth are equivalent, since
       the user can input different auth information when prompted. So the
       practical solution is to assume the auth doesn't affect the response.
    2. Parse the query to avoid the ordering issue. Note that ordering under the
       same key in the query are NOT cleaned; i.e. "a=1&a=2" and "a=2&a=1" are
       still considered different.
    3. Explicitly drop most of the fragment part, except ``subdirectory=`` and
       hash values, since it should have no impact the downloaded content. Note
       that this drops the "egg=" part historically used to denote the requested
       project (and extras), which is wrong in the strictest sense, but too many
       people are supplying it inconsistently to cause superfluous resolution
       conflicts, so we choose to also ignore them.
    """

    parsed: urllib.parse.SplitResult
    query: dict[str, list[str]]
    subdirectory: str
    hashes: dict[str, str]


def _clean_link(link: Link) -> _CleanResult:
    parsed = link._parsed_url
    netloc = parsed.netloc.rsplit("@", 1)[-1]
    # According to RFC 8089, an empty host in file: means localhost.
    if parsed.scheme == "file" and not netloc:
        netloc = "localhost"
    fragment = urllib.parse.parse_qs(parsed.fragment)
    if "egg" in fragment:
        logger.debug("Ignoring egg= fragment in %s", link)
    try:
        # If there are multiple subdirectory values, use the first one.
        # This matches the behavior of Link.subdirectory_fragment.
        subdirectory = fragment["subdirectory"][0]
    except (IndexError, KeyError):
        subdirectory = ""
    # If there are multiple hash values under the same algorithm, use the
    # first one. This matches the behavior of Link.hash_value.
    hashes = {k: fragment[k][0] for k in _SUPPORTED_HASHES if k in fragment}
    return _CleanResult(
        parsed=parsed._replace(netloc=netloc, query="", fragment=""),
        query=urllib.parse.parse_qs(parsed.query),
        subdirectory=subdirectory,
        hashes=hashes,
    )


@functools.cache
def links_equivalent(link1: Link, link2: Link) -> bool:
    return _clean_link(link1) == _clean_link(link2)

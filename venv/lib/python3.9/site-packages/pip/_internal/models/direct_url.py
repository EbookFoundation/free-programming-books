"""PEP 610"""

from __future__ import annotations

import json
import re
import urllib.parse
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, ClassVar, TypeVar, Union

__all__ = [
    "DirectUrl",
    "DirectUrlValidationError",
    "DirInfo",
    "ArchiveInfo",
    "VcsInfo",
]

T = TypeVar("T")

DIRECT_URL_METADATA_NAME = "direct_url.json"
ENV_VAR_RE = re.compile(r"^\$\{[A-Za-z0-9-_]+\}(:\$\{[A-Za-z0-9-_]+\})?$")


class DirectUrlValidationError(Exception):
    pass


def _get(
    d: dict[str, Any], expected_type: type[T], key: str, default: T | None = None
) -> T | None:
    """Get value from dictionary and verify expected type."""
    if key not in d:
        return default
    value = d[key]
    if not isinstance(value, expected_type):
        raise DirectUrlValidationError(
            f"{value!r} has unexpected type for {key} (expected {expected_type})"
        )
    return value


def _get_required(
    d: dict[str, Any], expected_type: type[T], key: str, default: T | None = None
) -> T:
    value = _get(d, expected_type, key, default)
    if value is None:
        raise DirectUrlValidationError(f"{key} must have a value")
    return value


def _exactly_one_of(infos: Iterable[InfoType | None]) -> InfoType:
    infos = [info for info in infos if info is not None]
    if not infos:
        raise DirectUrlValidationError(
            "missing one of archive_info, dir_info, vcs_info"
        )
    if len(infos) > 1:
        raise DirectUrlValidationError(
            "more than one of archive_info, dir_info, vcs_info"
        )
    assert infos[0] is not None
    return infos[0]


def _filter_none(**kwargs: Any) -> dict[str, Any]:
    """Make dict excluding None values."""
    return {k: v for k, v in kwargs.items() if v is not None}


@dataclass
class VcsInfo:
    name: ClassVar = "vcs_info"

    vcs: str
    commit_id: str
    requested_revision: str | None = None

    @classmethod
    def _from_dict(cls, d: dict[str, Any] | None) -> VcsInfo | None:
        if d is None:
            return None
        return cls(
            vcs=_get_required(d, str, "vcs"),
            commit_id=_get_required(d, str, "commit_id"),
            requested_revision=_get(d, str, "requested_revision"),
        )

    def _to_dict(self) -> dict[str, Any]:
        return _filter_none(
            vcs=self.vcs,
            requested_revision=self.requested_revision,
            commit_id=self.commit_id,
        )


class ArchiveInfo:
    name = "archive_info"

    def __init__(
        self,
        hash: str | None = None,
        hashes: dict[str, str] | None = None,
    ) -> None:
        # set hashes before hash, since the hash setter will further populate hashes
        self.hashes = hashes
        self.hash = hash

    @property
    def hash(self) -> str | None:
        return self._hash

    @hash.setter
    def hash(self, value: str | None) -> None:
        if value is not None:
            # Auto-populate the hashes key to upgrade to the new format automatically.
            # We don't back-populate the legacy hash key from hashes.
            try:
                hash_name, hash_value = value.split("=", 1)
            except ValueError:
                raise DirectUrlValidationError(
                    f"invalid archive_info.hash format: {value!r}"
                )
            if self.hashes is None:
                self.hashes = {hash_name: hash_value}
            elif hash_name not in self.hashes:
                self.hashes = self.hashes.copy()
                self.hashes[hash_name] = hash_value
        self._hash = value

    @classmethod
    def _from_dict(cls, d: dict[str, Any] | None) -> ArchiveInfo | None:
        if d is None:
            return None
        return cls(hash=_get(d, str, "hash"), hashes=_get(d, dict, "hashes"))

    def _to_dict(self) -> dict[str, Any]:
        return _filter_none(hash=self.hash, hashes=self.hashes)


@dataclass
class DirInfo:
    name: ClassVar = "dir_info"

    editable: bool = False

    @classmethod
    def _from_dict(cls, d: dict[str, Any] | None) -> DirInfo | None:
        if d is None:
            return None
        return cls(editable=_get_required(d, bool, "editable", default=False))

    def _to_dict(self) -> dict[str, Any]:
        return _filter_none(editable=self.editable or None)


InfoType = Union[ArchiveInfo, DirInfo, VcsInfo]


@dataclass
class DirectUrl:
    url: str
    info: InfoType
    subdirectory: str | None = None

    def _remove_auth_from_netloc(self, netloc: str) -> str:
        if "@" not in netloc:
            return netloc
        user_pass, netloc_no_user_pass = netloc.split("@", 1)
        if (
            isinstance(self.info, VcsInfo)
            and self.info.vcs == "git"
            and user_pass == "git"
        ):
            return netloc
        if ENV_VAR_RE.match(user_pass):
            return netloc
        return netloc_no_user_pass

    @property
    def redacted_url(self) -> str:
        """url with user:password part removed unless it is formed with
        environment variables as specified in PEP 610, or it is ``git``
        in the case of a git URL.
        """
        purl = urllib.parse.urlsplit(self.url)
        netloc = self._remove_auth_from_netloc(purl.netloc)
        surl = urllib.parse.urlunsplit(
            (purl.scheme, netloc, purl.path, purl.query, purl.fragment)
        )
        return surl

    def validate(self) -> None:
        self.from_dict(self.to_dict())

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DirectUrl:
        return DirectUrl(
            url=_get_required(d, str, "url"),
            subdirectory=_get(d, str, "subdirectory"),
            info=_exactly_one_of(
                [
                    ArchiveInfo._from_dict(_get(d, dict, "archive_info")),
                    DirInfo._from_dict(_get(d, dict, "dir_info")),
                    VcsInfo._from_dict(_get(d, dict, "vcs_info")),
                ]
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        res = _filter_none(
            url=self.redacted_url,
            subdirectory=self.subdirectory,
        )
        res[self.info.name] = self.info._to_dict()
        return res

    @classmethod
    def from_json(cls, s: str) -> DirectUrl:
        return cls.from_dict(json.loads(s))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    def is_local_editable(self) -> bool:
        return isinstance(self.info, DirInfo) and self.info.editable

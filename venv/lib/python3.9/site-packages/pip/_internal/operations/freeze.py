from __future__ import annotations

import collections
import logging
import os
from collections.abc import Container, Generator, Iterable
from dataclasses import dataclass, field
from typing import NamedTuple

from pip._vendor.packaging.utils import NormalizedName, canonicalize_name
from pip._vendor.packaging.version import InvalidVersion

from pip._internal.exceptions import BadCommand, InstallationError
from pip._internal.metadata import BaseDistribution, get_environment
from pip._internal.req.constructors import (
    install_req_from_editable,
    install_req_from_line,
)
from pip._internal.req.req_file import COMMENT_RE
from pip._internal.utils.direct_url_helpers import direct_url_as_pep440_direct_reference

logger = logging.getLogger(__name__)


class _EditableInfo(NamedTuple):
    requirement: str
    comments: list[str]


def freeze(
    requirement: list[str] | None = None,
    local_only: bool = False,
    user_only: bool = False,
    paths: list[str] | None = None,
    isolated: bool = False,
    exclude_editable: bool = False,
    skip: Container[str] = (),
) -> Generator[str, None, None]:
    installations: dict[str, FrozenRequirement] = {}

    dists = get_environment(paths).iter_installed_distributions(
        local_only=local_only,
        skip=(),
        user_only=user_only,
    )
    for dist in dists:
        req = FrozenRequirement.from_dist(dist)
        if exclude_editable and req.editable:
            continue
        installations[req.canonical_name] = req

    if requirement:
        # the options that don't get turned into an InstallRequirement
        # should only be emitted once, even if the same option is in multiple
        # requirements files, so we need to keep track of what has been emitted
        # so that we don't emit it again if it's seen again
        emitted_options: set[str] = set()
        # keep track of which files a requirement is in so that we can
        # give an accurate warning if a requirement appears multiple times.
        req_files: dict[str, list[str]] = collections.defaultdict(list)
        for req_file_path in requirement:
            with open(req_file_path) as req_file:
                for line in req_file:
                    if (
                        not line.strip()
                        or line.strip().startswith("#")
                        or line.startswith(
                            (
                                "-r",
                                "--requirement",
                                "-f",
                                "--find-links",
                                "-i",
                                "--index-url",
                                "--pre",
                                "--trusted-host",
                                "--process-dependency-links",
                                "--extra-index-url",
                                "--use-feature",
                            )
                        )
                    ):
                        line = line.rstrip()
                        if line not in emitted_options:
                            emitted_options.add(line)
                            yield line
                        continue

                    if line.startswith(("-e", "--editable")):
                        if line.startswith("-e"):
                            line = line[2:].strip()
                        else:
                            line = line[len("--editable") :].strip().lstrip("=")
                        line_req = install_req_from_editable(
                            line,
                            isolated=isolated,
                        )
                    else:
                        line_req = install_req_from_line(
                            COMMENT_RE.sub("", line).strip(),
                            isolated=isolated,
                        )

                    if not line_req.name:
                        logger.info(
                            "Skipping line in requirement file [%s] because "
                            "it's not clear what it would install: %s",
                            req_file_path,
                            line.strip(),
                        )
                        logger.info(
                            "  (add #egg=PackageName to the URL to avoid"
                            " this warning)"
                        )
                    else:
                        line_req_canonical_name = canonicalize_name(line_req.name)
                        if line_req_canonical_name not in installations:
                            # either it's not installed, or it is installed
                            # but has been processed already
                            if not req_files[line_req.name]:
                                logger.warning(
                                    "Requirement file [%s] contains %s, but "
                                    "package %r is not installed",
                                    req_file_path,
                                    COMMENT_RE.sub("", line).strip(),
                                    line_req.name,
                                )
                            else:
                                req_files[line_req.name].append(req_file_path)
                        else:
                            yield str(installations[line_req_canonical_name]).rstrip()
                            del installations[line_req_canonical_name]
                            req_files[line_req.name].append(req_file_path)

        # Warn about requirements that were included multiple times (in a
        # single requirements file or in different requirements files).
        for name, files in req_files.items():
            if len(files) > 1:
                logger.warning(
                    "Requirement %s included multiple times [%s]",
                    name,
                    ", ".join(sorted(set(files))),
                )

        yield ("## The following requirements were added by pip freeze:")
    for installation in sorted(installations.values(), key=lambda x: x.name.lower()):
        if installation.canonical_name not in skip:
            yield str(installation).rstrip()


def _format_as_name_version(dist: BaseDistribution) -> str:
    try:
        dist_version = dist.version
    except InvalidVersion:
        # legacy version
        return f"{dist.raw_name}==={dist.raw_version}"
    else:
        return f"{dist.raw_name}=={dist_version}"


def _get_editable_info(dist: BaseDistribution) -> _EditableInfo:
    """
    Compute and return values (req, comments) for use in
    FrozenRequirement.from_dist().
    """
    editable_project_location = dist.editable_project_location
    assert editable_project_location
    location = os.path.normcase(os.path.abspath(editable_project_location))

    from pip._internal.vcs import RemoteNotFoundError, RemoteNotValidError, vcs

    vcs_backend = vcs.get_backend_for_dir(location)

    if vcs_backend is None:
        display = _format_as_name_version(dist)
        logger.debug(
            'No VCS found for editable requirement "%s" in: %r',
            display,
            location,
        )
        return _EditableInfo(
            requirement=location,
            comments=[f"# Editable install with no version control ({display})"],
        )

    vcs_name = type(vcs_backend).__name__

    try:
        req = vcs_backend.get_src_requirement(location, dist.raw_name)
    except RemoteNotFoundError:
        display = _format_as_name_version(dist)
        return _EditableInfo(
            requirement=location,
            comments=[f"# Editable {vcs_name} install with no remote ({display})"],
        )
    except RemoteNotValidError as ex:
        display = _format_as_name_version(dist)
        return _EditableInfo(
            requirement=location,
            comments=[
                f"# Editable {vcs_name} install ({display}) with either a deleted "
                f"local remote or invalid URI:",
                f"# '{ex.url}'",
            ],
        )
    except BadCommand:
        logger.warning(
            "cannot determine version of editable source in %s "
            "(%s command not found in path)",
            location,
            vcs_backend.name,
        )
        return _EditableInfo(requirement=location, comments=[])
    except InstallationError as exc:
        logger.warning("Error when trying to get requirement for VCS system %s", exc)
    else:
        return _EditableInfo(requirement=req, comments=[])

    logger.warning("Could not determine repository location of %s", location)

    return _EditableInfo(
        requirement=location,
        comments=["## !! Could not determine repository location"],
    )


@dataclass(frozen=True)
class FrozenRequirement:
    name: str
    req: str
    editable: bool
    comments: Iterable[str] = field(default_factory=tuple)

    @property
    def canonical_name(self) -> NormalizedName:
        return canonicalize_name(self.name)

    @classmethod
    def from_dist(cls, dist: BaseDistribution) -> FrozenRequirement:
        editable = dist.editable
        if editable:
            req, comments = _get_editable_info(dist)
        else:
            comments = []
            direct_url = dist.direct_url
            if direct_url:
                # if PEP 610 metadata is present, use it
                req = direct_url_as_pep440_direct_reference(direct_url, dist.raw_name)
            else:
                # name==version requirement
                req = _format_as_name_version(dist)

        return cls(dist.raw_name, req, editable, comments=comments)

    def __str__(self) -> str:
        req = self.req
        if self.editable:
            req = f"-e {req}"
        return "\n".join(list(self.comments) + [str(req)]) + "\n"

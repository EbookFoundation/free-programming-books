from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Optional

from pip._vendor.packaging.specifiers import SpecifierSet
from pip._vendor.packaging.utils import NormalizedName
from pip._vendor.packaging.version import Version

from pip._internal.models.link import Link, links_equivalent
from pip._internal.req.req_install import InstallRequirement
from pip._internal.utils.hashes import Hashes

CandidateLookup = tuple[Optional["Candidate"], Optional[InstallRequirement]]


def format_name(project: NormalizedName, extras: frozenset[NormalizedName]) -> str:
    if not extras:
        return project
    extras_expr = ",".join(sorted(extras))
    return f"{project}[{extras_expr}]"


@dataclass(frozen=True)
class Constraint:
    specifier: SpecifierSet
    hashes: Hashes
    links: frozenset[Link]

    @classmethod
    def empty(cls) -> Constraint:
        return Constraint(SpecifierSet(), Hashes(), frozenset())

    @classmethod
    def from_ireq(cls, ireq: InstallRequirement) -> Constraint:
        links = frozenset([ireq.link]) if ireq.link else frozenset()
        return Constraint(ireq.specifier, ireq.hashes(trust_internet=False), links)

    def __bool__(self) -> bool:
        return bool(self.specifier) or bool(self.hashes) or bool(self.links)

    def __and__(self, other: InstallRequirement) -> Constraint:
        if not isinstance(other, InstallRequirement):
            return NotImplemented
        specifier = self.specifier & other.specifier
        hashes = self.hashes & other.hashes(trust_internet=False)
        links = self.links
        if other.link:
            links = links.union([other.link])
        return Constraint(specifier, hashes, links)

    def is_satisfied_by(self, candidate: Candidate) -> bool:
        # Reject if there are any mismatched URL constraints on this package.
        if self.links and not all(_match_link(link, candidate) for link in self.links):
            return False
        # We can safely always allow prereleases here since PackageFinder
        # already implements the prerelease logic, and would have filtered out
        # prerelease candidates if the user does not expect them.
        return self.specifier.contains(candidate.version, prereleases=True)


class Requirement:
    @property
    def project_name(self) -> NormalizedName:
        """The "project name" of a requirement.

        This is different from ``name`` if this requirement contains extras,
        in which case ``name`` would contain the ``[...]`` part, while this
        refers to the name of the project.
        """
        raise NotImplementedError("Subclass should override")

    @property
    def name(self) -> str:
        """The name identifying this requirement in the resolver.

        This is different from ``project_name`` if this requirement contains
        extras, where ``project_name`` would not contain the ``[...]`` part.
        """
        raise NotImplementedError("Subclass should override")

    def is_satisfied_by(self, candidate: Candidate) -> bool:
        return False

    def get_candidate_lookup(self) -> CandidateLookup:
        raise NotImplementedError("Subclass should override")

    def format_for_error(self) -> str:
        raise NotImplementedError("Subclass should override")


def _match_link(link: Link, candidate: Candidate) -> bool:
    if candidate.source_link:
        return links_equivalent(link, candidate.source_link)
    return False


class Candidate:
    @property
    def project_name(self) -> NormalizedName:
        """The "project name" of the candidate.

        This is different from ``name`` if this candidate contains extras,
        in which case ``name`` would contain the ``[...]`` part, while this
        refers to the name of the project.
        """
        raise NotImplementedError("Override in subclass")

    @property
    def name(self) -> str:
        """The name identifying this candidate in the resolver.

        This is different from ``project_name`` if this candidate contains
        extras, where ``project_name`` would not contain the ``[...]`` part.
        """
        raise NotImplementedError("Override in subclass")

    @property
    def version(self) -> Version:
        raise NotImplementedError("Override in subclass")

    @property
    def is_installed(self) -> bool:
        raise NotImplementedError("Override in subclass")

    @property
    def is_editable(self) -> bool:
        raise NotImplementedError("Override in subclass")

    @property
    def source_link(self) -> Link | None:
        raise NotImplementedError("Override in subclass")

    def iter_dependencies(self, with_requires: bool) -> Iterable[Requirement | None]:
        raise NotImplementedError("Override in subclass")

    def get_install_requirement(self) -> InstallRequirement | None:
        raise NotImplementedError("Override in subclass")

    def format_for_error(self) -> str:
        raise NotImplementedError("Subclass should override")

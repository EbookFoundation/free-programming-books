from __future__ import annotations

from typing import Any

from pip._vendor.packaging.specifiers import SpecifierSet
from pip._vendor.packaging.utils import NormalizedName, canonicalize_name

from pip._internal.req.constructors import install_req_drop_extras
from pip._internal.req.req_install import InstallRequirement

from .base import Candidate, CandidateLookup, Requirement, format_name


class ExplicitRequirement(Requirement):
    def __init__(self, candidate: Candidate) -> None:
        self.candidate = candidate

    def __str__(self) -> str:
        return str(self.candidate)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.candidate!r})"

    def __hash__(self) -> int:
        return hash(self.candidate)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ExplicitRequirement):
            return False
        return self.candidate == other.candidate

    @property
    def project_name(self) -> NormalizedName:
        # No need to canonicalize - the candidate did this
        return self.candidate.project_name

    @property
    def name(self) -> str:
        # No need to canonicalize - the candidate did this
        return self.candidate.name

    def format_for_error(self) -> str:
        return self.candidate.format_for_error()

    def get_candidate_lookup(self) -> CandidateLookup:
        return self.candidate, None

    def is_satisfied_by(self, candidate: Candidate) -> bool:
        return candidate == self.candidate


class SpecifierRequirement(Requirement):
    def __init__(self, ireq: InstallRequirement) -> None:
        assert ireq.link is None, "This is a link, not a specifier"
        self._ireq = ireq
        self._equal_cache: str | None = None
        self._hash: int | None = None
        self._extras = frozenset(canonicalize_name(e) for e in self._ireq.extras)

    @property
    def _equal(self) -> str:
        if self._equal_cache is not None:
            return self._equal_cache

        self._equal_cache = str(self._ireq)
        return self._equal_cache

    def __str__(self) -> str:
        return str(self._ireq.req)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self._ireq.req)!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SpecifierRequirement):
            return NotImplemented
        return self._equal == other._equal

    def __hash__(self) -> int:
        if self._hash is not None:
            return self._hash

        self._hash = hash(self._equal)
        return self._hash

    @property
    def project_name(self) -> NormalizedName:
        assert self._ireq.req, "Specifier-backed ireq is always PEP 508"
        return canonicalize_name(self._ireq.req.name)

    @property
    def name(self) -> str:
        return format_name(self.project_name, self._extras)

    def format_for_error(self) -> str:
        # Convert comma-separated specifiers into "A, B, ..., F and G"
        # This makes the specifier a bit more "human readable", without
        # risking a change in meaning. (Hopefully! Not all edge cases have
        # been checked)
        parts = [s.strip() for s in str(self).split(",")]
        if len(parts) == 0:
            return ""
        elif len(parts) == 1:
            return parts[0]

        return ", ".join(parts[:-1]) + " and " + parts[-1]

    def get_candidate_lookup(self) -> CandidateLookup:
        return None, self._ireq

    def is_satisfied_by(self, candidate: Candidate) -> bool:
        assert candidate.name == self.name, (
            f"Internal issue: Candidate is not for this requirement "
            f"{candidate.name} vs {self.name}"
        )
        # We can safely always allow prereleases here since PackageFinder
        # already implements the prerelease logic, and would have filtered out
        # prerelease candidates if the user does not expect them.
        assert self._ireq.req, "Specifier-backed ireq is always PEP 508"
        spec = self._ireq.req.specifier
        return spec.contains(candidate.version, prereleases=True)


class SpecifierWithoutExtrasRequirement(SpecifierRequirement):
    """
    Requirement backed by an install requirement on a base package.
    Trims extras from its install requirement if there are any.
    """

    def __init__(self, ireq: InstallRequirement) -> None:
        assert ireq.link is None, "This is a link, not a specifier"
        self._ireq = install_req_drop_extras(ireq)
        self._equal_cache: str | None = None
        self._hash: int | None = None
        self._extras = frozenset(canonicalize_name(e) for e in self._ireq.extras)

    @property
    def _equal(self) -> str:
        if self._equal_cache is not None:
            return self._equal_cache

        self._equal_cache = str(self._ireq)
        return self._equal_cache

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SpecifierWithoutExtrasRequirement):
            return NotImplemented
        return self._equal == other._equal

    def __hash__(self) -> int:
        if self._hash is not None:
            return self._hash

        self._hash = hash(self._equal)
        return self._hash


class RequiresPythonRequirement(Requirement):
    """A requirement representing Requires-Python metadata."""

    def __init__(self, specifier: SpecifierSet, match: Candidate) -> None:
        self.specifier = specifier
        self._specifier_string = str(specifier)  # for faster __eq__
        self._hash: int | None = None
        self._candidate = match

    def __str__(self) -> str:
        return f"Python {self.specifier}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self.specifier)!r})"

    def __hash__(self) -> int:
        if self._hash is not None:
            return self._hash

        self._hash = hash((self._specifier_string, self._candidate))
        return self._hash

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RequiresPythonRequirement):
            return False
        return (
            self._specifier_string == other._specifier_string
            and self._candidate == other._candidate
        )

    @property
    def project_name(self) -> NormalizedName:
        return self._candidate.project_name

    @property
    def name(self) -> str:
        return self._candidate.name

    def format_for_error(self) -> str:
        return str(self)

    def get_candidate_lookup(self) -> CandidateLookup:
        if self.specifier.contains(self._candidate.version, prereleases=True):
            return self._candidate, None
        return None, None

    def is_satisfied_by(self, candidate: Candidate) -> bool:
        assert candidate.name == self._candidate.name, "Not Python candidate"
        # We can safely always allow prereleases here since PackageFinder
        # already implements the prerelease logic, and would have filtered out
        # prerelease candidates if the user does not expect them.
        return self.specifier.contains(candidate.version, prereleases=True)


class UnsatisfiableRequirement(Requirement):
    """A requirement that cannot be satisfied."""

    def __init__(self, name: NormalizedName) -> None:
        self._name = name

    def __str__(self) -> str:
        return f"{self._name} (unavailable)"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self._name)!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UnsatisfiableRequirement):
            return NotImplemented
        return self._name == other._name

    def __hash__(self) -> int:
        return hash(self._name)

    @property
    def project_name(self) -> NormalizedName:
        return self._name

    @property
    def name(self) -> str:
        return self._name

    def format_for_error(self) -> str:
        return str(self)

    def get_candidate_lookup(self) -> CandidateLookup:
        return None, None

    def is_satisfied_by(self, candidate: Candidate) -> bool:
        return False

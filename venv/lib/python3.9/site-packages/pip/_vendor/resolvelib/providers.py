from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Sequence,
)

from .structs import CT, KT, RT, Matches, RequirementInformation

if TYPE_CHECKING:
    from typing import Any, Protocol

    class Preference(Protocol):
        def __lt__(self, __other: Any) -> bool: ...


class AbstractProvider(Generic[RT, CT, KT]):
    """Delegate class to provide the required interface for the resolver."""

    def identify(self, requirement_or_candidate: RT | CT) -> KT:
        """Given a requirement or candidate, return an identifier for it.

        This is used to identify, e.g. whether two requirements
        should have their specifier parts merged or a candidate matches a
        requirement via ``find_matches()``.
        """
        raise NotImplementedError

    def get_preference(
        self,
        identifier: KT,
        resolutions: Mapping[KT, CT],
        candidates: Mapping[KT, Iterator[CT]],
        information: Mapping[KT, Iterator[RequirementInformation[RT, CT]]],
        backtrack_causes: Sequence[RequirementInformation[RT, CT]],
    ) -> Preference:
        """Produce a sort key for given requirement based on preference.

        As this is a sort key it will be called O(n) times per backtrack
        step, where n is the number of `identifier`s, if you have a check
        which is expensive in some sense. E.g. It needs to make O(n) checks
        per call or takes significant wall clock time, consider using
        `narrow_requirement_selection` to filter the `identifier`s, which
        is applied before this sort key is called.

        The preference is defined as "I think this requirement should be
        resolved first". The lower the return value is, the more preferred
        this group of arguments is.

        :param identifier: An identifier as returned by ``identify()``. This
            identifies the requirement being considered.
        :param resolutions: Mapping of candidates currently pinned by the
            resolver. Each key is an identifier, and the value is a candidate.
            The candidate may conflict with requirements from ``information``.
        :param candidates: Mapping of each dependency's possible candidates.
            Each value is an iterator of candidates.
        :param information: Mapping of requirement information of each package.
            Each value is an iterator of *requirement information*.
        :param backtrack_causes: Sequence of *requirement information* that are
            the requirements that caused the resolver to most recently
            backtrack.

        A *requirement information* instance is a named tuple with two members:

        * ``requirement`` specifies a requirement contributing to the current
          list of candidates.
        * ``parent`` specifies the candidate that provides (depended on) the
          requirement, or ``None`` to indicate a root requirement.

        The preference could depend on various issues, including (not
        necessarily in this order):

        * Is this package pinned in the current resolution result?
        * How relaxed is the requirement? Stricter ones should probably be
          worked on first? (I don't know, actually.)
        * How many possibilities are there to satisfy this requirement? Those
          with few left should likely be worked on first, I guess?
        * Are there any known conflicts for this requirement? We should
          probably work on those with the most known conflicts.

        A sortable value should be returned (this will be used as the ``key``
        parameter of the built-in sorting function). The smaller the value is,
        the more preferred this requirement is (i.e. the sorting function
        is called with ``reverse=False``).
        """
        raise NotImplementedError

    def find_matches(
        self,
        identifier: KT,
        requirements: Mapping[KT, Iterator[RT]],
        incompatibilities: Mapping[KT, Iterator[CT]],
    ) -> Matches[CT]:
        """Find all possible candidates that satisfy the given constraints.

        :param identifier: An identifier as returned by ``identify()``. All
            candidates returned by this method should produce the same
            identifier.
        :param requirements: A mapping of requirements that all returned
            candidates must satisfy. Each key is an identifier, and the value
            an iterator of requirements for that dependency.
        :param incompatibilities: A mapping of known incompatibile candidates of
            each dependency. Each key is an identifier, and the value an
            iterator of incompatibilities known to the resolver. All
            incompatibilities *must* be excluded from the return value.

        This should try to get candidates based on the requirements' types.
        For VCS, local, and archive requirements, the one-and-only match is
        returned, and for a "named" requirement, the index(es) should be
        consulted to find concrete candidates for this requirement.

        The return value should produce candidates ordered by preference; the
        most preferred candidate should come first. The return type may be one
        of the following:

        * A callable that returns an iterator that yields candidates.
        * An collection of candidates.
        * An iterable of candidates. This will be consumed immediately into a
          list of candidates.
        """
        raise NotImplementedError

    def is_satisfied_by(self, requirement: RT, candidate: CT) -> bool:
        """Whether the given requirement can be satisfied by a candidate.

        The candidate is guaranteed to have been generated from the
        requirement.

        A boolean should be returned to indicate whether ``candidate`` is a
        viable solution to the requirement.
        """
        raise NotImplementedError

    def get_dependencies(self, candidate: CT) -> Iterable[RT]:
        """Get dependencies of a candidate.

        This should return a collection of requirements that `candidate`
        specifies as its dependencies.
        """
        raise NotImplementedError

    def narrow_requirement_selection(
        self,
        identifiers: Iterable[KT],
        resolutions: Mapping[KT, CT],
        candidates: Mapping[KT, Iterator[CT]],
        information: Mapping[KT, Iterator[RequirementInformation[RT, CT]]],
        backtrack_causes: Sequence[RequirementInformation[RT, CT]],
    ) -> Iterable[KT]:
        """
        An optional method to narrow the selection of requirements being
        considered during resolution. This method is called O(1) time per
        backtrack step.

        :param identifiers: An iterable of `identifiers` as returned by
            ``identify()``. These identify all requirements currently being
            considered.
        :param resolutions: A mapping of candidates currently pinned by the
            resolver. Each key is an identifier, and the value is a candidate
            that may conflict with requirements from ``information``.
        :param candidates: A mapping of each dependency's possible candidates.
            Each value is an iterator of candidates.
        :param information: A mapping of requirement information for each package.
            Each value is an iterator of *requirement information*.
        :param backtrack_causes: A sequence of *requirement information* that are
            the requirements causing the resolver to most recently
            backtrack.

        A *requirement information* instance is a named tuple with two members:

        * ``requirement`` specifies a requirement contributing to the current
          list of candidates.
        * ``parent`` specifies the candidate that provides (is depended on for)
          the requirement, or ``None`` to indicate a root requirement.

        Must return a non-empty subset of `identifiers`, with the default
        implementation being to return `identifiers` unchanged. Those `identifiers`
        will then be passed to the sort key `get_preference` to pick the most
        prefered requirement to attempt to pin, unless `narrow_requirement_selection`
        returns only 1 requirement, in which case that will be used without
        calling the sort key `get_preference`.

        This method is designed to be used by the provider to optimize the
        dependency resolution, e.g. if a check cost is O(m) and it can be done
        against all identifiers at once then filtering the requirement selection
        here will cost O(m) but making it part of the sort key in `get_preference`
        will cost O(m*n), where n is the number of `identifiers`.

        Returns:
            Iterable[KT]: A non-empty subset of `identifiers`.
        """
        return identifiers

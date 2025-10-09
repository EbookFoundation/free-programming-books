from __future__ import annotations

from typing import TYPE_CHECKING, Collection, Generic

from ..structs import CT, RT, RequirementInformation

if TYPE_CHECKING:
    from .criterion import Criterion


class ResolverException(Exception):
    """A base class for all exceptions raised by this module.

    Exceptions derived by this class should all be handled in this module. Any
    bubbling pass the resolver should be treated as a bug.
    """


class RequirementsConflicted(ResolverException, Generic[RT, CT]):
    def __init__(self, criterion: Criterion[RT, CT]) -> None:
        super().__init__(criterion)
        self.criterion = criterion

    def __str__(self) -> str:
        return "Requirements conflict: {}".format(
            ", ".join(repr(r) for r in self.criterion.iter_requirement()),
        )


class InconsistentCandidate(ResolverException, Generic[RT, CT]):
    def __init__(self, candidate: CT, criterion: Criterion[RT, CT]):
        super().__init__(candidate, criterion)
        self.candidate = candidate
        self.criterion = criterion

    def __str__(self) -> str:
        return "Provided candidate {!r} does not satisfy {}".format(
            self.candidate,
            ", ".join(repr(r) for r in self.criterion.iter_requirement()),
        )


class ResolutionError(ResolverException):
    pass


class ResolutionImpossible(ResolutionError, Generic[RT, CT]):
    def __init__(self, causes: Collection[RequirementInformation[RT, CT]]):
        super().__init__(causes)
        # causes is a list of RequirementInformation objects
        self.causes = causes


class ResolutionTooDeep(ResolutionError):
    def __init__(self, round_count: int) -> None:
        super().__init__(round_count)
        self.round_count = round_count

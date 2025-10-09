from __future__ import annotations

from typing import Collection, Generic, Iterable, Iterator

from ..structs import CT, RT, RequirementInformation


class Criterion(Generic[RT, CT]):
    """Representation of possible resolution results of a package.

    This holds three attributes:

    * `information` is a collection of `RequirementInformation` pairs.
      Each pair is a requirement contributing to this criterion, and the
      candidate that provides the requirement.
    * `incompatibilities` is a collection of all known not-to-work candidates
      to exclude from consideration.
    * `candidates` is a collection containing all possible candidates deducted
      from the union of contributing requirements and known incompatibilities.
      It should never be empty, except when the criterion is an attribute of a
      raised `RequirementsConflicted` (in which case it is always empty).

    .. note::
        This class is intended to be externally immutable. **Do not** mutate
        any of its attribute containers.
    """

    def __init__(
        self,
        candidates: Iterable[CT],
        information: Collection[RequirementInformation[RT, CT]],
        incompatibilities: Collection[CT],
    ) -> None:
        self.candidates = candidates
        self.information = information
        self.incompatibilities = incompatibilities

    def __repr__(self) -> str:
        requirements = ", ".join(
            f"({req!r}, via={parent!r})" for req, parent in self.information
        )
        return f"Criterion({requirements})"

    def iter_requirement(self) -> Iterator[RT]:
        return (i.requirement for i in self.information)

    def iter_parent(self) -> Iterator[CT | None]:
        return (i.parent for i in self.information)

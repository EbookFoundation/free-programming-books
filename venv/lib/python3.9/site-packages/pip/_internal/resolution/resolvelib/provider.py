from __future__ import annotations

import math
from collections.abc import Iterable, Iterator, Mapping, Sequence
from functools import cache
from typing import (
    TYPE_CHECKING,
    TypeVar,
)

from pip._vendor.resolvelib.providers import AbstractProvider

from pip._internal.req.req_install import InstallRequirement

from .base import Candidate, Constraint, Requirement
from .candidates import REQUIRES_PYTHON_IDENTIFIER
from .factory import Factory
from .requirements import ExplicitRequirement

if TYPE_CHECKING:
    from pip._vendor.resolvelib.providers import Preference
    from pip._vendor.resolvelib.resolvers import RequirementInformation

    PreferenceInformation = RequirementInformation[Requirement, Candidate]

    _ProviderBase = AbstractProvider[Requirement, Candidate, str]
else:
    _ProviderBase = AbstractProvider

# Notes on the relationship between the provider, the factory, and the
# candidate and requirement classes.
#
# The provider is a direct implementation of the resolvelib class. Its role
# is to deliver the API that resolvelib expects.
#
# Rather than work with completely abstract "requirement" and "candidate"
# concepts as resolvelib does, pip has concrete classes implementing these two
# ideas. The API of Requirement and Candidate objects are defined in the base
# classes, but essentially map fairly directly to the equivalent provider
# methods. In particular, `find_matches` and `is_satisfied_by` are
# requirement methods, and `get_dependencies` is a candidate method.
#
# The factory is the interface to pip's internal mechanisms. It is stateless,
# and is created by the resolver and held as a property of the provider. It is
# responsible for creating Requirement and Candidate objects, and provides
# services to those objects (access to pip's finder and preparer).


D = TypeVar("D")
V = TypeVar("V")


def _get_with_identifier(
    mapping: Mapping[str, V],
    identifier: str,
    default: D,
) -> D | V:
    """Get item from a package name lookup mapping with a resolver identifier.

    This extra logic is needed when the target mapping is keyed by package
    name, which cannot be directly looked up with an identifier (which may
    contain requested extras). Additional logic is added to also look up a value
    by "cleaning up" the extras from the identifier.
    """
    if identifier in mapping:
        return mapping[identifier]
    # HACK: Theoretically we should check whether this identifier is a valid
    # "NAME[EXTRAS]" format, and parse out the name part with packaging or
    # some regular expression. But since pip's resolver only spits out three
    # kinds of identifiers: normalized PEP 503 names, normalized names plus
    # extras, and Requires-Python, we can cheat a bit here.
    name, open_bracket, _ = identifier.partition("[")
    if open_bracket and name in mapping:
        return mapping[name]
    return default


class PipProvider(_ProviderBase):
    """Pip's provider implementation for resolvelib.

    :params constraints: A mapping of constraints specified by the user. Keys
        are canonicalized project names.
    :params ignore_dependencies: Whether the user specified ``--no-deps``.
    :params upgrade_strategy: The user-specified upgrade strategy.
    :params user_requested: A set of canonicalized package names that the user
        supplied for pip to install/upgrade.
    """

    def __init__(
        self,
        factory: Factory,
        constraints: dict[str, Constraint],
        ignore_dependencies: bool,
        upgrade_strategy: str,
        user_requested: dict[str, int],
    ) -> None:
        self._factory = factory
        self._constraints = constraints
        self._ignore_dependencies = ignore_dependencies
        self._upgrade_strategy = upgrade_strategy
        self._user_requested = user_requested

    def identify(self, requirement_or_candidate: Requirement | Candidate) -> str:
        return requirement_or_candidate.name

    def narrow_requirement_selection(
        self,
        identifiers: Iterable[str],
        resolutions: Mapping[str, Candidate],
        candidates: Mapping[str, Iterator[Candidate]],
        information: Mapping[str, Iterator[PreferenceInformation]],
        backtrack_causes: Sequence[PreferenceInformation],
    ) -> Iterable[str]:
        """Produce a subset of identifiers that should be considered before others.

        Currently pip narrows the following selection:
            * Requires-Python, if present is always returned by itself
            * Backtrack causes are considered next because they can be identified
              in linear time here, whereas because get_preference() is called
              for each identifier, it would be quadratic to check for them there.
              Further, the current backtrack causes likely need to be resolved
              before other requirements as a resolution can't be found while
              there is a conflict.
        """
        backtrack_identifiers = set()
        for info in backtrack_causes:
            backtrack_identifiers.add(info.requirement.name)
            if info.parent is not None:
                backtrack_identifiers.add(info.parent.name)

        current_backtrack_causes = []
        for identifier in identifiers:
            # Requires-Python has only one candidate and the check is basically
            # free, so we always do it first to avoid needless work if it fails.
            # This skips calling get_preference() for all other identifiers.
            if identifier == REQUIRES_PYTHON_IDENTIFIER:
                return [identifier]

            # Check if this identifier is a backtrack cause
            if identifier in backtrack_identifiers:
                current_backtrack_causes.append(identifier)
                continue

        if current_backtrack_causes:
            return current_backtrack_causes

        return identifiers

    def get_preference(
        self,
        identifier: str,
        resolutions: Mapping[str, Candidate],
        candidates: Mapping[str, Iterator[Candidate]],
        information: Mapping[str, Iterable[PreferenceInformation]],
        backtrack_causes: Sequence[PreferenceInformation],
    ) -> Preference:
        """Produce a sort key for given requirement based on preference.

        The lower the return value is, the more preferred this group of
        arguments is.

        Currently pip considers the following in order:

        * Any requirement that is "direct", e.g., points to an explicit URL.
        * Any requirement that is "pinned", i.e., contains the operator ``===``
          or ``==`` without a wildcard.
        * Any requirement that imposes an upper version limit, i.e., contains the
          operator ``<``, ``<=``, ``~=``, or ``==`` with a wildcard. Because
          pip prioritizes the latest version, preferring explicit upper bounds
          can rule out infeasible candidates sooner. This does not imply that
          upper bounds are good practice; they can make dependency management
          and resolution harder.
        * Order user-specified requirements as they are specified, placing
          other requirements afterward.
        * Any "non-free" requirement, i.e., one that contains at least one
          operator, such as ``>=`` or ``!=``.
        * Alphabetical order for consistency (aids debuggability).
        """
        try:
            next(iter(information[identifier]))
        except StopIteration:
            # There is no information for this identifier, so there's no known
            # candidates.
            has_information = False
        else:
            has_information = True

        if not has_information:
            direct = False
            ireqs: tuple[InstallRequirement | None, ...] = ()
        else:
            # Go through the information and for each requirement,
            # check if it's explicit (e.g., a direct link) and get the
            # InstallRequirement (the second element) from get_candidate_lookup()
            directs, ireqs = zip(
                *(
                    (isinstance(r, ExplicitRequirement), r.get_candidate_lookup()[1])
                    for r, _ in information[identifier]
                )
            )
            direct = any(directs)

        operators: list[tuple[str, str]] = [
            (specifier.operator, specifier.version)
            for specifier_set in (ireq.specifier for ireq in ireqs if ireq)
            for specifier in specifier_set
        ]

        pinned = any(((op[:2] == "==") and ("*" not in ver)) for op, ver in operators)
        upper_bounded = any(
            ((op in ("<", "<=", "~=")) or (op == "==" and "*" in ver))
            for op, ver in operators
        )
        unfree = bool(operators)
        requested_order = self._user_requested.get(identifier, math.inf)

        return (
            not direct,
            not pinned,
            not upper_bounded,
            requested_order,
            not unfree,
            identifier,
        )

    def find_matches(
        self,
        identifier: str,
        requirements: Mapping[str, Iterator[Requirement]],
        incompatibilities: Mapping[str, Iterator[Candidate]],
    ) -> Iterable[Candidate]:
        def _eligible_for_upgrade(identifier: str) -> bool:
            """Are upgrades allowed for this project?

            This checks the upgrade strategy, and whether the project was one
            that the user specified in the command line, in order to decide
            whether we should upgrade if there's a newer version available.

            (Note that we don't need access to the `--upgrade` flag, because
            an upgrade strategy of "to-satisfy-only" means that `--upgrade`
            was not specified).
            """
            if self._upgrade_strategy == "eager":
                return True
            elif self._upgrade_strategy == "only-if-needed":
                user_order = _get_with_identifier(
                    self._user_requested,
                    identifier,
                    default=None,
                )
                return user_order is not None
            return False

        constraint = _get_with_identifier(
            self._constraints,
            identifier,
            default=Constraint.empty(),
        )
        return self._factory.find_candidates(
            identifier=identifier,
            requirements=requirements,
            constraint=constraint,
            prefers_installed=(not _eligible_for_upgrade(identifier)),
            incompatibilities=incompatibilities,
            is_satisfied_by=self.is_satisfied_by,
        )

    @staticmethod
    @cache
    def is_satisfied_by(requirement: Requirement, candidate: Candidate) -> bool:
        return requirement.is_satisfied_by(candidate)

    def get_dependencies(self, candidate: Candidate) -> Iterable[Requirement]:
        with_requires = not self._ignore_dependencies
        # iter_dependencies() can perform nontrivial work so delay until needed.
        return (r for r in candidate.iter_dependencies(with_requires) if r is not None)

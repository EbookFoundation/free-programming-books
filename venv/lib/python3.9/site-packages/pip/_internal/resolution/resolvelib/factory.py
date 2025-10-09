from __future__ import annotations

import contextlib
import functools
import logging
from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import (
    TYPE_CHECKING,
    Callable,
    NamedTuple,
    Protocol,
    TypeVar,
    cast,
)

from pip._vendor.packaging.requirements import InvalidRequirement
from pip._vendor.packaging.specifiers import SpecifierSet
from pip._vendor.packaging.utils import NormalizedName, canonicalize_name
from pip._vendor.packaging.version import InvalidVersion, Version
from pip._vendor.resolvelib import ResolutionImpossible

from pip._internal.cache import CacheEntry, WheelCache
from pip._internal.exceptions import (
    DistributionNotFound,
    InstallationError,
    InvalidInstalledPackage,
    MetadataInconsistent,
    MetadataInvalid,
    UnsupportedPythonVersion,
    UnsupportedWheel,
)
from pip._internal.index.package_finder import PackageFinder
from pip._internal.metadata import BaseDistribution, get_default_environment
from pip._internal.models.link import Link
from pip._internal.models.wheel import Wheel
from pip._internal.operations.prepare import RequirementPreparer
from pip._internal.req.constructors import (
    install_req_drop_extras,
    install_req_from_link_and_ireq,
)
from pip._internal.req.req_install import (
    InstallRequirement,
    check_invalid_constraint_type,
)
from pip._internal.resolution.base import InstallRequirementProvider
from pip._internal.utils.compatibility_tags import get_supported
from pip._internal.utils.hashes import Hashes
from pip._internal.utils.packaging import get_requirement
from pip._internal.utils.virtualenv import running_under_virtualenv

from .base import Candidate, Constraint, Requirement
from .candidates import (
    AlreadyInstalledCandidate,
    BaseCandidate,
    EditableCandidate,
    ExtrasCandidate,
    LinkCandidate,
    RequiresPythonCandidate,
    as_base_candidate,
)
from .found_candidates import FoundCandidates, IndexCandidateInfo
from .requirements import (
    ExplicitRequirement,
    RequiresPythonRequirement,
    SpecifierRequirement,
    SpecifierWithoutExtrasRequirement,
    UnsatisfiableRequirement,
)

if TYPE_CHECKING:

    class ConflictCause(Protocol):
        requirement: RequiresPythonRequirement
        parent: Candidate


logger = logging.getLogger(__name__)

C = TypeVar("C")
Cache = dict[Link, C]


class CollectedRootRequirements(NamedTuple):
    requirements: list[Requirement]
    constraints: dict[str, Constraint]
    user_requested: dict[str, int]


class Factory:
    def __init__(
        self,
        finder: PackageFinder,
        preparer: RequirementPreparer,
        make_install_req: InstallRequirementProvider,
        wheel_cache: WheelCache | None,
        use_user_site: bool,
        force_reinstall: bool,
        ignore_installed: bool,
        ignore_requires_python: bool,
        py_version_info: tuple[int, ...] | None = None,
    ) -> None:
        self._finder = finder
        self.preparer = preparer
        self._wheel_cache = wheel_cache
        self._python_candidate = RequiresPythonCandidate(py_version_info)
        self._make_install_req_from_spec = make_install_req
        self._use_user_site = use_user_site
        self._force_reinstall = force_reinstall
        self._ignore_requires_python = ignore_requires_python

        self._build_failures: Cache[InstallationError] = {}
        self._link_candidate_cache: Cache[LinkCandidate] = {}
        self._editable_candidate_cache: Cache[EditableCandidate] = {}
        self._installed_candidate_cache: dict[str, AlreadyInstalledCandidate] = {}
        self._extras_candidate_cache: dict[
            tuple[int, frozenset[NormalizedName]], ExtrasCandidate
        ] = {}
        self._supported_tags_cache = get_supported()

        if not ignore_installed:
            env = get_default_environment()
            self._installed_dists = {
                dist.canonical_name: dist
                for dist in env.iter_installed_distributions(local_only=False)
            }
        else:
            self._installed_dists = {}

    @property
    def force_reinstall(self) -> bool:
        return self._force_reinstall

    def _fail_if_link_is_unsupported_wheel(self, link: Link) -> None:
        if not link.is_wheel:
            return
        wheel = Wheel(link.filename)
        if wheel.supported(self._finder.target_python.get_unsorted_tags()):
            return
        msg = f"{link.filename} is not a supported wheel on this platform."
        raise UnsupportedWheel(msg)

    def _make_extras_candidate(
        self,
        base: BaseCandidate,
        extras: frozenset[str],
        *,
        comes_from: InstallRequirement | None = None,
    ) -> ExtrasCandidate:
        cache_key = (id(base), frozenset(canonicalize_name(e) for e in extras))
        try:
            candidate = self._extras_candidate_cache[cache_key]
        except KeyError:
            candidate = ExtrasCandidate(base, extras, comes_from=comes_from)
            self._extras_candidate_cache[cache_key] = candidate
        return candidate

    def _make_candidate_from_dist(
        self,
        dist: BaseDistribution,
        extras: frozenset[str],
        template: InstallRequirement,
    ) -> Candidate:
        try:
            base = self._installed_candidate_cache[dist.canonical_name]
        except KeyError:
            base = AlreadyInstalledCandidate(dist, template, factory=self)
            self._installed_candidate_cache[dist.canonical_name] = base
        if not extras:
            return base
        return self._make_extras_candidate(base, extras, comes_from=template)

    def _make_candidate_from_link(
        self,
        link: Link,
        extras: frozenset[str],
        template: InstallRequirement,
        name: NormalizedName | None,
        version: Version | None,
    ) -> Candidate | None:
        base: BaseCandidate | None = self._make_base_candidate_from_link(
            link, template, name, version
        )
        if not extras or base is None:
            return base
        return self._make_extras_candidate(base, extras, comes_from=template)

    def _make_base_candidate_from_link(
        self,
        link: Link,
        template: InstallRequirement,
        name: NormalizedName | None,
        version: Version | None,
    ) -> BaseCandidate | None:
        # TODO: Check already installed candidate, and use it if the link and
        # editable flag match.

        if link in self._build_failures:
            # We already tried this candidate before, and it does not build.
            # Don't bother trying again.
            return None

        if template.editable:
            if link not in self._editable_candidate_cache:
                try:
                    self._editable_candidate_cache[link] = EditableCandidate(
                        link,
                        template,
                        factory=self,
                        name=name,
                        version=version,
                    )
                except (MetadataInconsistent, MetadataInvalid) as e:
                    logger.info(
                        "Discarding [blue underline]%s[/]: [yellow]%s[reset]",
                        link,
                        e,
                        extra={"markup": True},
                    )
                    self._build_failures[link] = e
                    return None

            return self._editable_candidate_cache[link]
        else:
            if link not in self._link_candidate_cache:
                try:
                    self._link_candidate_cache[link] = LinkCandidate(
                        link,
                        template,
                        factory=self,
                        name=name,
                        version=version,
                    )
                except MetadataInconsistent as e:
                    logger.info(
                        "Discarding [blue underline]%s[/]: [yellow]%s[reset]",
                        link,
                        e,
                        extra={"markup": True},
                    )
                    self._build_failures[link] = e
                    return None
            return self._link_candidate_cache[link]

    def _iter_found_candidates(
        self,
        ireqs: Sequence[InstallRequirement],
        specifier: SpecifierSet,
        hashes: Hashes,
        prefers_installed: bool,
        incompatible_ids: set[int],
    ) -> Iterable[Candidate]:
        if not ireqs:
            return ()

        # The InstallRequirement implementation requires us to give it a
        # "template". Here we just choose the first requirement to represent
        # all of them.
        # Hopefully the Project model can correct this mismatch in the future.
        template = ireqs[0]
        assert template.req, "Candidates found on index must be PEP 508"
        name = canonicalize_name(template.req.name)

        extras: frozenset[str] = frozenset()
        for ireq in ireqs:
            assert ireq.req, "Candidates found on index must be PEP 508"
            specifier &= ireq.req.specifier
            hashes &= ireq.hashes(trust_internet=False)
            extras |= frozenset(ireq.extras)

        def _get_installed_candidate() -> Candidate | None:
            """Get the candidate for the currently-installed version."""
            # If --force-reinstall is set, we want the version from the index
            # instead, so we "pretend" there is nothing installed.
            if self._force_reinstall:
                return None
            try:
                installed_dist = self._installed_dists[name]
            except KeyError:
                return None

            try:
                # Don't use the installed distribution if its version
                # does not fit the current dependency graph.
                if not specifier.contains(installed_dist.version, prereleases=True):
                    return None
            except InvalidVersion as e:
                raise InvalidInstalledPackage(dist=installed_dist, invalid_exc=e)

            candidate = self._make_candidate_from_dist(
                dist=installed_dist,
                extras=extras,
                template=template,
            )
            # The candidate is a known incompatibility. Don't use it.
            if id(candidate) in incompatible_ids:
                return None
            return candidate

        def iter_index_candidate_infos() -> Iterator[IndexCandidateInfo]:
            result = self._finder.find_best_candidate(
                project_name=name,
                specifier=specifier,
                hashes=hashes,
            )
            icans = result.applicable_candidates

            # PEP 592: Yanked releases are ignored unless the specifier
            # explicitly pins a version (via '==' or '===') that can be
            # solely satisfied by a yanked release.
            all_yanked = all(ican.link.is_yanked for ican in icans)

            def is_pinned(specifier: SpecifierSet) -> bool:
                for sp in specifier:
                    if sp.operator == "===":
                        return True
                    if sp.operator != "==":
                        continue
                    if sp.version.endswith(".*"):
                        continue
                    return True
                return False

            pinned = is_pinned(specifier)

            # PackageFinder returns earlier versions first, so we reverse.
            for ican in reversed(icans):
                if not (all_yanked and pinned) and ican.link.is_yanked:
                    continue
                func = functools.partial(
                    self._make_candidate_from_link,
                    link=ican.link,
                    extras=extras,
                    template=template,
                    name=name,
                    version=ican.version,
                )
                yield ican.version, func

        return FoundCandidates(
            iter_index_candidate_infos,
            _get_installed_candidate(),
            prefers_installed,
            incompatible_ids,
        )

    def _iter_explicit_candidates_from_base(
        self,
        base_requirements: Iterable[Requirement],
        extras: frozenset[str],
    ) -> Iterator[Candidate]:
        """Produce explicit candidates from the base given an extra-ed package.

        :param base_requirements: Requirements known to the resolver. The
            requirements are guaranteed to not have extras.
        :param extras: The extras to inject into the explicit requirements'
            candidates.
        """
        for req in base_requirements:
            lookup_cand, _ = req.get_candidate_lookup()
            if lookup_cand is None:  # Not explicit.
                continue
            # We've stripped extras from the identifier, and should always
            # get a BaseCandidate here, unless there's a bug elsewhere.
            base_cand = as_base_candidate(lookup_cand)
            assert base_cand is not None, "no extras here"
            yield self._make_extras_candidate(base_cand, extras)

    def _iter_candidates_from_constraints(
        self,
        identifier: str,
        constraint: Constraint,
        template: InstallRequirement,
    ) -> Iterator[Candidate]:
        """Produce explicit candidates from constraints.

        This creates "fake" InstallRequirement objects that are basically clones
        of what "should" be the template, but with original_link set to link.
        """
        for link in constraint.links:
            self._fail_if_link_is_unsupported_wheel(link)
            candidate = self._make_base_candidate_from_link(
                link,
                template=install_req_from_link_and_ireq(link, template),
                name=canonicalize_name(identifier),
                version=None,
            )
            if candidate:
                yield candidate

    def find_candidates(
        self,
        identifier: str,
        requirements: Mapping[str, Iterable[Requirement]],
        incompatibilities: Mapping[str, Iterator[Candidate]],
        constraint: Constraint,
        prefers_installed: bool,
        is_satisfied_by: Callable[[Requirement, Candidate], bool],
    ) -> Iterable[Candidate]:
        # Collect basic lookup information from the requirements.
        explicit_candidates: set[Candidate] = set()
        ireqs: list[InstallRequirement] = []
        for req in requirements[identifier]:
            cand, ireq = req.get_candidate_lookup()
            if cand is not None:
                explicit_candidates.add(cand)
            if ireq is not None:
                ireqs.append(ireq)

        # If the current identifier contains extras, add requires and explicit
        # candidates from entries from extra-less identifier.
        with contextlib.suppress(InvalidRequirement):
            parsed_requirement = get_requirement(identifier)
            if parsed_requirement.name != identifier:
                explicit_candidates.update(
                    self._iter_explicit_candidates_from_base(
                        requirements.get(parsed_requirement.name, ()),
                        frozenset(parsed_requirement.extras),
                    ),
                )
                for req in requirements.get(parsed_requirement.name, []):
                    _, ireq = req.get_candidate_lookup()
                    if ireq is not None:
                        ireqs.append(ireq)

        # Add explicit candidates from constraints. We only do this if there are
        # known ireqs, which represent requirements not already explicit. If
        # there are no ireqs, we're constraining already-explicit requirements,
        # which is handled later when we return the explicit candidates.
        if ireqs:
            try:
                explicit_candidates.update(
                    self._iter_candidates_from_constraints(
                        identifier,
                        constraint,
                        template=ireqs[0],
                    ),
                )
            except UnsupportedWheel:
                # If we're constrained to install a wheel incompatible with the
                # target architecture, no candidates will ever be valid.
                return ()

        # Since we cache all the candidates, incompatibility identification
        # can be made quicker by comparing only the id() values.
        incompat_ids = {id(c) for c in incompatibilities.get(identifier, ())}

        # If none of the requirements want an explicit candidate, we can ask
        # the finder for candidates.
        if not explicit_candidates:
            return self._iter_found_candidates(
                ireqs,
                constraint.specifier,
                constraint.hashes,
                prefers_installed,
                incompat_ids,
            )

        return (
            c
            for c in explicit_candidates
            if id(c) not in incompat_ids
            and constraint.is_satisfied_by(c)
            and all(is_satisfied_by(req, c) for req in requirements[identifier])
        )

    def _make_requirements_from_install_req(
        self, ireq: InstallRequirement, requested_extras: Iterable[str]
    ) -> Iterator[Requirement]:
        """
        Returns requirement objects associated with the given InstallRequirement. In
        most cases this will be a single object but the following special cases exist:
            - the InstallRequirement has markers that do not apply -> result is empty
            - the InstallRequirement has both a constraint (or link) and extras
                -> result is split in two requirement objects: one with the constraint
                (or link) and one with the extra. This allows centralized constraint
                handling for the base, resulting in fewer candidate rejections.
        """
        if not ireq.match_markers(requested_extras):
            logger.info(
                "Ignoring %s: markers '%s' don't match your environment",
                ireq.name,
                ireq.markers,
            )
        elif not ireq.link:
            if ireq.extras and ireq.req is not None and ireq.req.specifier:
                yield SpecifierWithoutExtrasRequirement(ireq)
            yield SpecifierRequirement(ireq)
        else:
            self._fail_if_link_is_unsupported_wheel(ireq.link)
            # Always make the link candidate for the base requirement to make it
            # available to `find_candidates` for explicit candidate lookup for any
            # set of extras.
            # The extras are required separately via a second requirement.
            cand = self._make_base_candidate_from_link(
                ireq.link,
                template=install_req_drop_extras(ireq) if ireq.extras else ireq,
                name=canonicalize_name(ireq.name) if ireq.name else None,
                version=None,
            )
            if cand is None:
                # There's no way we can satisfy a URL requirement if the underlying
                # candidate fails to build. An unnamed URL must be user-supplied, so
                # we fail eagerly. If the URL is named, an unsatisfiable requirement
                # can make the resolver do the right thing, either backtrack (and
                # maybe find some other requirement that's buildable) or raise a
                # ResolutionImpossible eventually.
                if not ireq.name:
                    raise self._build_failures[ireq.link]
                yield UnsatisfiableRequirement(canonicalize_name(ireq.name))
            else:
                # require the base from the link
                yield self.make_requirement_from_candidate(cand)
                if ireq.extras:
                    # require the extras on top of the base candidate
                    yield self.make_requirement_from_candidate(
                        self._make_extras_candidate(cand, frozenset(ireq.extras))
                    )

    def collect_root_requirements(
        self, root_ireqs: list[InstallRequirement]
    ) -> CollectedRootRequirements:
        collected = CollectedRootRequirements([], {}, {})
        for i, ireq in enumerate(root_ireqs):
            if ireq.constraint:
                # Ensure we only accept valid constraints
                problem = check_invalid_constraint_type(ireq)
                if problem:
                    raise InstallationError(problem)
                if not ireq.match_markers():
                    continue
                assert ireq.name, "Constraint must be named"
                name = canonicalize_name(ireq.name)
                if name in collected.constraints:
                    collected.constraints[name] &= ireq
                else:
                    collected.constraints[name] = Constraint.from_ireq(ireq)
            else:
                reqs = list(
                    self._make_requirements_from_install_req(
                        ireq,
                        requested_extras=(),
                    )
                )
                if not reqs:
                    continue
                template = reqs[0]
                if ireq.user_supplied and template.name not in collected.user_requested:
                    collected.user_requested[template.name] = i
                collected.requirements.extend(reqs)
        # Put requirements with extras at the end of the root requires. This does not
        # affect resolvelib's picking preference but it does affect its initial criteria
        # population: by putting extras at the end we enable the candidate finder to
        # present resolvelib with a smaller set of candidates to resolvelib, already
        # taking into account any non-transient constraints on the associated base. This
        # means resolvelib will have fewer candidates to visit and reject.
        # Python's list sort is stable, meaning relative order is kept for objects with
        # the same key.
        collected.requirements.sort(key=lambda r: r.name != r.project_name)
        return collected

    def make_requirement_from_candidate(
        self, candidate: Candidate
    ) -> ExplicitRequirement:
        return ExplicitRequirement(candidate)

    def make_requirements_from_spec(
        self,
        specifier: str,
        comes_from: InstallRequirement | None,
        requested_extras: Iterable[str] = (),
    ) -> Iterator[Requirement]:
        """
        Returns requirement objects associated with the given specifier. In most cases
        this will be a single object but the following special cases exist:
            - the specifier has markers that do not apply -> result is empty
            - the specifier has both a constraint and extras -> result is split
                in two requirement objects: one with the constraint and one with the
                extra. This allows centralized constraint handling for the base,
                resulting in fewer candidate rejections.
        """
        ireq = self._make_install_req_from_spec(specifier, comes_from)
        return self._make_requirements_from_install_req(ireq, requested_extras)

    def make_requires_python_requirement(
        self,
        specifier: SpecifierSet,
    ) -> Requirement | None:
        if self._ignore_requires_python:
            return None
        # Don't bother creating a dependency for an empty Requires-Python.
        if not str(specifier):
            return None
        return RequiresPythonRequirement(specifier, self._python_candidate)

    def get_wheel_cache_entry(self, link: Link, name: str | None) -> CacheEntry | None:
        """Look up the link in the wheel cache.

        If ``preparer.require_hashes`` is True, don't use the wheel cache,
        because cached wheels, always built locally, have different hashes
        than the files downloaded from the index server and thus throw false
        hash mismatches. Furthermore, cached wheels at present have
        nondeterministic contents due to file modification times.
        """
        if self._wheel_cache is None:
            return None
        return self._wheel_cache.get_cache_entry(
            link=link,
            package_name=name,
            supported_tags=self._supported_tags_cache,
        )

    def get_dist_to_uninstall(self, candidate: Candidate) -> BaseDistribution | None:
        # TODO: Are there more cases this needs to return True? Editable?
        dist = self._installed_dists.get(candidate.project_name)
        if dist is None:  # Not installed, no uninstallation required.
            return None

        # We're installing into global site. The current installation must
        # be uninstalled, no matter it's in global or user site, because the
        # user site installation has precedence over global.
        if not self._use_user_site:
            return dist

        # We're installing into user site. Remove the user site installation.
        if dist.in_usersite:
            return dist

        # We're installing into user site, but the installed incompatible
        # package is in global site. We can't uninstall that, and would let
        # the new user installation to "shadow" it. But shadowing won't work
        # in virtual environments, so we error out.
        if running_under_virtualenv() and dist.in_site_packages:
            message = (
                f"Will not install to the user site because it will lack "
                f"sys.path precedence to {dist.raw_name} in {dist.location}"
            )
            raise InstallationError(message)
        return None

    def _report_requires_python_error(
        self, causes: Sequence[ConflictCause]
    ) -> UnsupportedPythonVersion:
        assert causes, "Requires-Python error reported with no cause"

        version = self._python_candidate.version

        if len(causes) == 1:
            specifier = str(causes[0].requirement.specifier)
            message = (
                f"Package {causes[0].parent.name!r} requires a different "
                f"Python: {version} not in {specifier!r}"
            )
            return UnsupportedPythonVersion(message)

        message = f"Packages require a different Python. {version} not in:"
        for cause in causes:
            package = cause.parent.format_for_error()
            specifier = str(cause.requirement.specifier)
            message += f"\n{specifier!r} (required by {package})"
        return UnsupportedPythonVersion(message)

    def _report_single_requirement_conflict(
        self, req: Requirement, parent: Candidate | None
    ) -> DistributionNotFound:
        if parent is None:
            req_disp = str(req)
        else:
            req_disp = f"{req} (from {parent.name})"

        cands = self._finder.find_all_candidates(req.project_name)
        skipped_by_requires_python = self._finder.requires_python_skipped_reasons()

        versions_set: set[Version] = set()
        yanked_versions_set: set[Version] = set()
        for c in cands:
            is_yanked = c.link.is_yanked if c.link else False
            if is_yanked:
                yanked_versions_set.add(c.version)
            else:
                versions_set.add(c.version)

        versions = [str(v) for v in sorted(versions_set)]
        yanked_versions = [str(v) for v in sorted(yanked_versions_set)]

        if yanked_versions:
            # Saying "version X is yanked" isn't entirely accurate.
            # https://github.com/pypa/pip/issues/11745#issuecomment-1402805842
            logger.critical(
                "Ignored the following yanked versions: %s",
                ", ".join(yanked_versions) or "none",
            )
        if skipped_by_requires_python:
            logger.critical(
                "Ignored the following versions that require a different python "
                "version: %s",
                "; ".join(skipped_by_requires_python) or "none",
            )
        logger.critical(
            "Could not find a version that satisfies the requirement %s "
            "(from versions: %s)",
            req_disp,
            ", ".join(versions) or "none",
        )
        if str(req) == "requirements.txt":
            logger.info(
                "HINT: You are attempting to install a package literally "
                'named "requirements.txt" (which cannot exist). Consider '
                "using the '-r' flag to install the packages listed in "
                "requirements.txt"
            )

        return DistributionNotFound(f"No matching distribution found for {req}")

    def get_installation_error(
        self,
        e: ResolutionImpossible[Requirement, Candidate],
        constraints: dict[str, Constraint],
    ) -> InstallationError:
        assert e.causes, "Installation error reported with no cause"

        # If one of the things we can't solve is "we need Python X.Y",
        # that is what we report.
        requires_python_causes = [
            cause
            for cause in e.causes
            if isinstance(cause.requirement, RequiresPythonRequirement)
            and not cause.requirement.is_satisfied_by(self._python_candidate)
        ]
        if requires_python_causes:
            # The comprehension above makes sure all Requirement instances are
            # RequiresPythonRequirement, so let's cast for convenience.
            return self._report_requires_python_error(
                cast("Sequence[ConflictCause]", requires_python_causes),
            )

        # Otherwise, we have a set of causes which can't all be satisfied
        # at once.

        # The simplest case is when we have *one* cause that can't be
        # satisfied. We just report that case.
        if len(e.causes) == 1:
            req, parent = next(iter(e.causes))
            if req.name not in constraints:
                return self._report_single_requirement_conflict(req, parent)

        # OK, we now have a list of requirements that can't all be
        # satisfied at once.

        # A couple of formatting helpers
        def text_join(parts: list[str]) -> str:
            if len(parts) == 1:
                return parts[0]

            return ", ".join(parts[:-1]) + " and " + parts[-1]

        def describe_trigger(parent: Candidate) -> str:
            ireq = parent.get_install_requirement()
            if not ireq or not ireq.comes_from:
                return f"{parent.name}=={parent.version}"
            if isinstance(ireq.comes_from, InstallRequirement):
                return str(ireq.comes_from.name)
            return str(ireq.comes_from)

        triggers = set()
        for req, parent in e.causes:
            if parent is None:
                # This is a root requirement, so we can report it directly
                trigger = req.format_for_error()
            else:
                trigger = describe_trigger(parent)
            triggers.add(trigger)

        if triggers:
            info = text_join(sorted(triggers))
        else:
            info = "the requested packages"

        msg = (
            f"Cannot install {info} because these package versions "
            "have conflicting dependencies."
        )
        logger.critical(msg)
        msg = "\nThe conflict is caused by:"

        relevant_constraints = set()
        for req, parent in e.causes:
            if req.name in constraints:
                relevant_constraints.add(req.name)
            msg = msg + "\n    "
            if parent:
                msg = msg + f"{parent.name} {parent.version} depends on "
            else:
                msg = msg + "The user requested "
            msg = msg + req.format_for_error()
        for key in relevant_constraints:
            spec = constraints[key].specifier
            msg += f"\n    The user requested (constraint) {key}{spec}"

        msg = (
            msg
            + "\n\n"
            + "To fix this you could try to:\n"
            + "1. loosen the range of package versions you've specified\n"
            + "2. remove package versions to allow pip to attempt to solve "
            + "the dependency conflict\n"
        )

        logger.info(msg)

        return DistributionNotFound(
            "ResolutionImpossible: for help visit "
            "https://pip.pypa.io/en/latest/topics/dependency-resolution/"
            "#dealing-with-dependency-conflicts"
        )

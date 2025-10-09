"""Routines related to PyPI, indexes"""

from __future__ import annotations

import enum
import functools
import itertools
import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Optional,
    Union,
)

from pip._vendor.packaging import specifiers
from pip._vendor.packaging.tags import Tag
from pip._vendor.packaging.utils import canonicalize_name
from pip._vendor.packaging.version import InvalidVersion, _BaseVersion
from pip._vendor.packaging.version import parse as parse_version

from pip._internal.exceptions import (
    BestVersionAlreadyInstalled,
    DistributionNotFound,
    InvalidWheelFilename,
    UnsupportedWheel,
)
from pip._internal.index.collector import LinkCollector, parse_links
from pip._internal.models.candidate import InstallationCandidate
from pip._internal.models.format_control import FormatControl
from pip._internal.models.link import Link
from pip._internal.models.search_scope import SearchScope
from pip._internal.models.selection_prefs import SelectionPreferences
from pip._internal.models.target_python import TargetPython
from pip._internal.models.wheel import Wheel
from pip._internal.req import InstallRequirement
from pip._internal.utils._log import getLogger
from pip._internal.utils.filetypes import WHEEL_EXTENSION
from pip._internal.utils.hashes import Hashes
from pip._internal.utils.logging import indent_log
from pip._internal.utils.misc import build_netloc
from pip._internal.utils.packaging import check_requires_python
from pip._internal.utils.unpacking import SUPPORTED_EXTENSIONS

if TYPE_CHECKING:
    from typing_extensions import TypeGuard

__all__ = ["FormatControl", "BestCandidateResult", "PackageFinder"]


logger = getLogger(__name__)

BuildTag = Union[tuple[()], tuple[int, str]]
CandidateSortingKey = tuple[int, int, int, _BaseVersion, Optional[int], BuildTag]


def _check_link_requires_python(
    link: Link,
    version_info: tuple[int, int, int],
    ignore_requires_python: bool = False,
) -> bool:
    """
    Return whether the given Python version is compatible with a link's
    "Requires-Python" value.

    :param version_info: A 3-tuple of ints representing the Python
        major-minor-micro version to check.
    :param ignore_requires_python: Whether to ignore the "Requires-Python"
        value if the given Python version isn't compatible.
    """
    try:
        is_compatible = check_requires_python(
            link.requires_python,
            version_info=version_info,
        )
    except specifiers.InvalidSpecifier:
        logger.debug(
            "Ignoring invalid Requires-Python (%r) for link: %s",
            link.requires_python,
            link,
        )
    else:
        if not is_compatible:
            version = ".".join(map(str, version_info))
            if not ignore_requires_python:
                logger.verbose(
                    "Link requires a different Python (%s not in: %r): %s",
                    version,
                    link.requires_python,
                    link,
                )
                return False

            logger.debug(
                "Ignoring failed Requires-Python check (%s not in: %r) for link: %s",
                version,
                link.requires_python,
                link,
            )

    return True


class LinkType(enum.Enum):
    candidate = enum.auto()
    different_project = enum.auto()
    yanked = enum.auto()
    format_unsupported = enum.auto()
    format_invalid = enum.auto()
    platform_mismatch = enum.auto()
    requires_python_mismatch = enum.auto()


class LinkEvaluator:
    """
    Responsible for evaluating links for a particular project.
    """

    _py_version_re = re.compile(r"-py([123]\.?[0-9]?)$")

    # Don't include an allow_yanked default value to make sure each call
    # site considers whether yanked releases are allowed. This also causes
    # that decision to be made explicit in the calling code, which helps
    # people when reading the code.
    def __init__(
        self,
        project_name: str,
        canonical_name: str,
        formats: frozenset[str],
        target_python: TargetPython,
        allow_yanked: bool,
        ignore_requires_python: bool | None = None,
    ) -> None:
        """
        :param project_name: The user supplied package name.
        :param canonical_name: The canonical package name.
        :param formats: The formats allowed for this package. Should be a set
            with 'binary' or 'source' or both in it.
        :param target_python: The target Python interpreter to use when
            evaluating link compatibility. This is used, for example, to
            check wheel compatibility, as well as when checking the Python
            version, e.g. the Python version embedded in a link filename
            (or egg fragment) and against an HTML link's optional PEP 503
            "data-requires-python" attribute.
        :param allow_yanked: Whether files marked as yanked (in the sense
            of PEP 592) are permitted to be candidates for install.
        :param ignore_requires_python: Whether to ignore incompatible
            PEP 503 "data-requires-python" values in HTML links. Defaults
            to False.
        """
        if ignore_requires_python is None:
            ignore_requires_python = False

        self._allow_yanked = allow_yanked
        self._canonical_name = canonical_name
        self._ignore_requires_python = ignore_requires_python
        self._formats = formats
        self._target_python = target_python

        self.project_name = project_name

    def evaluate_link(self, link: Link) -> tuple[LinkType, str]:
        """
        Determine whether a link is a candidate for installation.

        :return: A tuple (result, detail), where *result* is an enum
            representing whether the evaluation found a candidate, or the reason
            why one is not found. If a candidate is found, *detail* will be the
            candidate's version string; if one is not found, it contains the
            reason the link fails to qualify.
        """
        version = None
        if link.is_yanked and not self._allow_yanked:
            reason = link.yanked_reason or "<none given>"
            return (LinkType.yanked, f"yanked for reason: {reason}")

        if link.egg_fragment:
            egg_info = link.egg_fragment
            ext = link.ext
        else:
            egg_info, ext = link.splitext()
            if not ext:
                return (LinkType.format_unsupported, "not a file")
            if ext not in SUPPORTED_EXTENSIONS:
                return (
                    LinkType.format_unsupported,
                    f"unsupported archive format: {ext}",
                )
            if "binary" not in self._formats and ext == WHEEL_EXTENSION:
                reason = f"No binaries permitted for {self.project_name}"
                return (LinkType.format_unsupported, reason)
            if "macosx10" in link.path and ext == ".zip":
                return (LinkType.format_unsupported, "macosx10 one")
            if ext == WHEEL_EXTENSION:
                try:
                    wheel = Wheel(link.filename)
                except InvalidWheelFilename:
                    return (
                        LinkType.format_invalid,
                        "invalid wheel filename",
                    )
                if canonicalize_name(wheel.name) != self._canonical_name:
                    reason = f"wrong project name (not {self.project_name})"
                    return (LinkType.different_project, reason)

                supported_tags = self._target_python.get_unsorted_tags()
                if not wheel.supported(supported_tags):
                    # Include the wheel's tags in the reason string to
                    # simplify troubleshooting compatibility issues.
                    file_tags = ", ".join(wheel.get_formatted_file_tags())
                    reason = (
                        f"none of the wheel's tags ({file_tags}) are compatible "
                        f"(run pip debug --verbose to show compatible tags)"
                    )
                    return (LinkType.platform_mismatch, reason)

                version = wheel.version

        # This should be up by the self.ok_binary check, but see issue 2700.
        if "source" not in self._formats and ext != WHEEL_EXTENSION:
            reason = f"No sources permitted for {self.project_name}"
            return (LinkType.format_unsupported, reason)

        if not version:
            version = _extract_version_from_fragment(
                egg_info,
                self._canonical_name,
            )
        if not version:
            reason = f"Missing project version for {self.project_name}"
            return (LinkType.format_invalid, reason)

        match = self._py_version_re.search(version)
        if match:
            version = version[: match.start()]
            py_version = match.group(1)
            if py_version != self._target_python.py_version:
                return (
                    LinkType.platform_mismatch,
                    "Python version is incorrect",
                )

        supports_python = _check_link_requires_python(
            link,
            version_info=self._target_python.py_version_info,
            ignore_requires_python=self._ignore_requires_python,
        )
        if not supports_python:
            requires_python = link.requires_python
            if requires_python:

                def get_version_sort_key(v: str) -> tuple[int, ...]:
                    return tuple(int(s) for s in v.split(".") if s.isdigit())

                requires_python = ",".join(
                    sorted(
                        (str(s) for s in specifiers.SpecifierSet(requires_python)),
                        key=get_version_sort_key,
                    )
                )
            reason = f"{version} Requires-Python {requires_python}"
            return (LinkType.requires_python_mismatch, reason)

        logger.debug("Found link %s, version: %s", link, version)

        return (LinkType.candidate, version)


def filter_unallowed_hashes(
    candidates: list[InstallationCandidate],
    hashes: Hashes | None,
    project_name: str,
) -> list[InstallationCandidate]:
    """
    Filter out candidates whose hashes aren't allowed, and return a new
    list of candidates.

    If at least one candidate has an allowed hash, then all candidates with
    either an allowed hash or no hash specified are returned.  Otherwise,
    the given candidates are returned.

    Including the candidates with no hash specified when there is a match
    allows a warning to be logged if there is a more preferred candidate
    with no hash specified.  Returning all candidates in the case of no
    matches lets pip report the hash of the candidate that would otherwise
    have been installed (e.g. permitting the user to more easily update
    their requirements file with the desired hash).
    """
    if not hashes:
        logger.debug(
            "Given no hashes to check %s links for project %r: "
            "discarding no candidates",
            len(candidates),
            project_name,
        )
        # Make sure we're not returning back the given value.
        return list(candidates)

    matches_or_no_digest = []
    # Collect the non-matches for logging purposes.
    non_matches = []
    match_count = 0
    for candidate in candidates:
        link = candidate.link
        if not link.has_hash:
            pass
        elif link.is_hash_allowed(hashes=hashes):
            match_count += 1
        else:
            non_matches.append(candidate)
            continue

        matches_or_no_digest.append(candidate)

    if match_count:
        filtered = matches_or_no_digest
    else:
        # Make sure we're not returning back the given value.
        filtered = list(candidates)

    if len(filtered) == len(candidates):
        discard_message = "discarding no candidates"
    else:
        discard_message = "discarding {} non-matches:\n  {}".format(
            len(non_matches),
            "\n  ".join(str(candidate.link) for candidate in non_matches),
        )

    logger.debug(
        "Checked %s links for project %r against %s hashes "
        "(%s matches, %s no digest): %s",
        len(candidates),
        project_name,
        hashes.digest_count,
        match_count,
        len(matches_or_no_digest) - match_count,
        discard_message,
    )

    return filtered


@dataclass
class CandidatePreferences:
    """
    Encapsulates some of the preferences for filtering and sorting
    InstallationCandidate objects.
    """

    prefer_binary: bool = False
    allow_all_prereleases: bool = False


@dataclass(frozen=True)
class BestCandidateResult:
    """A collection of candidates, returned by `PackageFinder.find_best_candidate`.

    This class is only intended to be instantiated by CandidateEvaluator's
    `compute_best_candidate()` method.

    :param all_candidates: A sequence of all available candidates found.
    :param applicable_candidates: The applicable candidates.
    :param best_candidate: The most preferred candidate found, or None
        if no applicable candidates were found.
    """

    all_candidates: list[InstallationCandidate]
    applicable_candidates: list[InstallationCandidate]
    best_candidate: InstallationCandidate | None

    def __post_init__(self) -> None:
        assert set(self.applicable_candidates) <= set(self.all_candidates)

        if self.best_candidate is None:
            assert not self.applicable_candidates
        else:
            assert self.best_candidate in self.applicable_candidates


class CandidateEvaluator:
    """
    Responsible for filtering and sorting candidates for installation based
    on what tags are valid.
    """

    @classmethod
    def create(
        cls,
        project_name: str,
        target_python: TargetPython | None = None,
        prefer_binary: bool = False,
        allow_all_prereleases: bool = False,
        specifier: specifiers.BaseSpecifier | None = None,
        hashes: Hashes | None = None,
    ) -> CandidateEvaluator:
        """Create a CandidateEvaluator object.

        :param target_python: The target Python interpreter to use when
            checking compatibility. If None (the default), a TargetPython
            object will be constructed from the running Python.
        :param specifier: An optional object implementing `filter`
            (e.g. `packaging.specifiers.SpecifierSet`) to filter applicable
            versions.
        :param hashes: An optional collection of allowed hashes.
        """
        if target_python is None:
            target_python = TargetPython()
        if specifier is None:
            specifier = specifiers.SpecifierSet()

        supported_tags = target_python.get_sorted_tags()

        return cls(
            project_name=project_name,
            supported_tags=supported_tags,
            specifier=specifier,
            prefer_binary=prefer_binary,
            allow_all_prereleases=allow_all_prereleases,
            hashes=hashes,
        )

    def __init__(
        self,
        project_name: str,
        supported_tags: list[Tag],
        specifier: specifiers.BaseSpecifier,
        prefer_binary: bool = False,
        allow_all_prereleases: bool = False,
        hashes: Hashes | None = None,
    ) -> None:
        """
        :param supported_tags: The PEP 425 tags supported by the target
            Python in order of preference (most preferred first).
        """
        self._allow_all_prereleases = allow_all_prereleases
        self._hashes = hashes
        self._prefer_binary = prefer_binary
        self._project_name = project_name
        self._specifier = specifier
        self._supported_tags = supported_tags
        # Since the index of the tag in the _supported_tags list is used
        # as a priority, precompute a map from tag to index/priority to be
        # used in wheel.find_most_preferred_tag.
        self._wheel_tag_preferences = {
            tag: idx for idx, tag in enumerate(supported_tags)
        }

    def get_applicable_candidates(
        self,
        candidates: list[InstallationCandidate],
    ) -> list[InstallationCandidate]:
        """
        Return the applicable candidates from a list of candidates.
        """
        # Using None infers from the specifier instead.
        allow_prereleases = self._allow_all_prereleases or None
        specifier = self._specifier

        # We turn the version object into a str here because otherwise
        # when we're debundled but setuptools isn't, Python will see
        # packaging.version.Version and
        # pkg_resources._vendor.packaging.version.Version as different
        # types. This way we'll use a str as a common data interchange
        # format. If we stop using the pkg_resources provided specifier
        # and start using our own, we can drop the cast to str().
        candidates_and_versions = [(c, str(c.version)) for c in candidates]
        versions = set(
            specifier.filter(
                (v for _, v in candidates_and_versions),
                prereleases=allow_prereleases,
            )
        )

        applicable_candidates = [c for c, v in candidates_and_versions if v in versions]
        filtered_applicable_candidates = filter_unallowed_hashes(
            candidates=applicable_candidates,
            hashes=self._hashes,
            project_name=self._project_name,
        )

        return sorted(filtered_applicable_candidates, key=self._sort_key)

    def _sort_key(self, candidate: InstallationCandidate) -> CandidateSortingKey:
        """
        Function to pass as the `key` argument to a call to sorted() to sort
        InstallationCandidates by preference.

        Returns a tuple such that tuples sorting as greater using Python's
        default comparison operator are more preferred.

        The preference is as follows:

        First and foremost, candidates with allowed (matching) hashes are
        always preferred over candidates without matching hashes. This is
        because e.g. if the only candidate with an allowed hash is yanked,
        we still want to use that candidate.

        Second, excepting hash considerations, candidates that have been
        yanked (in the sense of PEP 592) are always less preferred than
        candidates that haven't been yanked. Then:

        If not finding wheels, they are sorted by version only.
        If finding wheels, then the sort order is by version, then:
          1. existing installs
          2. wheels ordered via Wheel.support_index_min(self._supported_tags)
          3. source archives
        If prefer_binary was set, then all wheels are sorted above sources.

        Note: it was considered to embed this logic into the Link
              comparison operators, but then different sdist links
              with the same version, would have to be considered equal
        """
        valid_tags = self._supported_tags
        support_num = len(valid_tags)
        build_tag: BuildTag = ()
        binary_preference = 0
        link = candidate.link
        if link.is_wheel:
            # can raise InvalidWheelFilename
            wheel = Wheel(link.filename)
            try:
                pri = -(
                    wheel.find_most_preferred_tag(
                        valid_tags, self._wheel_tag_preferences
                    )
                )
            except ValueError:
                raise UnsupportedWheel(
                    f"{wheel.filename} is not a supported wheel for this platform. It "
                    "can't be sorted."
                )
            if self._prefer_binary:
                binary_preference = 1
            build_tag = wheel.build_tag
        else:  # sdist
            pri = -(support_num)
        has_allowed_hash = int(link.is_hash_allowed(self._hashes))
        yank_value = -1 * int(link.is_yanked)  # -1 for yanked.
        return (
            has_allowed_hash,
            yank_value,
            binary_preference,
            candidate.version,
            pri,
            build_tag,
        )

    def sort_best_candidate(
        self,
        candidates: list[InstallationCandidate],
    ) -> InstallationCandidate | None:
        """
        Return the best candidate per the instance's sort order, or None if
        no candidate is acceptable.
        """
        if not candidates:
            return None
        best_candidate = max(candidates, key=self._sort_key)
        return best_candidate

    def compute_best_candidate(
        self,
        candidates: list[InstallationCandidate],
    ) -> BestCandidateResult:
        """
        Compute and return a `BestCandidateResult` instance.
        """
        applicable_candidates = self.get_applicable_candidates(candidates)

        best_candidate = self.sort_best_candidate(applicable_candidates)

        return BestCandidateResult(
            candidates,
            applicable_candidates=applicable_candidates,
            best_candidate=best_candidate,
        )


class PackageFinder:
    """This finds packages.

    This is meant to match easy_install's technique for looking for
    packages, by reading pages and looking for appropriate links.
    """

    def __init__(
        self,
        link_collector: LinkCollector,
        target_python: TargetPython,
        allow_yanked: bool,
        format_control: FormatControl | None = None,
        candidate_prefs: CandidatePreferences | None = None,
        ignore_requires_python: bool | None = None,
    ) -> None:
        """
        This constructor is primarily meant to be used by the create() class
        method and from tests.

        :param format_control: A FormatControl object, used to control
            the selection of source packages / binary packages when consulting
            the index and links.
        :param candidate_prefs: Options to use when creating a
            CandidateEvaluator object.
        """
        if candidate_prefs is None:
            candidate_prefs = CandidatePreferences()

        format_control = format_control or FormatControl(set(), set())

        self._allow_yanked = allow_yanked
        self._candidate_prefs = candidate_prefs
        self._ignore_requires_python = ignore_requires_python
        self._link_collector = link_collector
        self._target_python = target_python

        self.format_control = format_control

        # These are boring links that have already been logged somehow.
        self._logged_links: set[tuple[Link, LinkType, str]] = set()

        # Cache of the result of finding candidates
        self._all_candidates: dict[str, list[InstallationCandidate]] = {}
        self._best_candidates: dict[
            tuple[str, specifiers.BaseSpecifier | None, Hashes | None],
            BestCandidateResult,
        ] = {}

    # Don't include an allow_yanked default value to make sure each call
    # site considers whether yanked releases are allowed. This also causes
    # that decision to be made explicit in the calling code, which helps
    # people when reading the code.
    @classmethod
    def create(
        cls,
        link_collector: LinkCollector,
        selection_prefs: SelectionPreferences,
        target_python: TargetPython | None = None,
    ) -> PackageFinder:
        """Create a PackageFinder.

        :param selection_prefs: The candidate selection preferences, as a
            SelectionPreferences object.
        :param target_python: The target Python interpreter to use when
            checking compatibility. If None (the default), a TargetPython
            object will be constructed from the running Python.
        """
        if target_python is None:
            target_python = TargetPython()

        candidate_prefs = CandidatePreferences(
            prefer_binary=selection_prefs.prefer_binary,
            allow_all_prereleases=selection_prefs.allow_all_prereleases,
        )

        return cls(
            candidate_prefs=candidate_prefs,
            link_collector=link_collector,
            target_python=target_python,
            allow_yanked=selection_prefs.allow_yanked,
            format_control=selection_prefs.format_control,
            ignore_requires_python=selection_prefs.ignore_requires_python,
        )

    @property
    def target_python(self) -> TargetPython:
        return self._target_python

    @property
    def search_scope(self) -> SearchScope:
        return self._link_collector.search_scope

    @search_scope.setter
    def search_scope(self, search_scope: SearchScope) -> None:
        self._link_collector.search_scope = search_scope

    @property
    def find_links(self) -> list[str]:
        return self._link_collector.find_links

    @property
    def index_urls(self) -> list[str]:
        return self.search_scope.index_urls

    @property
    def proxy(self) -> str | None:
        return self._link_collector.session.pip_proxy

    @property
    def trusted_hosts(self) -> Iterable[str]:
        for host_port in self._link_collector.session.pip_trusted_origins:
            yield build_netloc(*host_port)

    @property
    def custom_cert(self) -> str | None:
        # session.verify is either a boolean (use default bundle/no SSL
        # verification) or a string path to a custom CA bundle to use. We only
        # care about the latter.
        verify = self._link_collector.session.verify
        return verify if isinstance(verify, str) else None

    @property
    def client_cert(self) -> str | None:
        cert = self._link_collector.session.cert
        assert not isinstance(cert, tuple), "pip only supports PEM client certs"
        return cert

    @property
    def allow_all_prereleases(self) -> bool:
        return self._candidate_prefs.allow_all_prereleases

    def set_allow_all_prereleases(self) -> None:
        self._candidate_prefs.allow_all_prereleases = True

    @property
    def prefer_binary(self) -> bool:
        return self._candidate_prefs.prefer_binary

    def set_prefer_binary(self) -> None:
        self._candidate_prefs.prefer_binary = True

    def requires_python_skipped_reasons(self) -> list[str]:
        reasons = {
            detail
            for _, result, detail in self._logged_links
            if result == LinkType.requires_python_mismatch
        }
        return sorted(reasons)

    def make_link_evaluator(self, project_name: str) -> LinkEvaluator:
        canonical_name = canonicalize_name(project_name)
        formats = self.format_control.get_allowed_formats(canonical_name)

        return LinkEvaluator(
            project_name=project_name,
            canonical_name=canonical_name,
            formats=formats,
            target_python=self._target_python,
            allow_yanked=self._allow_yanked,
            ignore_requires_python=self._ignore_requires_python,
        )

    def _sort_links(self, links: Iterable[Link]) -> list[Link]:
        """
        Returns elements of links in order, non-egg links first, egg links
        second, while eliminating duplicates
        """
        eggs, no_eggs = [], []
        seen: set[Link] = set()
        for link in links:
            if link not in seen:
                seen.add(link)
                if link.egg_fragment:
                    eggs.append(link)
                else:
                    no_eggs.append(link)
        return no_eggs + eggs

    def _log_skipped_link(self, link: Link, result: LinkType, detail: str) -> None:
        entry = (link, result, detail)
        if entry not in self._logged_links:
            # Put the link at the end so the reason is more visible and because
            # the link string is usually very long.
            logger.debug("Skipping link: %s: %s", detail, link)
            self._logged_links.add(entry)

    def get_install_candidate(
        self, link_evaluator: LinkEvaluator, link: Link
    ) -> InstallationCandidate | None:
        """
        If the link is a candidate for install, convert it to an
        InstallationCandidate and return it. Otherwise, return None.
        """
        result, detail = link_evaluator.evaluate_link(link)
        if result != LinkType.candidate:
            self._log_skipped_link(link, result, detail)
            return None

        try:
            return InstallationCandidate(
                name=link_evaluator.project_name,
                link=link,
                version=detail,
            )
        except InvalidVersion:
            return None

    def evaluate_links(
        self, link_evaluator: LinkEvaluator, links: Iterable[Link]
    ) -> list[InstallationCandidate]:
        """
        Convert links that are candidates to InstallationCandidate objects.
        """
        candidates = []
        for link in self._sort_links(links):
            candidate = self.get_install_candidate(link_evaluator, link)
            if candidate is not None:
                candidates.append(candidate)

        return candidates

    def process_project_url(
        self, project_url: Link, link_evaluator: LinkEvaluator
    ) -> list[InstallationCandidate]:
        logger.debug(
            "Fetching project page and analyzing links: %s",
            project_url,
        )
        index_response = self._link_collector.fetch_response(project_url)
        if index_response is None:
            return []

        page_links = list(parse_links(index_response))

        with indent_log():
            package_links = self.evaluate_links(
                link_evaluator,
                links=page_links,
            )

        return package_links

    def find_all_candidates(self, project_name: str) -> list[InstallationCandidate]:
        """Find all available InstallationCandidate for project_name

        This checks index_urls and find_links.
        All versions found are returned as an InstallationCandidate list.

        See LinkEvaluator.evaluate_link() for details on which files
        are accepted.
        """
        if project_name in self._all_candidates:
            return self._all_candidates[project_name]

        link_evaluator = self.make_link_evaluator(project_name)

        collected_sources = self._link_collector.collect_sources(
            project_name=project_name,
            candidates_from_page=functools.partial(
                self.process_project_url,
                link_evaluator=link_evaluator,
            ),
        )

        page_candidates_it = itertools.chain.from_iterable(
            source.page_candidates()
            for sources in collected_sources
            for source in sources
            if source is not None
        )
        page_candidates = list(page_candidates_it)

        file_links_it = itertools.chain.from_iterable(
            source.file_links()
            for sources in collected_sources
            for source in sources
            if source is not None
        )
        file_candidates = self.evaluate_links(
            link_evaluator,
            sorted(file_links_it, reverse=True),
        )

        if logger.isEnabledFor(logging.DEBUG) and file_candidates:
            paths = []
            for candidate in file_candidates:
                assert candidate.link.url  # we need to have a URL
                try:
                    paths.append(candidate.link.file_path)
                except Exception:
                    paths.append(candidate.link.url)  # it's not a local file

            logger.debug("Local files found: %s", ", ".join(paths))

        # This is an intentional priority ordering
        self._all_candidates[project_name] = file_candidates + page_candidates

        return self._all_candidates[project_name]

    def make_candidate_evaluator(
        self,
        project_name: str,
        specifier: specifiers.BaseSpecifier | None = None,
        hashes: Hashes | None = None,
    ) -> CandidateEvaluator:
        """Create a CandidateEvaluator object to use."""
        candidate_prefs = self._candidate_prefs
        return CandidateEvaluator.create(
            project_name=project_name,
            target_python=self._target_python,
            prefer_binary=candidate_prefs.prefer_binary,
            allow_all_prereleases=candidate_prefs.allow_all_prereleases,
            specifier=specifier,
            hashes=hashes,
        )

    def find_best_candidate(
        self,
        project_name: str,
        specifier: specifiers.BaseSpecifier | None = None,
        hashes: Hashes | None = None,
    ) -> BestCandidateResult:
        """Find matches for the given project and specifier.

        :param specifier: An optional object implementing `filter`
            (e.g. `packaging.specifiers.SpecifierSet`) to filter applicable
            versions.

        :return: A `BestCandidateResult` instance.
        """
        if (project_name, specifier, hashes) in self._best_candidates:
            return self._best_candidates[project_name, specifier, hashes]

        candidates = self.find_all_candidates(project_name)
        candidate_evaluator = self.make_candidate_evaluator(
            project_name=project_name,
            specifier=specifier,
            hashes=hashes,
        )
        self._best_candidates[project_name, specifier, hashes] = (
            candidate_evaluator.compute_best_candidate(candidates)
        )

        return self._best_candidates[project_name, specifier, hashes]

    def find_requirement(
        self, req: InstallRequirement, upgrade: bool
    ) -> InstallationCandidate | None:
        """Try to find a Link matching req

        Expects req, an InstallRequirement and upgrade, a boolean
        Returns a InstallationCandidate if found,
        Raises DistributionNotFound or BestVersionAlreadyInstalled otherwise
        """
        name = req.name
        assert name is not None, "find_requirement() called with no name"

        hashes = req.hashes(trust_internet=False)
        best_candidate_result = self.find_best_candidate(
            name,
            specifier=req.specifier,
            hashes=hashes,
        )
        best_candidate = best_candidate_result.best_candidate

        installed_version: _BaseVersion | None = None
        if req.satisfied_by is not None:
            installed_version = req.satisfied_by.version

        def _format_versions(cand_iter: Iterable[InstallationCandidate]) -> str:
            # This repeated parse_version and str() conversion is needed to
            # handle different vendoring sources from pip and pkg_resources.
            # If we stop using the pkg_resources provided specifier and start
            # using our own, we can drop the cast to str().
            return (
                ", ".join(
                    sorted(
                        {str(c.version) for c in cand_iter},
                        key=parse_version,
                    )
                )
                or "none"
            )

        if installed_version is None and best_candidate is None:
            logger.critical(
                "Could not find a version that satisfies the requirement %s "
                "(from versions: %s)",
                req,
                _format_versions(best_candidate_result.all_candidates),
            )

            raise DistributionNotFound(f"No matching distribution found for {req}")

        def _should_install_candidate(
            candidate: InstallationCandidate | None,
        ) -> TypeGuard[InstallationCandidate]:
            if installed_version is None:
                return True
            if best_candidate is None:
                return False
            return best_candidate.version > installed_version

        if not upgrade and installed_version is not None:
            if _should_install_candidate(best_candidate):
                logger.debug(
                    "Existing installed version (%s) satisfies requirement "
                    "(most up-to-date version is %s)",
                    installed_version,
                    best_candidate.version,
                )
            else:
                logger.debug(
                    "Existing installed version (%s) is most up-to-date and "
                    "satisfies requirement",
                    installed_version,
                )
            return None

        if _should_install_candidate(best_candidate):
            logger.debug(
                "Using version %s (newest of versions: %s)",
                best_candidate.version,
                _format_versions(best_candidate_result.applicable_candidates),
            )
            return best_candidate

        # We have an existing version, and its the best version
        logger.debug(
            "Installed version (%s) is most up-to-date (past versions: %s)",
            installed_version,
            _format_versions(best_candidate_result.applicable_candidates),
        )
        raise BestVersionAlreadyInstalled


def _find_name_version_sep(fragment: str, canonical_name: str) -> int:
    """Find the separator's index based on the package's canonical name.

    :param fragment: A <package>+<version> filename "fragment" (stem) or
        egg fragment.
    :param canonical_name: The package's canonical name.

    This function is needed since the canonicalized name does not necessarily
    have the same length as the egg info's name part. An example::

    >>> fragment = 'foo__bar-1.0'
    >>> canonical_name = 'foo-bar'
    >>> _find_name_version_sep(fragment, canonical_name)
    8
    """
    # Project name and version must be separated by one single dash. Find all
    # occurrences of dashes; if the string in front of it matches the canonical
    # name, this is the one separating the name and version parts.
    for i, c in enumerate(fragment):
        if c != "-":
            continue
        if canonicalize_name(fragment[:i]) == canonical_name:
            return i
    raise ValueError(f"{fragment} does not match {canonical_name}")


def _extract_version_from_fragment(fragment: str, canonical_name: str) -> str | None:
    """Parse the version string from a <package>+<version> filename
    "fragment" (stem) or egg fragment.

    :param fragment: The string to parse. E.g. foo-2.1
    :param canonical_name: The canonicalized name of the package this
        belongs to.
    """
    try:
        version_start = _find_name_version_sep(fragment, canonical_name) + 1
    except ValueError:
        return None
    version = fragment[version_start:]
    if not version:
        return None
    return version

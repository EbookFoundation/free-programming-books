from __future__ import annotations

import logging
import sys
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Union, cast

from pip._vendor.packaging.requirements import InvalidRequirement
from pip._vendor.packaging.utils import NormalizedName, canonicalize_name
from pip._vendor.packaging.version import Version

from pip._internal.exceptions import (
    HashError,
    InstallationSubprocessError,
    InvalidInstalledPackage,
    MetadataInconsistent,
    MetadataInvalid,
)
from pip._internal.metadata import BaseDistribution
from pip._internal.models.link import Link, links_equivalent
from pip._internal.models.wheel import Wheel
from pip._internal.req.constructors import (
    install_req_from_editable,
    install_req_from_line,
)
from pip._internal.req.req_install import InstallRequirement
from pip._internal.utils.direct_url_helpers import direct_url_from_link
from pip._internal.utils.misc import normalize_version_info

from .base import Candidate, Requirement, format_name

if TYPE_CHECKING:
    from .factory import Factory

logger = logging.getLogger(__name__)

BaseCandidate = Union[
    "AlreadyInstalledCandidate",
    "EditableCandidate",
    "LinkCandidate",
]

# Avoid conflicting with the PyPI package "Python".
REQUIRES_PYTHON_IDENTIFIER = cast(NormalizedName, "<Python from Requires-Python>")


def as_base_candidate(candidate: Candidate) -> BaseCandidate | None:
    """The runtime version of BaseCandidate."""
    base_candidate_classes = (
        AlreadyInstalledCandidate,
        EditableCandidate,
        LinkCandidate,
    )
    if isinstance(candidate, base_candidate_classes):
        return candidate
    return None


def make_install_req_from_link(
    link: Link, template: InstallRequirement
) -> InstallRequirement:
    assert not template.editable, "template is editable"
    if template.req:
        line = str(template.req)
    else:
        line = link.url
    ireq = install_req_from_line(
        line,
        user_supplied=template.user_supplied,
        comes_from=template.comes_from,
        use_pep517=template.use_pep517,
        isolated=template.isolated,
        constraint=template.constraint,
        global_options=template.global_options,
        hash_options=template.hash_options,
        config_settings=template.config_settings,
    )
    ireq.original_link = template.original_link
    ireq.link = link
    ireq.extras = template.extras
    return ireq


def make_install_req_from_editable(
    link: Link, template: InstallRequirement
) -> InstallRequirement:
    assert template.editable, "template not editable"
    ireq = install_req_from_editable(
        link.url,
        user_supplied=template.user_supplied,
        comes_from=template.comes_from,
        use_pep517=template.use_pep517,
        isolated=template.isolated,
        constraint=template.constraint,
        permit_editable_wheels=template.permit_editable_wheels,
        global_options=template.global_options,
        hash_options=template.hash_options,
        config_settings=template.config_settings,
    )
    ireq.extras = template.extras
    return ireq


def _make_install_req_from_dist(
    dist: BaseDistribution, template: InstallRequirement
) -> InstallRequirement:
    if template.req:
        line = str(template.req)
    elif template.link:
        line = f"{dist.canonical_name} @ {template.link.url}"
    else:
        line = f"{dist.canonical_name}=={dist.version}"
    ireq = install_req_from_line(
        line,
        user_supplied=template.user_supplied,
        comes_from=template.comes_from,
        use_pep517=template.use_pep517,
        isolated=template.isolated,
        constraint=template.constraint,
        global_options=template.global_options,
        hash_options=template.hash_options,
        config_settings=template.config_settings,
    )
    ireq.satisfied_by = dist
    return ireq


class _InstallRequirementBackedCandidate(Candidate):
    """A candidate backed by an ``InstallRequirement``.

    This represents a package request with the target not being already
    in the environment, and needs to be fetched and installed. The backing
    ``InstallRequirement`` is responsible for most of the leg work; this
    class exposes appropriate information to the resolver.

    :param link: The link passed to the ``InstallRequirement``. The backing
        ``InstallRequirement`` will use this link to fetch the distribution.
    :param source_link: The link this candidate "originates" from. This is
        different from ``link`` when the link is found in the wheel cache.
        ``link`` would point to the wheel cache, while this points to the
        found remote link (e.g. from pypi.org).
    """

    dist: BaseDistribution
    is_installed = False

    def __init__(
        self,
        link: Link,
        source_link: Link,
        ireq: InstallRequirement,
        factory: Factory,
        name: NormalizedName | None = None,
        version: Version | None = None,
    ) -> None:
        self._link = link
        self._source_link = source_link
        self._factory = factory
        self._ireq = ireq
        self._name = name
        self._version = version
        self.dist = self._prepare()
        self._hash: int | None = None

    def __str__(self) -> str:
        return f"{self.name} {self.version}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self._link)!r})"

    def __hash__(self) -> int:
        if self._hash is not None:
            return self._hash

        self._hash = hash((self.__class__, self._link))
        return self._hash

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, self.__class__):
            return links_equivalent(self._link, other._link)
        return False

    @property
    def source_link(self) -> Link | None:
        return self._source_link

    @property
    def project_name(self) -> NormalizedName:
        """The normalised name of the project the candidate refers to"""
        if self._name is None:
            self._name = self.dist.canonical_name
        return self._name

    @property
    def name(self) -> str:
        return self.project_name

    @property
    def version(self) -> Version:
        if self._version is None:
            self._version = self.dist.version
        return self._version

    def format_for_error(self) -> str:
        return (
            f"{self.name} {self.version} "
            f"(from {self._link.file_path if self._link.is_file else self._link})"
        )

    def _prepare_distribution(self) -> BaseDistribution:
        raise NotImplementedError("Override in subclass")

    def _check_metadata_consistency(self, dist: BaseDistribution) -> None:
        """Check for consistency of project name and version of dist."""
        if self._name is not None and self._name != dist.canonical_name:
            raise MetadataInconsistent(
                self._ireq,
                "name",
                self._name,
                dist.canonical_name,
            )
        if self._version is not None and self._version != dist.version:
            raise MetadataInconsistent(
                self._ireq,
                "version",
                str(self._version),
                str(dist.version),
            )
        # check dependencies are valid
        # TODO performance: this means we iterate the dependencies at least twice,
        # we may want to cache parsed Requires-Dist
        try:
            list(dist.iter_dependencies(list(dist.iter_provided_extras())))
        except InvalidRequirement as e:
            raise MetadataInvalid(self._ireq, str(e))

    def _prepare(self) -> BaseDistribution:
        try:
            dist = self._prepare_distribution()
        except HashError as e:
            # Provide HashError the underlying ireq that caused it. This
            # provides context for the resulting error message to show the
            # offending line to the user.
            e.req = self._ireq
            raise
        except InstallationSubprocessError as exc:
            # The output has been presented already, so don't duplicate it.
            exc.context = "See above for output."
            raise

        self._check_metadata_consistency(dist)
        return dist

    def iter_dependencies(self, with_requires: bool) -> Iterable[Requirement | None]:
        # Emit the Requires-Python requirement first to fail fast on
        # unsupported candidates and avoid pointless downloads/preparation.
        yield self._factory.make_requires_python_requirement(self.dist.requires_python)
        requires = self.dist.iter_dependencies() if with_requires else ()
        for r in requires:
            yield from self._factory.make_requirements_from_spec(str(r), self._ireq)

    def get_install_requirement(self) -> InstallRequirement | None:
        return self._ireq


class LinkCandidate(_InstallRequirementBackedCandidate):
    is_editable = False

    def __init__(
        self,
        link: Link,
        template: InstallRequirement,
        factory: Factory,
        name: NormalizedName | None = None,
        version: Version | None = None,
    ) -> None:
        source_link = link
        cache_entry = factory.get_wheel_cache_entry(source_link, name)
        if cache_entry is not None:
            logger.debug("Using cached wheel link: %s", cache_entry.link)
            link = cache_entry.link
        ireq = make_install_req_from_link(link, template)
        assert ireq.link == link
        if ireq.link.is_wheel and not ireq.link.is_file:
            wheel = Wheel(ireq.link.filename)
            wheel_name = canonicalize_name(wheel.name)
            assert name == wheel_name, f"{name!r} != {wheel_name!r} for wheel"
            # Version may not be present for PEP 508 direct URLs
            if version is not None:
                wheel_version = Version(wheel.version)
                assert (
                    version == wheel_version
                ), f"{version!r} != {wheel_version!r} for wheel {name}"

        if cache_entry is not None:
            assert ireq.link.is_wheel
            assert ireq.link.is_file
            if cache_entry.persistent and template.link is template.original_link:
                ireq.cached_wheel_source_link = source_link
            if cache_entry.origin is not None:
                ireq.download_info = cache_entry.origin
            else:
                # Legacy cache entry that does not have origin.json.
                # download_info may miss the archive_info.hashes field.
                ireq.download_info = direct_url_from_link(
                    source_link, link_is_in_wheel_cache=cache_entry.persistent
                )

        super().__init__(
            link=link,
            source_link=source_link,
            ireq=ireq,
            factory=factory,
            name=name,
            version=version,
        )

    def _prepare_distribution(self) -> BaseDistribution:
        preparer = self._factory.preparer
        return preparer.prepare_linked_requirement(self._ireq, parallel_builds=True)


class EditableCandidate(_InstallRequirementBackedCandidate):
    is_editable = True

    def __init__(
        self,
        link: Link,
        template: InstallRequirement,
        factory: Factory,
        name: NormalizedName | None = None,
        version: Version | None = None,
    ) -> None:
        super().__init__(
            link=link,
            source_link=link,
            ireq=make_install_req_from_editable(link, template),
            factory=factory,
            name=name,
            version=version,
        )

    def _prepare_distribution(self) -> BaseDistribution:
        return self._factory.preparer.prepare_editable_requirement(self._ireq)


class AlreadyInstalledCandidate(Candidate):
    is_installed = True
    source_link = None

    def __init__(
        self,
        dist: BaseDistribution,
        template: InstallRequirement,
        factory: Factory,
    ) -> None:
        self.dist = dist
        self._ireq = _make_install_req_from_dist(dist, template)
        self._factory = factory
        self._version = None

        # This is just logging some messages, so we can do it eagerly.
        # The returned dist would be exactly the same as self.dist because we
        # set satisfied_by in _make_install_req_from_dist.
        # TODO: Supply reason based on force_reinstall and upgrade_strategy.
        skip_reason = "already satisfied"
        factory.preparer.prepare_installed_requirement(self._ireq, skip_reason)

    def __str__(self) -> str:
        return str(self.dist)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.dist!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AlreadyInstalledCandidate):
            return NotImplemented
        return self.name == other.name and self.version == other.version

    def __hash__(self) -> int:
        return hash((self.name, self.version))

    @property
    def project_name(self) -> NormalizedName:
        return self.dist.canonical_name

    @property
    def name(self) -> str:
        return self.project_name

    @property
    def version(self) -> Version:
        if self._version is None:
            self._version = self.dist.version
        return self._version

    @property
    def is_editable(self) -> bool:
        return self.dist.editable

    def format_for_error(self) -> str:
        return f"{self.name} {self.version} (Installed)"

    def iter_dependencies(self, with_requires: bool) -> Iterable[Requirement | None]:
        if not with_requires:
            return

        try:
            for r in self.dist.iter_dependencies():
                yield from self._factory.make_requirements_from_spec(str(r), self._ireq)
        except InvalidRequirement as exc:
            raise InvalidInstalledPackage(dist=self.dist, invalid_exc=exc) from None

    def get_install_requirement(self) -> InstallRequirement | None:
        return None


class ExtrasCandidate(Candidate):
    """A candidate that has 'extras', indicating additional dependencies.

    Requirements can be for a project with dependencies, something like
    foo[extra].  The extras don't affect the project/version being installed
    directly, but indicate that we need additional dependencies. We model that
    by having an artificial ExtrasCandidate that wraps the "base" candidate.

    The ExtrasCandidate differs from the base in the following ways:

    1. It has a unique name, of the form foo[extra]. This causes the resolver
       to treat it as a separate node in the dependency graph.
    2. When we're getting the candidate's dependencies,
       a) We specify that we want the extra dependencies as well.
       b) We add a dependency on the base candidate.
          See below for why this is needed.
    3. We return None for the underlying InstallRequirement, as the base
       candidate will provide it, and we don't want to end up with duplicates.

    The dependency on the base candidate is needed so that the resolver can't
    decide that it should recommend foo[extra1] version 1.0 and foo[extra2]
    version 2.0. Having those candidates depend on foo=1.0 and foo=2.0
    respectively forces the resolver to recognise that this is a conflict.
    """

    def __init__(
        self,
        base: BaseCandidate,
        extras: frozenset[str],
        *,
        comes_from: InstallRequirement | None = None,
    ) -> None:
        """
        :param comes_from: the InstallRequirement that led to this candidate if it
            differs from the base's InstallRequirement. This will often be the
            case in the sense that this candidate's requirement has the extras
            while the base's does not. Unlike the InstallRequirement backed
            candidates, this requirement is used solely for reporting purposes,
            it does not do any leg work.
        """
        self.base = base
        self.extras = frozenset(canonicalize_name(e) for e in extras)
        self._comes_from = comes_from if comes_from is not None else self.base._ireq

    def __str__(self) -> str:
        name, rest = str(self.base).split(" ", 1)
        return "{}[{}] {}".format(name, ",".join(self.extras), rest)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(base={self.base!r}, extras={self.extras!r})"

    def __hash__(self) -> int:
        return hash((self.base, self.extras))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, self.__class__):
            return self.base == other.base and self.extras == other.extras
        return False

    @property
    def project_name(self) -> NormalizedName:
        return self.base.project_name

    @property
    def name(self) -> str:
        """The normalised name of the project the candidate refers to"""
        return format_name(self.base.project_name, self.extras)

    @property
    def version(self) -> Version:
        return self.base.version

    def format_for_error(self) -> str:
        return "{} [{}]".format(
            self.base.format_for_error(), ", ".join(sorted(self.extras))
        )

    @property
    def is_installed(self) -> bool:
        return self.base.is_installed

    @property
    def is_editable(self) -> bool:
        return self.base.is_editable

    @property
    def source_link(self) -> Link | None:
        return self.base.source_link

    def iter_dependencies(self, with_requires: bool) -> Iterable[Requirement | None]:
        factory = self.base._factory

        # Add a dependency on the exact base
        # (See note 2b in the class docstring)
        yield factory.make_requirement_from_candidate(self.base)
        if not with_requires:
            return

        # The user may have specified extras that the candidate doesn't
        # support. We ignore any unsupported extras here.
        valid_extras = self.extras.intersection(self.base.dist.iter_provided_extras())
        invalid_extras = self.extras.difference(self.base.dist.iter_provided_extras())
        for extra in sorted(invalid_extras):
            logger.warning(
                "%s %s does not provide the extra '%s'",
                self.base.name,
                self.version,
                extra,
            )

        for r in self.base.dist.iter_dependencies(valid_extras):
            yield from factory.make_requirements_from_spec(
                str(r),
                self._comes_from,
                valid_extras,
            )

    def get_install_requirement(self) -> InstallRequirement | None:
        # We don't return anything here, because we always
        # depend on the base candidate, and we'll get the
        # install requirement from that.
        return None


class RequiresPythonCandidate(Candidate):
    is_installed = False
    source_link = None

    def __init__(self, py_version_info: tuple[int, ...] | None) -> None:
        if py_version_info is not None:
            version_info = normalize_version_info(py_version_info)
        else:
            version_info = sys.version_info[:3]
        self._version = Version(".".join(str(c) for c in version_info))

    # We don't need to implement __eq__() and __ne__() since there is always
    # only one RequiresPythonCandidate in a resolution, i.e. the host Python.
    # The built-in object.__eq__() and object.__ne__() do exactly what we want.

    def __str__(self) -> str:
        return f"Python {self._version}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._version!r})"

    @property
    def project_name(self) -> NormalizedName:
        return REQUIRES_PYTHON_IDENTIFIER

    @property
    def name(self) -> str:
        return REQUIRES_PYTHON_IDENTIFIER

    @property
    def version(self) -> Version:
        return self._version

    def format_for_error(self) -> str:
        return f"Python {self.version}"

    def iter_dependencies(self, with_requires: bool) -> Iterable[Requirement | None]:
        return ()

    def get_install_requirement(self) -> InstallRequirement | None:
        return None

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING

from pip._internal.build_env import BuildEnvironment
from pip._internal.distributions.base import AbstractDistribution
from pip._internal.exceptions import InstallationError
from pip._internal.metadata import BaseDistribution
from pip._internal.utils.subprocess import runner_with_spinner_message

if TYPE_CHECKING:
    from pip._internal.build_env import BuildEnvironmentInstaller

logger = logging.getLogger(__name__)


class SourceDistribution(AbstractDistribution):
    """Represents a source distribution.

    The preparation step for these needs metadata for the packages to be
    generated, either using PEP 517 or using the legacy `setup.py egg_info`.
    """

    @property
    def build_tracker_id(self) -> str | None:
        """Identify this requirement uniquely by its link."""
        assert self.req.link
        return self.req.link.url_without_fragment

    def get_metadata_distribution(self) -> BaseDistribution:
        return self.req.get_dist()

    def prepare_distribution_metadata(
        self,
        build_env_installer: BuildEnvironmentInstaller,
        build_isolation: bool,
        check_build_deps: bool,
    ) -> None:
        # Load pyproject.toml, to determine whether PEP 517 is to be used
        self.req.load_pyproject_toml()

        # Set up the build isolation, if this requirement should be isolated
        should_isolate = self.req.use_pep517 and build_isolation
        if should_isolate:
            # Setup an isolated environment and install the build backend static
            # requirements in it.
            self._prepare_build_backend(build_env_installer)
            # Check that if the requirement is editable, it either supports PEP 660 or
            # has a setup.py or a setup.cfg. This cannot be done earlier because we need
            # to setup the build backend to verify it supports build_editable, nor can
            # it be done later, because we want to avoid installing build requirements
            # needlessly. Doing it here also works around setuptools generating
            # UNKNOWN.egg-info when running get_requires_for_build_wheel on a directory
            # without setup.py nor setup.cfg.
            self.req.isolated_editable_sanity_check()
            # Install the dynamic build requirements.
            self._install_build_reqs(build_env_installer)
        # Check if the current environment provides build dependencies
        should_check_deps = self.req.use_pep517 and check_build_deps
        if should_check_deps:
            pyproject_requires = self.req.pyproject_requires
            assert pyproject_requires is not None
            conflicting, missing = self.req.build_env.check_requirements(
                pyproject_requires
            )
            if conflicting:
                self._raise_conflicts("the backend dependencies", conflicting)
            if missing:
                self._raise_missing_reqs(missing)
        self.req.prepare_metadata()

    def _prepare_build_backend(
        self, build_env_installer: BuildEnvironmentInstaller
    ) -> None:
        # Isolate in a BuildEnvironment and install the build-time
        # requirements.
        pyproject_requires = self.req.pyproject_requires
        assert pyproject_requires is not None

        self.req.build_env = BuildEnvironment(build_env_installer)
        self.req.build_env.install_requirements(
            pyproject_requires, "overlay", kind="build dependencies", for_req=self.req
        )
        conflicting, missing = self.req.build_env.check_requirements(
            self.req.requirements_to_check
        )
        if conflicting:
            self._raise_conflicts("PEP 517/518 supported requirements", conflicting)
        if missing:
            logger.warning(
                "Missing build requirements in pyproject.toml for %s.",
                self.req,
            )
            logger.warning(
                "The project does not specify a build backend, and "
                "pip cannot fall back to setuptools without %s.",
                " and ".join(map(repr, sorted(missing))),
            )

    def _get_build_requires_wheel(self) -> Iterable[str]:
        with self.req.build_env:
            runner = runner_with_spinner_message("Getting requirements to build wheel")
            backend = self.req.pep517_backend
            assert backend is not None
            with backend.subprocess_runner(runner):
                return backend.get_requires_for_build_wheel()

    def _get_build_requires_editable(self) -> Iterable[str]:
        with self.req.build_env:
            runner = runner_with_spinner_message(
                "Getting requirements to build editable"
            )
            backend = self.req.pep517_backend
            assert backend is not None
            with backend.subprocess_runner(runner):
                return backend.get_requires_for_build_editable()

    def _install_build_reqs(
        self, build_env_installer: BuildEnvironmentInstaller
    ) -> None:
        # Install any extra build dependencies that the backend requests.
        # This must be done in a second pass, as the pyproject.toml
        # dependencies must be installed before we can call the backend.
        if (
            self.req.editable
            and self.req.permit_editable_wheels
            and self.req.supports_pyproject_editable
        ):
            build_reqs = self._get_build_requires_editable()
        else:
            build_reqs = self._get_build_requires_wheel()
        conflicting, missing = self.req.build_env.check_requirements(build_reqs)
        if conflicting:
            self._raise_conflicts("the backend dependencies", conflicting)
        self.req.build_env.install_requirements(
            missing, "normal", kind="backend dependencies", for_req=self.req
        )

    def _raise_conflicts(
        self, conflicting_with: str, conflicting_reqs: set[tuple[str, str]]
    ) -> None:
        format_string = (
            "Some build dependencies for {requirement} "
            "conflict with {conflicting_with}: {description}."
        )
        error_message = format_string.format(
            requirement=self.req,
            conflicting_with=conflicting_with,
            description=", ".join(
                f"{installed} is incompatible with {wanted}"
                for installed, wanted in sorted(conflicting_reqs)
            ),
        )
        raise InstallationError(error_message)

    def _raise_missing_reqs(self, missing: set[str]) -> None:
        format_string = (
            "Some build dependencies for {requirement} are missing: {missing}."
        )
        error_message = format_string.format(
            requirement=self.req, missing=", ".join(map(repr, sorted(missing)))
        )
        raise InstallationError(error_message)

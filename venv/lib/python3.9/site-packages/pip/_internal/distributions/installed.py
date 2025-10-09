from __future__ import annotations

from typing import TYPE_CHECKING

from pip._internal.distributions.base import AbstractDistribution
from pip._internal.metadata import BaseDistribution

if TYPE_CHECKING:
    from pip._internal.build_env import BuildEnvironmentInstaller


class InstalledDistribution(AbstractDistribution):
    """Represents an installed package.

    This does not need any preparation as the required information has already
    been computed.
    """

    @property
    def build_tracker_id(self) -> str | None:
        return None

    def get_metadata_distribution(self) -> BaseDistribution:
        assert self.req.satisfied_by is not None, "not actually installed"
        return self.req.satisfied_by

    def prepare_distribution_metadata(
        self,
        build_env_installer: BuildEnvironmentInstaller,
        build_isolation: bool,
        check_build_deps: bool,
    ) -> None:
        pass

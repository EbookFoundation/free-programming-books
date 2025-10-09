from __future__ import annotations

import abc
from typing import TYPE_CHECKING

from pip._internal.metadata.base import BaseDistribution
from pip._internal.req import InstallRequirement

if TYPE_CHECKING:
    from pip._internal.build_env import BuildEnvironmentInstaller


class AbstractDistribution(metaclass=abc.ABCMeta):
    """A base class for handling installable artifacts.

    The requirements for anything installable are as follows:

     - we must be able to determine the requirement name
       (or we can't correctly handle the non-upgrade case).

     - for packages with setup requirements, we must also be able
       to determine their requirements without installing additional
       packages (for the same reason as run-time dependencies)

     - we must be able to create a Distribution object exposing the
       above metadata.

     - if we need to do work in the build tracker, we must be able to generate a unique
       string to identify the requirement in the build tracker.
    """

    def __init__(self, req: InstallRequirement) -> None:
        super().__init__()
        self.req = req

    @abc.abstractproperty
    def build_tracker_id(self) -> str | None:
        """A string that uniquely identifies this requirement to the build tracker.

        If None, then this dist has no work to do in the build tracker, and
        ``.prepare_distribution_metadata()`` will not be called."""
        raise NotImplementedError()

    @abc.abstractmethod
    def get_metadata_distribution(self) -> BaseDistribution:
        raise NotImplementedError()

    @abc.abstractmethod
    def prepare_distribution_metadata(
        self,
        build_env_installer: BuildEnvironmentInstaller,
        build_isolation: bool,
        check_build_deps: bool,
    ) -> None:
        raise NotImplementedError()

from typing import Callable, Optional

from pip._internal.req.req_install import InstallRequirement
from pip._internal.req.req_set import RequirementSet

InstallRequirementProvider = Callable[
    [str, Optional[InstallRequirement]], InstallRequirement
]


class BaseResolver:
    def resolve(
        self, root_reqs: list[InstallRequirement], check_supported_wheels: bool
    ) -> RequirementSet:
        raise NotImplementedError()

    def get_installation_order(
        self, req_set: RequirementSet
    ) -> list[InstallRequirement]:
        raise NotImplementedError()

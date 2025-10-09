from collections.abc import Sequence
from typing import Any

from pip._vendor.packaging.markers import default_environment

from pip import __version__
from pip._internal.req.req_install import InstallRequirement


class InstallationReport:
    def __init__(self, install_requirements: Sequence[InstallRequirement]):
        self._install_requirements = install_requirements

    @classmethod
    def _install_req_to_dict(cls, ireq: InstallRequirement) -> dict[str, Any]:
        assert ireq.download_info, f"No download_info for {ireq}"
        res = {
            # PEP 610 json for the download URL. download_info.archive_info.hashes may
            # be absent when the requirement was installed from the wheel cache
            # and the cache entry was populated by an older pip version that did not
            # record origin.json.
            "download_info": ireq.download_info.to_dict(),
            # is_direct is true if the requirement was a direct URL reference (which
            # includes editable requirements), and false if the requirement was
            # downloaded from a PEP 503 index or --find-links.
            "is_direct": ireq.is_direct,
            # is_yanked is true if the requirement was yanked from the index, but
            # was still selected by pip to conform to PEP 592.
            "is_yanked": ireq.link.is_yanked if ireq.link else False,
            # requested is true if the requirement was specified by the user (aka
            # top level requirement), and false if it was installed as a dependency of a
            # requirement. https://peps.python.org/pep-0376/#requested
            "requested": ireq.user_supplied,
            # PEP 566 json encoding for metadata
            # https://www.python.org/dev/peps/pep-0566/#json-compatible-metadata
            "metadata": ireq.get_dist().metadata_dict,
        }
        if ireq.user_supplied and ireq.extras:
            # For top level requirements, the list of requested extras, if any.
            res["requested_extras"] = sorted(ireq.extras)
        return res

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": "1",
            "pip_version": __version__,
            "install": [
                self._install_req_to_dict(ireq) for ireq in self._install_requirements
            ],
            # https://peps.python.org/pep-0508/#environment-markers
            # TODO: currently, the resolver uses the default environment to evaluate
            # environment markers, so that is what we report here. In the future, it
            # should also take into account options such as --python-version or
            # --platform, perhaps under the form of an environment_override field?
            # https://github.com/pypa/pip/issues/11198
            "environment": default_environment(),
        }

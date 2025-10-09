import logging
from optparse import Values
from typing import Any

from pip._vendor.packaging.markers import default_environment
from pip._vendor.rich import print_json

from pip import __version__
from pip._internal.cli import cmdoptions
from pip._internal.cli.base_command import Command
from pip._internal.cli.status_codes import SUCCESS
from pip._internal.metadata import BaseDistribution, get_environment
from pip._internal.utils.compat import stdlib_pkgs
from pip._internal.utils.urls import path_to_url

logger = logging.getLogger(__name__)


class InspectCommand(Command):
    """
    Inspect the content of a Python environment and produce a report in JSON format.
    """

    ignore_require_venv = True
    usage = """
      %prog [options]"""

    def add_options(self) -> None:
        self.cmd_opts.add_option(
            "--local",
            action="store_true",
            default=False,
            help=(
                "If in a virtualenv that has global access, do not list "
                "globally-installed packages."
            ),
        )
        self.cmd_opts.add_option(
            "--user",
            dest="user",
            action="store_true",
            default=False,
            help="Only output packages installed in user-site.",
        )
        self.cmd_opts.add_option(cmdoptions.list_path())
        self.parser.insert_option_group(0, self.cmd_opts)

    def run(self, options: Values, args: list[str]) -> int:
        cmdoptions.check_list_path_option(options)
        dists = get_environment(options.path).iter_installed_distributions(
            local_only=options.local,
            user_only=options.user,
            skip=set(stdlib_pkgs),
        )
        output = {
            "version": "1",
            "pip_version": __version__,
            "installed": [self._dist_to_dict(dist) for dist in dists],
            "environment": default_environment(),
            # TODO tags? scheme?
        }
        print_json(data=output)
        return SUCCESS

    def _dist_to_dict(self, dist: BaseDistribution) -> dict[str, Any]:
        res: dict[str, Any] = {
            "metadata": dist.metadata_dict,
            "metadata_location": dist.info_location,
        }
        # direct_url. Note that we don't have download_info (as in the installation
        # report) since it is not recorded in installed metadata.
        direct_url = dist.direct_url
        if direct_url is not None:
            res["direct_url"] = direct_url.to_dict()
        else:
            # Emulate direct_url for legacy editable installs.
            editable_project_location = dist.editable_project_location
            if editable_project_location is not None:
                res["direct_url"] = {
                    "url": path_to_url(editable_project_location),
                    "dir_info": {
                        "editable": True,
                    },
                }
        # installer
        installer = dist.installer
        if dist.installer:
            res["installer"] = installer
        # requested
        if dist.installed_with_dist_info:
            res["requested"] = dist.requested
        return res

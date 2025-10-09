from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from optparse import Values
from typing import Any, Callable

from pip._vendor.packaging.version import Version

from pip._internal.cli import cmdoptions
from pip._internal.cli.req_command import IndexGroupCommand
from pip._internal.cli.status_codes import ERROR, SUCCESS
from pip._internal.commands.search import (
    get_installed_distribution,
    print_dist_installation_info,
)
from pip._internal.exceptions import CommandError, DistributionNotFound, PipError
from pip._internal.index.collector import LinkCollector
from pip._internal.index.package_finder import PackageFinder
from pip._internal.models.selection_prefs import SelectionPreferences
from pip._internal.models.target_python import TargetPython
from pip._internal.network.session import PipSession
from pip._internal.utils.misc import write_output

logger = logging.getLogger(__name__)


class IndexCommand(IndexGroupCommand):
    """
    Inspect information available from package indexes.
    """

    ignore_require_venv = True
    usage = """
        %prog versions <package>
    """

    def add_options(self) -> None:
        cmdoptions.add_target_python_options(self.cmd_opts)

        self.cmd_opts.add_option(cmdoptions.ignore_requires_python())
        self.cmd_opts.add_option(cmdoptions.pre())
        self.cmd_opts.add_option(cmdoptions.json())
        self.cmd_opts.add_option(cmdoptions.no_binary())
        self.cmd_opts.add_option(cmdoptions.only_binary())

        index_opts = cmdoptions.make_option_group(
            cmdoptions.index_group,
            self.parser,
        )

        self.parser.insert_option_group(0, index_opts)
        self.parser.insert_option_group(0, self.cmd_opts)

    def handler_map(self) -> dict[str, Callable[[Values, list[str]], None]]:
        return {
            "versions": self.get_available_package_versions,
        }

    def run(self, options: Values, args: list[str]) -> int:
        handler_map = self.handler_map()

        # Determine action
        if not args or args[0] not in handler_map:
            logger.error(
                "Need an action (%s) to perform.",
                ", ".join(sorted(handler_map)),
            )
            return ERROR

        action = args[0]

        # Error handling happens here, not in the action-handlers.
        try:
            handler_map[action](options, args[1:])
        except PipError as e:
            logger.error(e.args[0])
            return ERROR

        return SUCCESS

    def _build_package_finder(
        self,
        options: Values,
        session: PipSession,
        target_python: TargetPython | None = None,
        ignore_requires_python: bool | None = None,
    ) -> PackageFinder:
        """
        Create a package finder appropriate to the index command.
        """
        link_collector = LinkCollector.create(session, options=options)

        # Pass allow_yanked=False to ignore yanked versions.
        selection_prefs = SelectionPreferences(
            allow_yanked=False,
            allow_all_prereleases=options.pre,
            ignore_requires_python=ignore_requires_python,
        )

        return PackageFinder.create(
            link_collector=link_collector,
            selection_prefs=selection_prefs,
            target_python=target_python,
        )

    def get_available_package_versions(self, options: Values, args: list[Any]) -> None:
        if len(args) != 1:
            raise CommandError("You need to specify exactly one argument")

        target_python = cmdoptions.make_target_python(options)
        query = args[0]

        with self._build_session(options) as session:
            finder = self._build_package_finder(
                options=options,
                session=session,
                target_python=target_python,
                ignore_requires_python=options.ignore_requires_python,
            )

            versions: Iterable[Version] = (
                candidate.version for candidate in finder.find_all_candidates(query)
            )

            if not options.pre:
                # Remove prereleases
                versions = (
                    version for version in versions if not version.is_prerelease
                )
            versions = set(versions)

            if not versions:
                raise DistributionNotFound(
                    f"No matching distribution found for {query}"
                )

            formatted_versions = [str(ver) for ver in sorted(versions, reverse=True)]
            latest = formatted_versions[0]

        dist = get_installed_distribution(query)

        if options.json:
            structured_output = {
                "name": query,
                "versions": formatted_versions,
                "latest": latest,
            }

            if dist is not None:
                structured_output["installed_version"] = str(dist.version)

            write_output(json.dumps(structured_output))

        else:
            write_output(f"{query} ({latest})")
            write_output("Available versions: {}".format(", ".join(formatted_versions)))
            print_dist_installation_info(latest, dist)

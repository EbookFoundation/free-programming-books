import logging
from optparse import Values

from pip._internal.cli.base_command import Command
from pip._internal.cli.status_codes import ERROR, SUCCESS
from pip._internal.metadata import get_default_environment
from pip._internal.operations.check import (
    check_package_set,
    check_unsupported,
    create_package_set_from_installed,
)
from pip._internal.utils.compatibility_tags import get_supported
from pip._internal.utils.misc import write_output

logger = logging.getLogger(__name__)


class CheckCommand(Command):
    """Verify installed packages have compatible dependencies."""

    ignore_require_venv = True
    usage = """
      %prog [options]"""

    def run(self, options: Values, args: list[str]) -> int:
        package_set, parsing_probs = create_package_set_from_installed()
        missing, conflicting = check_package_set(package_set)
        unsupported = list(
            check_unsupported(
                get_default_environment().iter_installed_distributions(),
                get_supported(),
            )
        )

        for project_name in missing:
            version = package_set[project_name].version
            for dependency in missing[project_name]:
                write_output(
                    "%s %s requires %s, which is not installed.",
                    project_name,
                    version,
                    dependency[0],
                )

        for project_name in conflicting:
            version = package_set[project_name].version
            for dep_name, dep_version, req in conflicting[project_name]:
                write_output(
                    "%s %s has requirement %s, but you have %s %s.",
                    project_name,
                    version,
                    req,
                    dep_name,
                    dep_version,
                )
        for package in unsupported:
            write_output(
                "%s %s is not supported on this platform",
                package.raw_name,
                package.version,
            )
        if missing or conflicting or parsing_probs or unsupported:
            return ERROR
        else:
            write_output("No broken requirements found.")
            return SUCCESS

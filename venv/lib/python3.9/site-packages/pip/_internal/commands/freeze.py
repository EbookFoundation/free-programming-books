import sys
from optparse import Values

from pip._internal.cli import cmdoptions
from pip._internal.cli.base_command import Command
from pip._internal.cli.status_codes import SUCCESS
from pip._internal.operations.freeze import freeze
from pip._internal.utils.compat import stdlib_pkgs


def _should_suppress_build_backends() -> bool:
    return sys.version_info < (3, 12)


def _dev_pkgs() -> set[str]:
    pkgs = {"pip"}

    if _should_suppress_build_backends():
        pkgs |= {"setuptools", "distribute", "wheel"}

    return pkgs


class FreezeCommand(Command):
    """
    Output installed packages in requirements format.

    packages are listed in a case-insensitive sorted order.
    """

    ignore_require_venv = True
    usage = """
      %prog [options]"""

    def add_options(self) -> None:
        self.cmd_opts.add_option(
            "-r",
            "--requirement",
            dest="requirements",
            action="append",
            default=[],
            metavar="file",
            help=(
                "Use the order in the given requirements file and its "
                "comments when generating output. This option can be "
                "used multiple times."
            ),
        )
        self.cmd_opts.add_option(
            "-l",
            "--local",
            dest="local",
            action="store_true",
            default=False,
            help=(
                "If in a virtualenv that has global access, do not output "
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
        self.cmd_opts.add_option(
            "--all",
            dest="freeze_all",
            action="store_true",
            help=(
                "Do not skip these packages in the output:"
                " {}".format(", ".join(_dev_pkgs()))
            ),
        )
        self.cmd_opts.add_option(
            "--exclude-editable",
            dest="exclude_editable",
            action="store_true",
            help="Exclude editable package from output.",
        )
        self.cmd_opts.add_option(cmdoptions.list_exclude())

        self.parser.insert_option_group(0, self.cmd_opts)

    def run(self, options: Values, args: list[str]) -> int:
        skip = set(stdlib_pkgs)
        if not options.freeze_all:
            skip.update(_dev_pkgs())

        if options.excludes:
            skip.update(options.excludes)

        cmdoptions.check_list_path_option(options)

        for line in freeze(
            requirement=options.requirements,
            local_only=options.local,
            user_only=options.user,
            paths=options.path,
            isolated=options.isolated_mode,
            skip=skip,
            exclude_editable=options.exclude_editable,
        ):
            sys.stdout.write(line + "\n")
        return SUCCESS

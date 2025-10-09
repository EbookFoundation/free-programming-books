"""Base Command class, and related routines"""

from __future__ import annotations

import logging
import logging.config
import optparse
import os
import sys
import traceback
from optparse import Values
from typing import Callable

from pip._vendor.rich import reconfigure
from pip._vendor.rich import traceback as rich_traceback

from pip._internal.cli import cmdoptions
from pip._internal.cli.command_context import CommandContextMixIn
from pip._internal.cli.parser import ConfigOptionParser, UpdatingDefaultsHelpFormatter
from pip._internal.cli.status_codes import (
    ERROR,
    PREVIOUS_BUILD_DIR_ERROR,
    UNKNOWN_ERROR,
    VIRTUALENV_NOT_FOUND,
)
from pip._internal.exceptions import (
    BadCommand,
    CommandError,
    DiagnosticPipError,
    InstallationError,
    NetworkConnectionError,
    PreviousBuildDirError,
)
from pip._internal.utils.filesystem import check_path_owner
from pip._internal.utils.logging import BrokenStdoutLoggingError, setup_logging
from pip._internal.utils.misc import get_prog, normalize_path
from pip._internal.utils.temp_dir import TempDirectoryTypeRegistry as TempDirRegistry
from pip._internal.utils.temp_dir import global_tempdir_manager, tempdir_registry
from pip._internal.utils.virtualenv import running_under_virtualenv

__all__ = ["Command"]

logger = logging.getLogger(__name__)


class Command(CommandContextMixIn):
    usage: str = ""
    ignore_require_venv: bool = False

    def __init__(self, name: str, summary: str, isolated: bool = False) -> None:
        super().__init__()

        self.name = name
        self.summary = summary
        self.parser = ConfigOptionParser(
            usage=self.usage,
            prog=f"{get_prog()} {name}",
            formatter=UpdatingDefaultsHelpFormatter(),
            add_help_option=False,
            name=name,
            description=self.__doc__,
            isolated=isolated,
        )

        self.tempdir_registry: TempDirRegistry | None = None

        # Commands should add options to this option group
        optgroup_name = f"{self.name.capitalize()} Options"
        self.cmd_opts = optparse.OptionGroup(self.parser, optgroup_name)

        # Add the general options
        gen_opts = cmdoptions.make_option_group(
            cmdoptions.general_group,
            self.parser,
        )
        self.parser.add_option_group(gen_opts)

        self.add_options()

    def add_options(self) -> None:
        pass

    def handle_pip_version_check(self, options: Values) -> None:
        """
        This is a no-op so that commands by default do not do the pip version
        check.
        """
        # Make sure we do the pip version check if the index_group options
        # are present.
        assert not hasattr(options, "no_index")

    def run(self, options: Values, args: list[str]) -> int:
        raise NotImplementedError

    def _run_wrapper(self, level_number: int, options: Values, args: list[str]) -> int:
        def _inner_run() -> int:
            try:
                return self.run(options, args)
            finally:
                self.handle_pip_version_check(options)

        if options.debug_mode:
            rich_traceback.install(show_locals=True)
            return _inner_run()

        try:
            status = _inner_run()
            assert isinstance(status, int)
            return status
        except DiagnosticPipError as exc:
            logger.error("%s", exc, extra={"rich": True})
            logger.debug("Exception information:", exc_info=True)

            return ERROR
        except PreviousBuildDirError as exc:
            logger.critical(str(exc))
            logger.debug("Exception information:", exc_info=True)

            return PREVIOUS_BUILD_DIR_ERROR
        except (
            InstallationError,
            BadCommand,
            NetworkConnectionError,
        ) as exc:
            logger.critical(str(exc))
            logger.debug("Exception information:", exc_info=True)

            return ERROR
        except CommandError as exc:
            logger.critical("%s", exc)
            logger.debug("Exception information:", exc_info=True)

            return ERROR
        except BrokenStdoutLoggingError:
            # Bypass our logger and write any remaining messages to
            # stderr because stdout no longer works.
            print("ERROR: Pipe to stdout was broken", file=sys.stderr)
            if level_number <= logging.DEBUG:
                traceback.print_exc(file=sys.stderr)

            return ERROR
        except KeyboardInterrupt:
            logger.critical("Operation cancelled by user")
            logger.debug("Exception information:", exc_info=True)

            return ERROR
        except BaseException:
            logger.critical("Exception:", exc_info=True)

            return UNKNOWN_ERROR

    def parse_args(self, args: list[str]) -> tuple[Values, list[str]]:
        # factored out for testability
        return self.parser.parse_args(args)

    def main(self, args: list[str]) -> int:
        try:
            with self.main_context():
                return self._main(args)
        finally:
            logging.shutdown()

    def _main(self, args: list[str]) -> int:
        # We must initialize this before the tempdir manager, otherwise the
        # configuration would not be accessible by the time we clean up the
        # tempdir manager.
        self.tempdir_registry = self.enter_context(tempdir_registry())
        # Intentionally set as early as possible so globally-managed temporary
        # directories are available to the rest of the code.
        self.enter_context(global_tempdir_manager())

        options, args = self.parse_args(args)

        # Set verbosity so that it can be used elsewhere.
        self.verbosity = options.verbose - options.quiet
        if options.debug_mode:
            self.verbosity = 2

        if hasattr(options, "progress_bar") and options.progress_bar == "auto":
            options.progress_bar = "on" if self.verbosity >= 0 else "off"

        reconfigure(no_color=options.no_color)
        level_number = setup_logging(
            verbosity=self.verbosity,
            no_color=options.no_color,
            user_log_file=options.log,
        )

        always_enabled_features = set(options.features_enabled) & set(
            cmdoptions.ALWAYS_ENABLED_FEATURES
        )
        if always_enabled_features:
            logger.warning(
                "The following features are always enabled: %s. ",
                ", ".join(sorted(always_enabled_features)),
            )

        # Make sure that the --python argument isn't specified after the
        # subcommand. We can tell, because if --python was specified,
        # we should only reach this point if we're running in the created
        # subprocess, which has the _PIP_RUNNING_IN_SUBPROCESS environment
        # variable set.
        if options.python and "_PIP_RUNNING_IN_SUBPROCESS" not in os.environ:
            logger.critical(
                "The --python option must be placed before the pip subcommand name"
            )
            sys.exit(ERROR)

        # TODO: Try to get these passing down from the command?
        #       without resorting to os.environ to hold these.
        #       This also affects isolated builds and it should.

        if options.no_input:
            os.environ["PIP_NO_INPUT"] = "1"

        if options.exists_action:
            os.environ["PIP_EXISTS_ACTION"] = " ".join(options.exists_action)

        if options.require_venv and not self.ignore_require_venv:
            # If a venv is required check if it can really be found
            if not running_under_virtualenv():
                logger.critical("Could not find an activated virtualenv (required).")
                sys.exit(VIRTUALENV_NOT_FOUND)

        if options.cache_dir:
            options.cache_dir = normalize_path(options.cache_dir)
            if not check_path_owner(options.cache_dir):
                logger.warning(
                    "The directory '%s' or its parent directory is not owned "
                    "or is not writable by the current user. The cache "
                    "has been disabled. Check the permissions and owner of "
                    "that directory. If executing pip with sudo, you should "
                    "use sudo's -H flag.",
                    options.cache_dir,
                )
                options.cache_dir = None

        return self._run_wrapper(level_number, options, args)

    def handler_map(self) -> dict[str, Callable[[Values, list[str]], None]]:
        """
        map of names to handler actions for commands with sub-actions
        """
        return {}

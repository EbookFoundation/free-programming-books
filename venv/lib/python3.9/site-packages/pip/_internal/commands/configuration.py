from __future__ import annotations

import logging
import os
import subprocess
from optparse import Values
from typing import Any, Callable

from pip._internal.cli.base_command import Command
from pip._internal.cli.status_codes import ERROR, SUCCESS
from pip._internal.configuration import (
    Configuration,
    Kind,
    get_configuration_files,
    kinds,
)
from pip._internal.exceptions import PipError
from pip._internal.utils.logging import indent_log
from pip._internal.utils.misc import get_prog, write_output

logger = logging.getLogger(__name__)


class ConfigurationCommand(Command):
    """
    Manage local and global configuration.

    Subcommands:

    - list: List the active configuration (or from the file specified)
    - edit: Edit the configuration file in an editor
    - get: Get the value associated with command.option
    - set: Set the command.option=value
    - unset: Unset the value associated with command.option
    - debug: List the configuration files and values defined under them

    Configuration keys should be dot separated command and option name,
    with the special prefix "global" affecting any command. For example,
    "pip config set global.index-url https://example.org/" would configure
    the index url for all commands, but "pip config set download.timeout 10"
    would configure a 10 second timeout only for "pip download" commands.

    If none of --user, --global and --site are passed, a virtual
    environment configuration file is used if one is active and the file
    exists. Otherwise, all modifications happen to the user file by
    default.
    """

    ignore_require_venv = True
    usage = """
        %prog [<file-option>] list
        %prog [<file-option>] [--editor <editor-path>] edit

        %prog [<file-option>] get command.option
        %prog [<file-option>] set command.option value
        %prog [<file-option>] unset command.option
        %prog [<file-option>] debug
    """

    def add_options(self) -> None:
        self.cmd_opts.add_option(
            "--editor",
            dest="editor",
            action="store",
            default=None,
            help=(
                "Editor to use to edit the file. Uses VISUAL or EDITOR "
                "environment variables if not provided."
            ),
        )

        self.cmd_opts.add_option(
            "--global",
            dest="global_file",
            action="store_true",
            default=False,
            help="Use the system-wide configuration file only",
        )

        self.cmd_opts.add_option(
            "--user",
            dest="user_file",
            action="store_true",
            default=False,
            help="Use the user configuration file only",
        )

        self.cmd_opts.add_option(
            "--site",
            dest="site_file",
            action="store_true",
            default=False,
            help="Use the current environment configuration file only",
        )

        self.parser.insert_option_group(0, self.cmd_opts)

    def handler_map(self) -> dict[str, Callable[[Values, list[str]], None]]:
        return {
            "list": self.list_values,
            "edit": self.open_in_editor,
            "get": self.get_name,
            "set": self.set_name_value,
            "unset": self.unset_name,
            "debug": self.list_config_values,
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

        # Determine which configuration files are to be loaded
        #    Depends on whether the command is modifying.
        try:
            load_only = self._determine_file(
                options, need_value=(action in ["get", "set", "unset", "edit"])
            )
        except PipError as e:
            logger.error(e.args[0])
            return ERROR

        # Load a new configuration
        self.configuration = Configuration(
            isolated=options.isolated_mode, load_only=load_only
        )
        self.configuration.load()

        # Error handling happens here, not in the action-handlers.
        try:
            handler_map[action](options, args[1:])
        except PipError as e:
            logger.error(e.args[0])
            return ERROR

        return SUCCESS

    def _determine_file(self, options: Values, need_value: bool) -> Kind | None:
        file_options = [
            key
            for key, value in (
                (kinds.USER, options.user_file),
                (kinds.GLOBAL, options.global_file),
                (kinds.SITE, options.site_file),
            )
            if value
        ]

        if not file_options:
            if not need_value:
                return None
            # Default to user, unless there's a site file.
            elif any(
                os.path.exists(site_config_file)
                for site_config_file in get_configuration_files()[kinds.SITE]
            ):
                return kinds.SITE
            else:
                return kinds.USER
        elif len(file_options) == 1:
            return file_options[0]

        raise PipError(
            "Need exactly one file to operate upon "
            "(--user, --site, --global) to perform."
        )

    def list_values(self, options: Values, args: list[str]) -> None:
        self._get_n_args(args, "list", n=0)

        for key, value in sorted(self.configuration.items()):
            for key, value in sorted(value.items()):
                write_output("%s=%r", key, value)

    def get_name(self, options: Values, args: list[str]) -> None:
        key = self._get_n_args(args, "get [name]", n=1)
        value = self.configuration.get_value(key)

        write_output("%s", value)

    def set_name_value(self, options: Values, args: list[str]) -> None:
        key, value = self._get_n_args(args, "set [name] [value]", n=2)
        self.configuration.set_value(key, value)

        self._save_configuration()

    def unset_name(self, options: Values, args: list[str]) -> None:
        key = self._get_n_args(args, "unset [name]", n=1)
        self.configuration.unset_value(key)

        self._save_configuration()

    def list_config_values(self, options: Values, args: list[str]) -> None:
        """List config key-value pairs across different config files"""
        self._get_n_args(args, "debug", n=0)

        self.print_env_var_values()
        # Iterate over config files and print if they exist, and the
        # key-value pairs present in them if they do
        for variant, files in sorted(self.configuration.iter_config_files()):
            write_output("%s:", variant)
            for fname in files:
                with indent_log():
                    file_exists = os.path.exists(fname)
                    write_output("%s, exists: %r", fname, file_exists)
                    if file_exists:
                        self.print_config_file_values(variant, fname)

    def print_config_file_values(self, variant: Kind, fname: str) -> None:
        """Get key-value pairs from the file of a variant"""
        for name, value in self.configuration.get_values_in_config(variant).items():
            with indent_log():
                if name == fname:
                    for confname, confvalue in value.items():
                        write_output("%s: %s", confname, confvalue)

    def print_env_var_values(self) -> None:
        """Get key-values pairs present as environment variables"""
        write_output("%s:", "env_var")
        with indent_log():
            for key, value in sorted(self.configuration.get_environ_vars()):
                env_var = f"PIP_{key.upper()}"
                write_output("%s=%r", env_var, value)

    def open_in_editor(self, options: Values, args: list[str]) -> None:
        editor = self._determine_editor(options)

        fname = self.configuration.get_file_to_edit()
        if fname is None:
            raise PipError("Could not determine appropriate file.")
        elif '"' in fname:
            # This shouldn't happen, unless we see a username like that.
            # If that happens, we'd appreciate a pull request fixing this.
            raise PipError(
                f'Can not open an editor for a file name containing "\n{fname}'
            )

        try:
            subprocess.check_call(f'{editor} "{fname}"', shell=True)
        except FileNotFoundError as e:
            if not e.filename:
                e.filename = editor
            raise
        except subprocess.CalledProcessError as e:
            raise PipError(f"Editor Subprocess exited with exit code {e.returncode}")

    def _get_n_args(self, args: list[str], example: str, n: int) -> Any:
        """Helper to make sure the command got the right number of arguments"""
        if len(args) != n:
            msg = (
                f"Got unexpected number of arguments, expected {n}. "
                f'(example: "{get_prog()} config {example}")'
            )
            raise PipError(msg)

        if n == 1:
            return args[0]
        else:
            return args

    def _save_configuration(self) -> None:
        # We successfully ran a modifying command. Need to save the
        # configuration.
        try:
            self.configuration.save()
        except Exception:
            logger.exception(
                "Unable to save configuration. Please report this as a bug."
            )
            raise PipError("Internal Error.")

    def _determine_editor(self, options: Values) -> str:
        if options.editor is not None:
            return options.editor
        elif "VISUAL" in os.environ:
            return os.environ["VISUAL"]
        elif "EDITOR" in os.environ:
            return os.environ["EDITOR"]
        else:
            raise PipError("Could not determine editor to use.")

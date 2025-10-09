"""Configuration management setup

Some terminology:
- name
  As written in config files.
- value
  Value associated with a name
- key
  Name combined with it's section (section.name)
- variant
  A single word describing where the configuration key-value pair came from
"""

from __future__ import annotations

import configparser
import locale
import os
import sys
from collections.abc import Iterable
from typing import Any, NewType

from pip._internal.exceptions import (
    ConfigurationError,
    ConfigurationFileCouldNotBeLoaded,
)
from pip._internal.utils import appdirs
from pip._internal.utils.compat import WINDOWS
from pip._internal.utils.logging import getLogger
from pip._internal.utils.misc import ensure_dir, enum

RawConfigParser = configparser.RawConfigParser  # Shorthand
Kind = NewType("Kind", str)

CONFIG_BASENAME = "pip.ini" if WINDOWS else "pip.conf"
ENV_NAMES_IGNORED = "version", "help"

# The kinds of configurations there are.
kinds = enum(
    USER="user",  # User Specific
    GLOBAL="global",  # System Wide
    SITE="site",  # [Virtual] Environment Specific
    ENV="env",  # from PIP_CONFIG_FILE
    ENV_VAR="env-var",  # from Environment Variables
)
OVERRIDE_ORDER = kinds.GLOBAL, kinds.USER, kinds.SITE, kinds.ENV, kinds.ENV_VAR
VALID_LOAD_ONLY = kinds.USER, kinds.GLOBAL, kinds.SITE

logger = getLogger(__name__)


# NOTE: Maybe use the optionx attribute to normalize keynames.
def _normalize_name(name: str) -> str:
    """Make a name consistent regardless of source (environment or file)"""
    name = name.lower().replace("_", "-")
    if name.startswith("--"):
        name = name[2:]  # only prefer long opts
    return name


def _disassemble_key(name: str) -> list[str]:
    if "." not in name:
        error_message = (
            "Key does not contain dot separated section and key. "
            f"Perhaps you wanted to use 'global.{name}' instead?"
        )
        raise ConfigurationError(error_message)
    return name.split(".", 1)


def get_configuration_files() -> dict[Kind, list[str]]:
    global_config_files = [
        os.path.join(path, CONFIG_BASENAME) for path in appdirs.site_config_dirs("pip")
    ]

    site_config_file = os.path.join(sys.prefix, CONFIG_BASENAME)
    legacy_config_file = os.path.join(
        os.path.expanduser("~"),
        "pip" if WINDOWS else ".pip",
        CONFIG_BASENAME,
    )
    new_config_file = os.path.join(appdirs.user_config_dir("pip"), CONFIG_BASENAME)
    return {
        kinds.GLOBAL: global_config_files,
        kinds.SITE: [site_config_file],
        kinds.USER: [legacy_config_file, new_config_file],
    }


class Configuration:
    """Handles management of configuration.

    Provides an interface to accessing and managing configuration files.

    This class converts provides an API that takes "section.key-name" style
    keys and stores the value associated with it as "key-name" under the
    section "section".

    This allows for a clean interface wherein the both the section and the
    key-name are preserved in an easy to manage form in the configuration files
    and the data stored is also nice.
    """

    def __init__(self, isolated: bool, load_only: Kind | None = None) -> None:
        super().__init__()

        if load_only is not None and load_only not in VALID_LOAD_ONLY:
            raise ConfigurationError(
                "Got invalid value for load_only - should be one of {}".format(
                    ", ".join(map(repr, VALID_LOAD_ONLY))
                )
            )
        self.isolated = isolated
        self.load_only = load_only

        # Because we keep track of where we got the data from
        self._parsers: dict[Kind, list[tuple[str, RawConfigParser]]] = {
            variant: [] for variant in OVERRIDE_ORDER
        }
        self._config: dict[Kind, dict[str, dict[str, Any]]] = {
            variant: {} for variant in OVERRIDE_ORDER
        }
        self._modified_parsers: list[tuple[str, RawConfigParser]] = []

    def load(self) -> None:
        """Loads configuration from configuration files and environment"""
        self._load_config_files()
        if not self.isolated:
            self._load_environment_vars()

    def get_file_to_edit(self) -> str | None:
        """Returns the file with highest priority in configuration"""
        assert self.load_only is not None, "Need to be specified a file to be editing"

        try:
            return self._get_parser_to_modify()[0]
        except IndexError:
            return None

    def items(self) -> Iterable[tuple[str, Any]]:
        """Returns key-value pairs like dict.items() representing the loaded
        configuration
        """
        return self._dictionary.items()

    def get_value(self, key: str) -> Any:
        """Get a value from the configuration."""
        orig_key = key
        key = _normalize_name(key)
        try:
            clean_config: dict[str, Any] = {}
            for file_values in self._dictionary.values():
                clean_config.update(file_values)
            return clean_config[key]
        except KeyError:
            # disassembling triggers a more useful error message than simply
            # "No such key" in the case that the key isn't in the form command.option
            _disassemble_key(key)
            raise ConfigurationError(f"No such key - {orig_key}")

    def set_value(self, key: str, value: Any) -> None:
        """Modify a value in the configuration."""
        key = _normalize_name(key)
        self._ensure_have_load_only()

        assert self.load_only
        fname, parser = self._get_parser_to_modify()

        if parser is not None:
            section, name = _disassemble_key(key)

            # Modify the parser and the configuration
            if not parser.has_section(section):
                parser.add_section(section)
            parser.set(section, name, value)

        self._config[self.load_only].setdefault(fname, {})
        self._config[self.load_only][fname][key] = value
        self._mark_as_modified(fname, parser)

    def unset_value(self, key: str) -> None:
        """Unset a value in the configuration."""
        orig_key = key
        key = _normalize_name(key)
        self._ensure_have_load_only()

        assert self.load_only
        fname, parser = self._get_parser_to_modify()

        if (
            key not in self._config[self.load_only][fname]
            and key not in self._config[self.load_only]
        ):
            raise ConfigurationError(f"No such key - {orig_key}")

        if parser is not None:
            section, name = _disassemble_key(key)
            if not (
                parser.has_section(section) and parser.remove_option(section, name)
            ):
                # The option was not removed.
                raise ConfigurationError(
                    "Fatal Internal error [id=1]. Please report as a bug."
                )

            # The section may be empty after the option was removed.
            if not parser.items(section):
                parser.remove_section(section)
            self._mark_as_modified(fname, parser)
        try:
            del self._config[self.load_only][fname][key]
        except KeyError:
            del self._config[self.load_only][key]

    def save(self) -> None:
        """Save the current in-memory state."""
        self._ensure_have_load_only()

        for fname, parser in self._modified_parsers:
            logger.info("Writing to %s", fname)

            # Ensure directory exists.
            ensure_dir(os.path.dirname(fname))

            # Ensure directory's permission(need to be writeable)
            try:
                with open(fname, "w") as f:
                    parser.write(f)
            except OSError as error:
                raise ConfigurationError(
                    f"An error occurred while writing to the configuration file "
                    f"{fname}: {error}"
                )

    #
    # Private routines
    #

    def _ensure_have_load_only(self) -> None:
        if self.load_only is None:
            raise ConfigurationError("Needed a specific file to be modifying.")
        logger.debug("Will be working with %s variant only", self.load_only)

    @property
    def _dictionary(self) -> dict[str, dict[str, Any]]:
        """A dictionary representing the loaded configuration."""
        # NOTE: Dictionaries are not populated if not loaded. So, conditionals
        #       are not needed here.
        retval = {}

        for variant in OVERRIDE_ORDER:
            retval.update(self._config[variant])

        return retval

    def _load_config_files(self) -> None:
        """Loads configuration from configuration files"""
        config_files = dict(self.iter_config_files())
        if config_files[kinds.ENV][0:1] == [os.devnull]:
            logger.debug(
                "Skipping loading configuration files due to "
                "environment's PIP_CONFIG_FILE being os.devnull"
            )
            return

        for variant, files in config_files.items():
            for fname in files:
                # If there's specific variant set in `load_only`, load only
                # that variant, not the others.
                if self.load_only is not None and variant != self.load_only:
                    logger.debug("Skipping file '%s' (variant: %s)", fname, variant)
                    continue

                parser = self._load_file(variant, fname)

                # Keeping track of the parsers used
                self._parsers[variant].append((fname, parser))

    def _load_file(self, variant: Kind, fname: str) -> RawConfigParser:
        logger.verbose("For variant '%s', will try loading '%s'", variant, fname)
        parser = self._construct_parser(fname)

        for section in parser.sections():
            items = parser.items(section)
            self._config[variant].setdefault(fname, {})
            self._config[variant][fname].update(self._normalized_keys(section, items))

        return parser

    def _construct_parser(self, fname: str) -> RawConfigParser:
        parser = configparser.RawConfigParser()
        # If there is no such file, don't bother reading it but create the
        # parser anyway, to hold the data.
        # Doing this is useful when modifying and saving files, where we don't
        # need to construct a parser.
        if os.path.exists(fname):
            locale_encoding = locale.getpreferredencoding(False)
            try:
                parser.read(fname, encoding=locale_encoding)
            except UnicodeDecodeError:
                # See https://github.com/pypa/pip/issues/4963
                raise ConfigurationFileCouldNotBeLoaded(
                    reason=f"contains invalid {locale_encoding} characters",
                    fname=fname,
                )
            except configparser.Error as error:
                # See https://github.com/pypa/pip/issues/4893
                raise ConfigurationFileCouldNotBeLoaded(error=error)
        return parser

    def _load_environment_vars(self) -> None:
        """Loads configuration from environment variables"""
        self._config[kinds.ENV_VAR].setdefault(":env:", {})
        self._config[kinds.ENV_VAR][":env:"].update(
            self._normalized_keys(":env:", self.get_environ_vars())
        )

    def _normalized_keys(
        self, section: str, items: Iterable[tuple[str, Any]]
    ) -> dict[str, Any]:
        """Normalizes items to construct a dictionary with normalized keys.

        This routine is where the names become keys and are made the same
        regardless of source - configuration files or environment.
        """
        normalized = {}
        for name, val in items:
            key = section + "." + _normalize_name(name)
            normalized[key] = val
        return normalized

    def get_environ_vars(self) -> Iterable[tuple[str, str]]:
        """Returns a generator with all environmental vars with prefix PIP_"""
        for key, val in os.environ.items():
            if key.startswith("PIP_"):
                name = key[4:].lower()
                if name not in ENV_NAMES_IGNORED:
                    yield name, val

    # XXX: This is patched in the tests.
    def iter_config_files(self) -> Iterable[tuple[Kind, list[str]]]:
        """Yields variant and configuration files associated with it.

        This should be treated like items of a dictionary. The order
        here doesn't affect what gets overridden. That is controlled
        by OVERRIDE_ORDER. However this does control the order they are
        displayed to the user. It's probably most ergonomic to display
        things in the same order as OVERRIDE_ORDER
        """
        # SMELL: Move the conditions out of this function

        env_config_file = os.environ.get("PIP_CONFIG_FILE", None)
        config_files = get_configuration_files()

        yield kinds.GLOBAL, config_files[kinds.GLOBAL]

        # per-user config is not loaded when env_config_file exists
        should_load_user_config = not self.isolated and not (
            env_config_file and os.path.exists(env_config_file)
        )
        if should_load_user_config:
            # The legacy config file is overridden by the new config file
            yield kinds.USER, config_files[kinds.USER]

        # virtualenv config
        yield kinds.SITE, config_files[kinds.SITE]

        if env_config_file is not None:
            yield kinds.ENV, [env_config_file]
        else:
            yield kinds.ENV, []

    def get_values_in_config(self, variant: Kind) -> dict[str, Any]:
        """Get values present in a config file"""
        return self._config[variant]

    def _get_parser_to_modify(self) -> tuple[str, RawConfigParser]:
        # Determine which parser to modify
        assert self.load_only
        parsers = self._parsers[self.load_only]
        if not parsers:
            # This should not happen if everything works correctly.
            raise ConfigurationError(
                "Fatal Internal error [id=2]. Please report as a bug."
            )

        # Use the highest priority parser.
        return parsers[-1]

    # XXX: This is patched in the tests.
    def _mark_as_modified(self, fname: str, parser: RawConfigParser) -> None:
        file_parser_tuple = (fname, parser)
        if file_parser_tuple not in self._modified_parsers:
            self._modified_parsers.append(file_parser_tuple)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._dictionary!r})"

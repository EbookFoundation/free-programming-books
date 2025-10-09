from __future__ import annotations

import locale
import logging
import os
import sys
from optparse import Values
from types import ModuleType
from typing import Any

import pip._vendor
from pip._vendor.certifi import where
from pip._vendor.packaging.version import parse as parse_version

from pip._internal.cli import cmdoptions
from pip._internal.cli.base_command import Command
from pip._internal.cli.cmdoptions import make_target_python
from pip._internal.cli.status_codes import SUCCESS
from pip._internal.configuration import Configuration
from pip._internal.metadata import get_environment
from pip._internal.utils.compat import open_text_resource
from pip._internal.utils.logging import indent_log
from pip._internal.utils.misc import get_pip_version

logger = logging.getLogger(__name__)


def show_value(name: str, value: Any) -> None:
    logger.info("%s: %s", name, value)


def show_sys_implementation() -> None:
    logger.info("sys.implementation:")
    implementation_name = sys.implementation.name
    with indent_log():
        show_value("name", implementation_name)


def create_vendor_txt_map() -> dict[str, str]:
    with open_text_resource("pip._vendor", "vendor.txt") as f:
        # Purge non version specifying lines.
        # Also, remove any space prefix or suffixes (including comments).
        lines = [
            line.strip().split(" ", 1)[0] for line in f.readlines() if "==" in line
        ]

    # Transform into "module" -> version dict.
    return dict(line.split("==", 1) for line in lines)


def get_module_from_module_name(module_name: str) -> ModuleType | None:
    # Module name can be uppercase in vendor.txt for some reason...
    module_name = module_name.lower().replace("-", "_")
    # PATCH: setuptools is actually only pkg_resources.
    if module_name == "setuptools":
        module_name = "pkg_resources"

    try:
        __import__(f"pip._vendor.{module_name}", globals(), locals(), level=0)
        return getattr(pip._vendor, module_name)
    except ImportError:
        # We allow 'truststore' to fail to import due
        # to being unavailable on Python 3.9 and earlier.
        if module_name == "truststore" and sys.version_info < (3, 10):
            return None
        raise


def get_vendor_version_from_module(module_name: str) -> str | None:
    module = get_module_from_module_name(module_name)
    version = getattr(module, "__version__", None)

    if module and not version:
        # Try to find version in debundled module info.
        assert module.__file__ is not None
        env = get_environment([os.path.dirname(module.__file__)])
        dist = env.get_distribution(module_name)
        if dist:
            version = str(dist.version)

    return version


def show_actual_vendor_versions(vendor_txt_versions: dict[str, str]) -> None:
    """Log the actual version and print extra info if there is
    a conflict or if the actual version could not be imported.
    """
    for module_name, expected_version in vendor_txt_versions.items():
        extra_message = ""
        actual_version = get_vendor_version_from_module(module_name)
        if not actual_version:
            extra_message = (
                " (Unable to locate actual module version, using"
                " vendor.txt specified version)"
            )
            actual_version = expected_version
        elif parse_version(actual_version) != parse_version(expected_version):
            extra_message = (
                " (CONFLICT: vendor.txt suggests version should"
                f" be {expected_version})"
            )
        logger.info("%s==%s%s", module_name, actual_version, extra_message)


def show_vendor_versions() -> None:
    logger.info("vendored library versions:")

    vendor_txt_versions = create_vendor_txt_map()
    with indent_log():
        show_actual_vendor_versions(vendor_txt_versions)


def show_tags(options: Values) -> None:
    tag_limit = 10

    target_python = make_target_python(options)
    tags = target_python.get_sorted_tags()

    # Display the target options that were explicitly provided.
    formatted_target = target_python.format_given()
    suffix = ""
    if formatted_target:
        suffix = f" (target: {formatted_target})"

    msg = f"Compatible tags: {len(tags)}{suffix}"
    logger.info(msg)

    if options.verbose < 1 and len(tags) > tag_limit:
        tags_limited = True
        tags = tags[:tag_limit]
    else:
        tags_limited = False

    with indent_log():
        for tag in tags:
            logger.info(str(tag))

        if tags_limited:
            msg = f"...\n[First {tag_limit} tags shown. Pass --verbose to show all.]"
            logger.info(msg)


def ca_bundle_info(config: Configuration) -> str:
    levels = {key.split(".", 1)[0] for key, _ in config.items()}
    if not levels:
        return "Not specified"

    levels_that_override_global = ["install", "wheel", "download"]
    global_overriding_level = [
        level for level in levels if level in levels_that_override_global
    ]
    if not global_overriding_level:
        return "global"

    if "global" in levels:
        levels.remove("global")
    return ", ".join(levels)


class DebugCommand(Command):
    """
    Display debug information.
    """

    usage = """
      %prog <options>"""
    ignore_require_venv = True

    def add_options(self) -> None:
        cmdoptions.add_target_python_options(self.cmd_opts)
        self.parser.insert_option_group(0, self.cmd_opts)
        self.parser.config.load()

    def run(self, options: Values, args: list[str]) -> int:
        logger.warning(
            "This command is only meant for debugging. "
            "Do not use this with automation for parsing and getting these "
            "details, since the output and options of this command may "
            "change without notice."
        )
        show_value("pip version", get_pip_version())
        show_value("sys.version", sys.version)
        show_value("sys.executable", sys.executable)
        show_value("sys.getdefaultencoding", sys.getdefaultencoding())
        show_value("sys.getfilesystemencoding", sys.getfilesystemencoding())
        show_value(
            "locale.getpreferredencoding",
            locale.getpreferredencoding(),
        )
        show_value("sys.platform", sys.platform)
        show_sys_implementation()

        show_value("'cert' config value", ca_bundle_info(self.parser.config))
        show_value("REQUESTS_CA_BUNDLE", os.environ.get("REQUESTS_CA_BUNDLE"))
        show_value("CURL_CA_BUNDLE", os.environ.get("CURL_CA_BUNDLE"))
        show_value("pip._vendor.certifi.where()", where())
        show_value("pip._vendor.DEBUNDLED", pip._vendor.DEBUNDLED)

        show_vendor_versions()

        show_tags(options)

        return SUCCESS

"""Primary application entrypoint."""

from __future__ import annotations

import locale
import logging
import os
import sys
import warnings

from pip._internal.cli.autocompletion import autocomplete
from pip._internal.cli.main_parser import parse_command
from pip._internal.commands import create_command
from pip._internal.exceptions import PipError
from pip._internal.utils import deprecation

logger = logging.getLogger(__name__)


# Do not import and use main() directly! Using it directly is actively
# discouraged by pip's maintainers. The name, location and behavior of
# this function is subject to change, so calling it directly is not
# portable across different pip versions.

# In addition, running pip in-process is unsupported and unsafe. This is
# elaborated in detail at
# https://pip.pypa.io/en/stable/user_guide/#using-pip-from-your-program.
# That document also provides suggestions that should work for nearly
# all users that are considering importing and using main() directly.

# However, we know that certain users will still want to invoke pip
# in-process. If you understand and accept the implications of using pip
# in an unsupported manner, the best approach is to use runpy to avoid
# depending on the exact location of this entry point.

# The following example shows how to use runpy to invoke pip in that
# case:
#
#     sys.argv = ["pip", your, args, here]
#     runpy.run_module("pip", run_name="__main__")
#
# Note that this will exit the process after running, unlike a direct
# call to main. As it is not safe to do any processing after calling
# main, this should not be an issue in practice.


def main(args: list[str] | None = None) -> int:
    if args is None:
        args = sys.argv[1:]

    # Suppress the pkg_resources deprecation warning
    # Note - we use a module of .*pkg_resources to cover
    # the normal case (pip._vendor.pkg_resources) and the
    # devendored case (a bare pkg_resources)
    warnings.filterwarnings(
        action="ignore", category=DeprecationWarning, module=".*pkg_resources"
    )

    # Configure our deprecation warnings to be sent through loggers
    deprecation.install_warning_logger()

    autocomplete()

    try:
        cmd_name, cmd_args = parse_command(args)
    except PipError as exc:
        sys.stderr.write(f"ERROR: {exc}")
        sys.stderr.write(os.linesep)
        sys.exit(1)

    # Needed for locale.getpreferredencoding(False) to work
    # in pip._internal.utils.encoding.auto_decode
    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error as e:
        # setlocale can apparently crash if locale are uninitialized
        logger.debug("Ignoring error %s when setting locale", e)
    command = create_command(cmd_name, isolated=("--isolated" in cmd_args))

    return command.main(cmd_args)

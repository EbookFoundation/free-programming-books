from __future__ import annotations

import logging
import os.path

from pip._internal.cli.spinners import open_spinner
from pip._internal.utils.deprecation import deprecated
from pip._internal.utils.setuptools_build import make_setuptools_bdist_wheel_args
from pip._internal.utils.subprocess import call_subprocess, format_command_args

logger = logging.getLogger(__name__)


def format_command_result(
    command_args: list[str],
    command_output: str,
) -> str:
    """Format command information for logging."""
    command_desc = format_command_args(command_args)
    text = f"Command arguments: {command_desc}\n"

    if not command_output:
        text += "Command output: None"
    elif logger.getEffectiveLevel() > logging.DEBUG:
        text += "Command output: [use --verbose to show]"
    else:
        if not command_output.endswith("\n"):
            command_output += "\n"
        text += f"Command output:\n{command_output}"

    return text


def get_legacy_build_wheel_path(
    names: list[str],
    temp_dir: str,
    name: str,
    command_args: list[str],
    command_output: str,
) -> str | None:
    """Return the path to the wheel in the temporary build directory."""
    # Sort for determinism.
    names = sorted(names)
    if not names:
        msg = f"Legacy build of wheel for {name!r} created no files.\n"
        msg += format_command_result(command_args, command_output)
        logger.warning(msg)
        return None

    if len(names) > 1:
        msg = (
            f"Legacy build of wheel for {name!r} created more than one file.\n"
            f"Filenames (choosing first): {names}\n"
        )
        msg += format_command_result(command_args, command_output)
        logger.warning(msg)

    return os.path.join(temp_dir, names[0])


def build_wheel_legacy(
    name: str,
    setup_py_path: str,
    source_dir: str,
    global_options: list[str],
    build_options: list[str],
    tempd: str,
) -> str | None:
    """Build one unpacked package using the "legacy" build process.

    Returns path to wheel if successfully built. Otherwise, returns None.
    """
    deprecated(
        reason=(
            f"Building {name!r} using the legacy setup.py bdist_wheel mechanism, "
            "which will be removed in a future version."
        ),
        replacement=(
            "to use the standardized build interface by "
            "setting the `--use-pep517` option, "
            "(possibly combined with `--no-build-isolation`), "
            f"or adding a `pyproject.toml` file to the source tree of {name!r}"
        ),
        gone_in="25.3",
        issue=6334,
    )

    wheel_args = make_setuptools_bdist_wheel_args(
        setup_py_path,
        global_options=global_options,
        build_options=build_options,
        destination_dir=tempd,
    )

    spin_message = f"Building wheel for {name} (setup.py)"
    with open_spinner(spin_message) as spinner:
        logger.debug("Destination directory: %s", tempd)

        try:
            output = call_subprocess(
                wheel_args,
                command_desc="python setup.py bdist_wheel",
                cwd=source_dir,
                spinner=spinner,
            )
        except Exception:
            spinner.finish("error")
            logger.error("Failed building wheel for %s", name)
            return None

        names = os.listdir(tempd)
        wheel_path = get_legacy_build_wheel_path(
            names=names,
            temp_dir=tempd,
            name=name,
            command_args=wheel_args,
            command_output=output,
        )
        return wheel_path

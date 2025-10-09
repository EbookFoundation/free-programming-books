"""Metadata generation logic for legacy source distributions."""

import logging
import os

from pip._internal.build_env import BuildEnvironment
from pip._internal.cli.spinners import open_spinner
from pip._internal.exceptions import (
    InstallationError,
    InstallationSubprocessError,
    MetadataGenerationFailed,
)
from pip._internal.utils.setuptools_build import make_setuptools_egg_info_args
from pip._internal.utils.subprocess import call_subprocess
from pip._internal.utils.temp_dir import TempDirectory

logger = logging.getLogger(__name__)


def _find_egg_info(directory: str) -> str:
    """Find an .egg-info subdirectory in `directory`."""
    filenames = [f for f in os.listdir(directory) if f.endswith(".egg-info")]

    if not filenames:
        raise InstallationError(f"No .egg-info directory found in {directory}")

    if len(filenames) > 1:
        raise InstallationError(
            f"More than one .egg-info directory found in {directory}"
        )

    return os.path.join(directory, filenames[0])


def generate_metadata(
    build_env: BuildEnvironment,
    setup_py_path: str,
    source_dir: str,
    isolated: bool,
    details: str,
) -> str:
    """Generate metadata using setup.py-based defacto mechanisms.

    Returns the generated metadata directory.
    """
    logger.debug(
        "Running setup.py (path:%s) egg_info for package %s",
        setup_py_path,
        details,
    )

    egg_info_dir = TempDirectory(kind="pip-egg-info", globally_managed=True).path

    args = make_setuptools_egg_info_args(
        setup_py_path,
        egg_info_dir=egg_info_dir,
        no_user_config=isolated,
    )

    with build_env:
        with open_spinner("Preparing metadata (setup.py)") as spinner:
            try:
                call_subprocess(
                    args,
                    cwd=source_dir,
                    command_desc="python setup.py egg_info",
                    spinner=spinner,
                )
            except InstallationSubprocessError as error:
                raise MetadataGenerationFailed(package_details=details) from error

    # Return the .egg-info directory.
    return _find_egg_info(egg_info_dir)

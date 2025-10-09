from __future__ import annotations

import logging
import os

from pip._vendor.pyproject_hooks import BuildBackendHookCaller

from pip._internal.utils.subprocess import runner_with_spinner_message

logger = logging.getLogger(__name__)


def build_wheel_pep517(
    name: str,
    backend: BuildBackendHookCaller,
    metadata_directory: str,
    tempd: str,
) -> str | None:
    """Build one InstallRequirement using the PEP 517 build process.

    Returns path to wheel if successfully built. Otherwise, returns None.
    """
    assert metadata_directory is not None
    try:
        logger.debug("Destination directory: %s", tempd)

        runner = runner_with_spinner_message(
            f"Building wheel for {name} (pyproject.toml)"
        )
        with backend.subprocess_runner(runner):
            wheel_name = backend.build_wheel(
                tempd,
                metadata_directory=metadata_directory,
            )
    except Exception:
        logger.error("Failed building wheel for %s", name)
        return None
    return os.path.join(tempd, wheel_name)

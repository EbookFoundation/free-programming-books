from __future__ import annotations

import logging
import os

from pip._vendor.pyproject_hooks import BuildBackendHookCaller, HookMissing

from pip._internal.utils.subprocess import runner_with_spinner_message

logger = logging.getLogger(__name__)


def build_wheel_editable(
    name: str,
    backend: BuildBackendHookCaller,
    metadata_directory: str,
    tempd: str,
) -> str | None:
    """Build one InstallRequirement using the PEP 660 build process.

    Returns path to wheel if successfully built. Otherwise, returns None.
    """
    assert metadata_directory is not None
    try:
        logger.debug("Destination directory: %s", tempd)

        runner = runner_with_spinner_message(
            f"Building editable for {name} (pyproject.toml)"
        )
        with backend.subprocess_runner(runner):
            try:
                wheel_name = backend.build_editable(
                    tempd,
                    metadata_directory=metadata_directory,
                )
            except HookMissing as e:
                logger.error(
                    "Cannot build editable %s because the build "
                    "backend does not have the %s hook",
                    name,
                    e,
                )
                return None
    except Exception:
        logger.error("Failed building editable for %s", name)
        return None
    return os.path.join(tempd, wheel_name)

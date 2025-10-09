from __future__ import annotations

import importlib.util
import os
from collections import namedtuple
from typing import Any

from pip._vendor.packaging.requirements import InvalidRequirement

from pip._internal.exceptions import (
    InstallationError,
    InvalidPyProjectBuildRequires,
    MissingPyProjectBuildRequires,
)
from pip._internal.utils.compat import tomllib
from pip._internal.utils.packaging import get_requirement


def _is_list_of_str(obj: Any) -> bool:
    return isinstance(obj, list) and all(isinstance(item, str) for item in obj)


def make_pyproject_path(unpacked_source_directory: str) -> str:
    return os.path.join(unpacked_source_directory, "pyproject.toml")


BuildSystemDetails = namedtuple(
    "BuildSystemDetails", ["requires", "backend", "check", "backend_path"]
)


def load_pyproject_toml(
    use_pep517: bool | None, pyproject_toml: str, setup_py: str, req_name: str
) -> BuildSystemDetails | None:
    """Load the pyproject.toml file.

    Parameters:
        use_pep517 - Has the user requested PEP 517 processing? None
                     means the user hasn't explicitly specified.
        pyproject_toml - Location of the project's pyproject.toml file
        setup_py - Location of the project's setup.py file
        req_name - The name of the requirement we're processing (for
                   error reporting)

    Returns:
        None if we should use the legacy code path, otherwise a tuple
        (
            requirements from pyproject.toml,
            name of PEP 517 backend,
            requirements we should check are installed after setting
                up the build environment
            directory paths to import the backend from (backend-path),
                relative to the project root.
        )
    """
    has_pyproject = os.path.isfile(pyproject_toml)
    has_setup = os.path.isfile(setup_py)

    if not has_pyproject and not has_setup:
        raise InstallationError(
            f"{req_name} does not appear to be a Python project: "
            f"neither 'setup.py' nor 'pyproject.toml' found."
        )

    if has_pyproject:
        with open(pyproject_toml, encoding="utf-8") as f:
            pp_toml = tomllib.loads(f.read())
        build_system = pp_toml.get("build-system")
    else:
        build_system = None

    # The following cases must use PEP 517
    # We check for use_pep517 being non-None and falsy because that means
    # the user explicitly requested --no-use-pep517.  The value 0 as
    # opposed to False can occur when the value is provided via an
    # environment variable or config file option (due to the quirk of
    # strtobool() returning an integer in pip's configuration code).
    if has_pyproject and not has_setup:
        if use_pep517 is not None and not use_pep517:
            raise InstallationError(
                "Disabling PEP 517 processing is invalid: "
                "project does not have a setup.py"
            )
        use_pep517 = True
    elif build_system and "build-backend" in build_system:
        if use_pep517 is not None and not use_pep517:
            raise InstallationError(
                "Disabling PEP 517 processing is invalid: "
                "project specifies a build backend of {} "
                "in pyproject.toml".format(build_system["build-backend"])
            )
        use_pep517 = True

    # If we haven't worked out whether to use PEP 517 yet,
    # and the user hasn't explicitly stated a preference,
    # we do so if the project has a pyproject.toml file
    # or if we cannot import setuptools or wheels.

    # We fallback to PEP 517 when without setuptools or without the wheel package,
    # so setuptools can be installed as a default build backend.
    # For more info see:
    # https://discuss.python.org/t/pip-without-setuptools-could-the-experience-be-improved/11810/9
    # https://github.com/pypa/pip/issues/8559
    elif use_pep517 is None:
        use_pep517 = (
            has_pyproject
            or not importlib.util.find_spec("setuptools")
            or not importlib.util.find_spec("wheel")
        )

    # At this point, we know whether we're going to use PEP 517.
    assert use_pep517 is not None

    # If we're using the legacy code path, there is nothing further
    # for us to do here.
    if not use_pep517:
        return None

    if build_system is None:
        # Either the user has a pyproject.toml with no build-system
        # section, or the user has no pyproject.toml, but has opted in
        # explicitly via --use-pep517.
        # In the absence of any explicit backend specification, we
        # assume the setuptools backend that most closely emulates the
        # traditional direct setup.py execution, and require wheel and
        # a version of setuptools that supports that backend.

        build_system = {
            "requires": ["setuptools>=40.8.0"],
            "build-backend": "setuptools.build_meta:__legacy__",
        }

    # If we're using PEP 517, we have build system information (either
    # from pyproject.toml, or defaulted by the code above).
    # Note that at this point, we do not know if the user has actually
    # specified a backend, though.
    assert build_system is not None

    # Ensure that the build-system section in pyproject.toml conforms
    # to PEP 518.

    # Specifying the build-system table but not the requires key is invalid
    if "requires" not in build_system:
        raise MissingPyProjectBuildRequires(package=req_name)

    # Error out if requires is not a list of strings
    requires = build_system["requires"]
    if not _is_list_of_str(requires):
        raise InvalidPyProjectBuildRequires(
            package=req_name,
            reason="It is not a list of strings.",
        )

    # Each requirement must be valid as per PEP 508
    for requirement in requires:
        try:
            get_requirement(requirement)
        except InvalidRequirement as error:
            raise InvalidPyProjectBuildRequires(
                package=req_name,
                reason=f"It contains an invalid requirement: {requirement!r}",
            ) from error

    backend = build_system.get("build-backend")
    backend_path = build_system.get("backend-path", [])
    check: list[str] = []
    if backend is None:
        # If the user didn't specify a backend, we assume they want to use
        # the setuptools backend. But we can't be sure they have included
        # a version of setuptools which supplies the backend. So we
        # make a note to check that this requirement is present once
        # we have set up the environment.
        # This is quite a lot of work to check for a very specific case. But
        # the problem is, that case is potentially quite common - projects that
        # adopted PEP 518 early for the ability to specify requirements to
        # execute setup.py, but never considered needing to mention the build
        # tools themselves. The original PEP 518 code had a similar check (but
        # implemented in a different way).
        backend = "setuptools.build_meta:__legacy__"
        check = ["setuptools>=40.8.0"]

    return BuildSystemDetails(requires, backend, check, backend_path)

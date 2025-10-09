from __future__ import annotations

import errno
import json
import operator
import os
import shutil
import site
from optparse import SUPPRESS_HELP, Values
from pathlib import Path

from pip._vendor.packaging.utils import canonicalize_name
from pip._vendor.requests.exceptions import InvalidProxyURL
from pip._vendor.rich import print_json

# Eagerly import self_outdated_check to avoid crashes. Otherwise,
# this module would be imported *after* pip was replaced, resulting
# in crashes if the new self_outdated_check module was incompatible
# with the rest of pip that's already imported, or allowing a
# wheel to execute arbitrary code on install by replacing
# self_outdated_check.
import pip._internal.self_outdated_check  # noqa: F401
from pip._internal.cache import WheelCache
from pip._internal.cli import cmdoptions
from pip._internal.cli.cmdoptions import make_target_python
from pip._internal.cli.req_command import (
    RequirementCommand,
    with_cleanup,
)
from pip._internal.cli.status_codes import ERROR, SUCCESS
from pip._internal.exceptions import (
    CommandError,
    InstallationError,
    InstallWheelBuildError,
)
from pip._internal.locations import get_scheme
from pip._internal.metadata import get_environment
from pip._internal.models.installation_report import InstallationReport
from pip._internal.operations.build.build_tracker import get_build_tracker
from pip._internal.operations.check import ConflictDetails, check_install_conflicts
from pip._internal.req import install_given_reqs
from pip._internal.req.req_install import (
    InstallRequirement,
    check_legacy_setup_py_options,
)
from pip._internal.utils.compat import WINDOWS
from pip._internal.utils.filesystem import test_writable_dir
from pip._internal.utils.logging import getLogger
from pip._internal.utils.misc import (
    check_externally_managed,
    ensure_dir,
    get_pip_version,
    protect_pip_from_modification_on_windows,
    warn_if_run_as_root,
    write_output,
)
from pip._internal.utils.temp_dir import TempDirectory
from pip._internal.utils.virtualenv import (
    running_under_virtualenv,
    virtualenv_no_global,
)
from pip._internal.wheel_builder import build, should_build_for_install_command

logger = getLogger(__name__)


class InstallCommand(RequirementCommand):
    """
    Install packages from:

    - PyPI (and other indexes) using requirement specifiers.
    - VCS project urls.
    - Local project directories.
    - Local or remote source archives.

    pip also supports installing from "requirements files", which provide
    an easy way to specify a whole environment to be installed.
    """

    usage = """
      %prog [options] <requirement specifier> [package-index-options] ...
      %prog [options] -r <requirements file> [package-index-options] ...
      %prog [options] [-e] <vcs project url> ...
      %prog [options] [-e] <local project path> ...
      %prog [options] <archive url/path> ..."""

    def add_options(self) -> None:
        self.cmd_opts.add_option(cmdoptions.requirements())
        self.cmd_opts.add_option(cmdoptions.constraints())
        self.cmd_opts.add_option(cmdoptions.no_deps())
        self.cmd_opts.add_option(cmdoptions.pre())

        self.cmd_opts.add_option(cmdoptions.editable())
        self.cmd_opts.add_option(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            default=False,
            help=(
                "Don't actually install anything, just print what would be. "
                "Can be used in combination with --ignore-installed "
                "to 'resolve' the requirements."
            ),
        )
        self.cmd_opts.add_option(
            "-t",
            "--target",
            dest="target_dir",
            metavar="dir",
            default=None,
            help=(
                "Install packages into <dir>. "
                "By default this will not replace existing files/folders in "
                "<dir>. Use --upgrade to replace existing packages in <dir> "
                "with new versions."
            ),
        )
        cmdoptions.add_target_python_options(self.cmd_opts)

        self.cmd_opts.add_option(
            "--user",
            dest="use_user_site",
            action="store_true",
            help=(
                "Install to the Python user install directory for your "
                "platform. Typically ~/.local/, or %APPDATA%\\Python on "
                "Windows. (See the Python documentation for site.USER_BASE "
                "for full details.)"
            ),
        )
        self.cmd_opts.add_option(
            "--no-user",
            dest="use_user_site",
            action="store_false",
            help=SUPPRESS_HELP,
        )
        self.cmd_opts.add_option(
            "--root",
            dest="root_path",
            metavar="dir",
            default=None,
            help="Install everything relative to this alternate root directory.",
        )
        self.cmd_opts.add_option(
            "--prefix",
            dest="prefix_path",
            metavar="dir",
            default=None,
            help=(
                "Installation prefix where lib, bin and other top-level "
                "folders are placed. Note that the resulting installation may "
                "contain scripts and other resources which reference the "
                "Python interpreter of pip, and not that of ``--prefix``. "
                "See also the ``--python`` option if the intention is to "
                "install packages into another (possibly pip-free) "
                "environment."
            ),
        )

        self.cmd_opts.add_option(cmdoptions.src())

        self.cmd_opts.add_option(
            "-U",
            "--upgrade",
            dest="upgrade",
            action="store_true",
            help=(
                "Upgrade all specified packages to the newest available "
                "version. The handling of dependencies depends on the "
                "upgrade-strategy used."
            ),
        )

        self.cmd_opts.add_option(
            "--upgrade-strategy",
            dest="upgrade_strategy",
            default="only-if-needed",
            choices=["only-if-needed", "eager"],
            help=(
                "Determines how dependency upgrading should be handled "
                "[default: %default]. "
                '"eager" - dependencies are upgraded regardless of '
                "whether the currently installed version satisfies the "
                "requirements of the upgraded package(s). "
                '"only-if-needed" -  are upgraded only when they do not '
                "satisfy the requirements of the upgraded package(s)."
            ),
        )

        self.cmd_opts.add_option(
            "--force-reinstall",
            dest="force_reinstall",
            action="store_true",
            help="Reinstall all packages even if they are already up-to-date.",
        )

        self.cmd_opts.add_option(
            "-I",
            "--ignore-installed",
            dest="ignore_installed",
            action="store_true",
            help=(
                "Ignore the installed packages, overwriting them. "
                "This can break your system if the existing package "
                "is of a different version or was installed "
                "with a different package manager!"
            ),
        )

        self.cmd_opts.add_option(cmdoptions.ignore_requires_python())
        self.cmd_opts.add_option(cmdoptions.no_build_isolation())
        self.cmd_opts.add_option(cmdoptions.use_pep517())
        self.cmd_opts.add_option(cmdoptions.no_use_pep517())
        self.cmd_opts.add_option(cmdoptions.check_build_deps())
        self.cmd_opts.add_option(cmdoptions.override_externally_managed())

        self.cmd_opts.add_option(cmdoptions.config_settings())
        self.cmd_opts.add_option(cmdoptions.global_options())

        self.cmd_opts.add_option(
            "--compile",
            action="store_true",
            dest="compile",
            default=True,
            help="Compile Python source files to bytecode",
        )

        self.cmd_opts.add_option(
            "--no-compile",
            action="store_false",
            dest="compile",
            help="Do not compile Python source files to bytecode",
        )

        self.cmd_opts.add_option(
            "--no-warn-script-location",
            action="store_false",
            dest="warn_script_location",
            default=True,
            help="Do not warn when installing scripts outside PATH",
        )
        self.cmd_opts.add_option(
            "--no-warn-conflicts",
            action="store_false",
            dest="warn_about_conflicts",
            default=True,
            help="Do not warn about broken dependencies",
        )
        self.cmd_opts.add_option(cmdoptions.no_binary())
        self.cmd_opts.add_option(cmdoptions.only_binary())
        self.cmd_opts.add_option(cmdoptions.prefer_binary())
        self.cmd_opts.add_option(cmdoptions.require_hashes())
        self.cmd_opts.add_option(cmdoptions.progress_bar())
        self.cmd_opts.add_option(cmdoptions.root_user_action())

        index_opts = cmdoptions.make_option_group(
            cmdoptions.index_group,
            self.parser,
        )

        self.parser.insert_option_group(0, index_opts)
        self.parser.insert_option_group(0, self.cmd_opts)

        self.cmd_opts.add_option(
            "--report",
            dest="json_report_file",
            metavar="file",
            default=None,
            help=(
                "Generate a JSON file describing what pip did to install "
                "the provided requirements. "
                "Can be used in combination with --dry-run and --ignore-installed "
                "to 'resolve' the requirements. "
                "When - is used as file name it writes to stdout. "
                "When writing to stdout, please combine with the --quiet option "
                "to avoid mixing pip logging output with JSON output."
            ),
        )

    @with_cleanup
    def run(self, options: Values, args: list[str]) -> int:
        if options.use_user_site and options.target_dir is not None:
            raise CommandError("Can not combine '--user' and '--target'")

        # Check whether the environment we're installing into is externally
        # managed, as specified in PEP 668. Specifying --root, --target, or
        # --prefix disables the check, since there's no reliable way to locate
        # the EXTERNALLY-MANAGED file for those cases. An exception is also
        # made specifically for "--dry-run --report" for convenience.
        installing_into_current_environment = (
            not (options.dry_run and options.json_report_file)
            and options.root_path is None
            and options.target_dir is None
            and options.prefix_path is None
        )
        if (
            installing_into_current_environment
            and not options.override_externally_managed
        ):
            check_externally_managed()

        upgrade_strategy = "to-satisfy-only"
        if options.upgrade:
            upgrade_strategy = options.upgrade_strategy

        cmdoptions.check_dist_restriction(options, check_target=True)

        logger.verbose("Using %s", get_pip_version())
        options.use_user_site = decide_user_install(
            options.use_user_site,
            prefix_path=options.prefix_path,
            target_dir=options.target_dir,
            root_path=options.root_path,
            isolated_mode=options.isolated_mode,
        )

        target_temp_dir: TempDirectory | None = None
        target_temp_dir_path: str | None = None
        if options.target_dir:
            options.ignore_installed = True
            options.target_dir = os.path.abspath(options.target_dir)
            if (
                # fmt: off
                os.path.exists(options.target_dir) and
                not os.path.isdir(options.target_dir)
                # fmt: on
            ):
                raise CommandError(
                    "Target path exists but is not a directory, will not continue."
                )

            # Create a target directory for using with the target option
            target_temp_dir = TempDirectory(kind="target")
            target_temp_dir_path = target_temp_dir.path
            self.enter_context(target_temp_dir)

        global_options = options.global_options or []

        session = self.get_default_session(options)

        target_python = make_target_python(options)
        finder = self._build_package_finder(
            options=options,
            session=session,
            target_python=target_python,
            ignore_requires_python=options.ignore_requires_python,
        )
        build_tracker = self.enter_context(get_build_tracker())

        directory = TempDirectory(
            delete=not options.no_clean,
            kind="install",
            globally_managed=True,
        )

        try:
            reqs = self.get_requirements(args, options, finder, session)
            check_legacy_setup_py_options(options, reqs)

            wheel_cache = WheelCache(options.cache_dir)

            # Only when installing is it permitted to use PEP 660.
            # In other circumstances (pip wheel, pip download) we generate
            # regular (i.e. non editable) metadata and wheels.
            for req in reqs:
                req.permit_editable_wheels = True

            preparer = self.make_requirement_preparer(
                temp_build_dir=directory,
                options=options,
                build_tracker=build_tracker,
                session=session,
                finder=finder,
                use_user_site=options.use_user_site,
                verbosity=self.verbosity,
            )
            resolver = self.make_resolver(
                preparer=preparer,
                finder=finder,
                options=options,
                wheel_cache=wheel_cache,
                use_user_site=options.use_user_site,
                ignore_installed=options.ignore_installed,
                ignore_requires_python=options.ignore_requires_python,
                force_reinstall=options.force_reinstall,
                upgrade_strategy=upgrade_strategy,
                use_pep517=options.use_pep517,
                py_version_info=options.python_version,
            )

            self.trace_basic_info(finder)

            requirement_set = resolver.resolve(
                reqs, check_supported_wheels=not options.target_dir
            )

            if options.json_report_file:
                report = InstallationReport(requirement_set.requirements_to_install)
                if options.json_report_file == "-":
                    print_json(data=report.to_dict())
                else:
                    with open(options.json_report_file, "w", encoding="utf-8") as f:
                        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

            if options.dry_run:
                would_install_items = sorted(
                    (r.metadata["name"], r.metadata["version"])
                    for r in requirement_set.requirements_to_install
                )
                if would_install_items:
                    write_output(
                        "Would install %s",
                        " ".join("-".join(item) for item in would_install_items),
                    )
                return SUCCESS

            try:
                pip_req = requirement_set.get_requirement("pip")
            except KeyError:
                modifying_pip = False
            else:
                # If we're not replacing an already installed pip,
                # we're not modifying it.
                modifying_pip = pip_req.satisfied_by is None
            protect_pip_from_modification_on_windows(modifying_pip=modifying_pip)

            reqs_to_build = [
                r
                for r in requirement_set.requirements_to_install
                if should_build_for_install_command(r)
            ]

            _, build_failures = build(
                reqs_to_build,
                wheel_cache=wheel_cache,
                verify=True,
                build_options=[],
                global_options=global_options,
            )

            if build_failures:
                raise InstallWheelBuildError(build_failures)

            to_install = resolver.get_installation_order(requirement_set)

            # Check for conflicts in the package set we're installing.
            conflicts: ConflictDetails | None = None
            should_warn_about_conflicts = (
                not options.ignore_dependencies and options.warn_about_conflicts
            )
            if should_warn_about_conflicts:
                conflicts = self._determine_conflicts(to_install)

            # Don't warn about script install locations if
            # --target or --prefix has been specified
            warn_script_location = options.warn_script_location
            if options.target_dir or options.prefix_path:
                warn_script_location = False

            installed = install_given_reqs(
                to_install,
                global_options,
                root=options.root_path,
                home=target_temp_dir_path,
                prefix=options.prefix_path,
                warn_script_location=warn_script_location,
                use_user_site=options.use_user_site,
                pycompile=options.compile,
                progress_bar=options.progress_bar,
            )

            lib_locations = get_lib_location_guesses(
                user=options.use_user_site,
                home=target_temp_dir_path,
                root=options.root_path,
                prefix=options.prefix_path,
                isolated=options.isolated_mode,
            )
            env = get_environment(lib_locations)

            # Display a summary of installed packages, with extra care to
            # display a package name as it was requested by the user.
            installed.sort(key=operator.attrgetter("name"))
            summary = []
            installed_versions = {}
            for distribution in env.iter_all_distributions():
                installed_versions[distribution.canonical_name] = distribution.version
            for package in installed:
                display_name = package.name
                version = installed_versions.get(canonicalize_name(display_name), None)
                if version:
                    text = f"{display_name}-{version}"
                else:
                    text = display_name
                summary.append(text)

            if conflicts is not None:
                self._warn_about_conflicts(
                    conflicts,
                    resolver_variant=self.determine_resolver_variant(options),
                )

            installed_desc = " ".join(summary)
            if installed_desc:
                write_output(
                    "Successfully installed %s",
                    installed_desc,
                )
        except OSError as error:
            show_traceback = self.verbosity >= 1

            message = create_os_error_message(
                error,
                show_traceback,
                options.use_user_site,
            )
            logger.error(message, exc_info=show_traceback)

            return ERROR

        if options.target_dir:
            assert target_temp_dir
            self._handle_target_dir(
                options.target_dir, target_temp_dir, options.upgrade
            )
        if options.root_user_action == "warn":
            warn_if_run_as_root()
        return SUCCESS

    def _handle_target_dir(
        self, target_dir: str, target_temp_dir: TempDirectory, upgrade: bool
    ) -> None:
        ensure_dir(target_dir)

        # Checking both purelib and platlib directories for installed
        # packages to be moved to target directory
        lib_dir_list = []

        # Checking both purelib and platlib directories for installed
        # packages to be moved to target directory
        scheme = get_scheme("", home=target_temp_dir.path)
        purelib_dir = scheme.purelib
        platlib_dir = scheme.platlib
        data_dir = scheme.data

        if os.path.exists(purelib_dir):
            lib_dir_list.append(purelib_dir)
        if os.path.exists(platlib_dir) and platlib_dir != purelib_dir:
            lib_dir_list.append(platlib_dir)
        if os.path.exists(data_dir):
            lib_dir_list.append(data_dir)

        for lib_dir in lib_dir_list:
            for item in os.listdir(lib_dir):
                if lib_dir == data_dir:
                    ddir = os.path.join(data_dir, item)
                    if any(s.startswith(ddir) for s in lib_dir_list[:-1]):
                        continue
                target_item_dir = os.path.join(target_dir, item)
                if os.path.exists(target_item_dir):
                    if not upgrade:
                        logger.warning(
                            "Target directory %s already exists. Specify "
                            "--upgrade to force replacement.",
                            target_item_dir,
                        )
                        continue
                    if os.path.islink(target_item_dir):
                        logger.warning(
                            "Target directory %s already exists and is "
                            "a link. pip will not automatically replace "
                            "links, please remove if replacement is "
                            "desired.",
                            target_item_dir,
                        )
                        continue
                    if os.path.isdir(target_item_dir):
                        shutil.rmtree(target_item_dir)
                    else:
                        os.remove(target_item_dir)

                shutil.move(os.path.join(lib_dir, item), target_item_dir)

    def _determine_conflicts(
        self, to_install: list[InstallRequirement]
    ) -> ConflictDetails | None:
        try:
            return check_install_conflicts(to_install)
        except Exception:
            logger.exception(
                "Error while checking for conflicts. Please file an issue on "
                "pip's issue tracker: https://github.com/pypa/pip/issues/new"
            )
            return None

    def _warn_about_conflicts(
        self, conflict_details: ConflictDetails, resolver_variant: str
    ) -> None:
        package_set, (missing, conflicting) = conflict_details
        if not missing and not conflicting:
            return

        parts: list[str] = []
        if resolver_variant == "legacy":
            parts.append(
                "pip's legacy dependency resolver does not consider dependency "
                "conflicts when selecting packages. This behaviour is the "
                "source of the following dependency conflicts."
            )
        else:
            assert resolver_variant == "resolvelib"
            parts.append(
                "pip's dependency resolver does not currently take into account "
                "all the packages that are installed. This behaviour is the "
                "source of the following dependency conflicts."
            )

        # NOTE: There is some duplication here, with commands/check.py
        for project_name in missing:
            version = package_set[project_name][0]
            for dependency in missing[project_name]:
                message = (
                    f"{project_name} {version} requires {dependency[1]}, "
                    "which is not installed."
                )
                parts.append(message)

        for project_name in conflicting:
            version = package_set[project_name][0]
            for dep_name, dep_version, req in conflicting[project_name]:
                message = (
                    "{name} {version} requires {requirement}, but {you} have "
                    "{dep_name} {dep_version} which is incompatible."
                ).format(
                    name=project_name,
                    version=version,
                    requirement=req,
                    dep_name=dep_name,
                    dep_version=dep_version,
                    you=("you" if resolver_variant == "resolvelib" else "you'll"),
                )
                parts.append(message)

        logger.critical("\n".join(parts))


def get_lib_location_guesses(
    user: bool = False,
    home: str | None = None,
    root: str | None = None,
    isolated: bool = False,
    prefix: str | None = None,
) -> list[str]:
    scheme = get_scheme(
        "",
        user=user,
        home=home,
        root=root,
        isolated=isolated,
        prefix=prefix,
    )
    return [scheme.purelib, scheme.platlib]


def site_packages_writable(root: str | None, isolated: bool) -> bool:
    return all(
        test_writable_dir(d)
        for d in set(get_lib_location_guesses(root=root, isolated=isolated))
    )


def decide_user_install(
    use_user_site: bool | None,
    prefix_path: str | None = None,
    target_dir: str | None = None,
    root_path: str | None = None,
    isolated_mode: bool = False,
) -> bool:
    """Determine whether to do a user install based on the input options.

    If use_user_site is False, no additional checks are done.
    If use_user_site is True, it is checked for compatibility with other
    options.
    If use_user_site is None, the default behaviour depends on the environment,
    which is provided by the other arguments.
    """
    # In some cases (config from tox), use_user_site can be set to an integer
    # rather than a bool, which 'use_user_site is False' wouldn't catch.
    if (use_user_site is not None) and (not use_user_site):
        logger.debug("Non-user install by explicit request")
        return False

    if use_user_site:
        if prefix_path:
            raise CommandError(
                "Can not combine '--user' and '--prefix' as they imply "
                "different installation locations"
            )
        if virtualenv_no_global():
            raise InstallationError(
                "Can not perform a '--user' install. User site-packages "
                "are not visible in this virtualenv."
            )
        logger.debug("User install by explicit request")
        return True

    # If we are here, user installs have not been explicitly requested/avoided
    assert use_user_site is None

    # user install incompatible with --prefix/--target
    if prefix_path or target_dir:
        logger.debug("Non-user install due to --prefix or --target option")
        return False

    # If user installs are not enabled, choose a non-user install
    if not site.ENABLE_USER_SITE:
        logger.debug("Non-user install because user site-packages disabled")
        return False

    # If we have permission for a non-user install, do that,
    # otherwise do a user install.
    if site_packages_writable(root=root_path, isolated=isolated_mode):
        logger.debug("Non-user install because site-packages writeable")
        return False

    logger.info(
        "Defaulting to user installation because normal site-packages "
        "is not writeable"
    )
    return True


def create_os_error_message(
    error: OSError, show_traceback: bool, using_user_site: bool
) -> str:
    """Format an error message for an OSError

    It may occur anytime during the execution of the install command.
    """
    parts = []

    # Mention the error if we are not going to show a traceback
    parts.append("Could not install packages due to an OSError")
    if not show_traceback:
        parts.append(": ")
        parts.append(str(error))
    else:
        parts.append(".")

    # Spilt the error indication from a helper message (if any)
    parts[-1] += "\n"

    # Suggest useful actions to the user:
    #  (1) using user site-packages or (2) verifying the permissions
    if error.errno == errno.EACCES:
        user_option_part = "Consider using the `--user` option"
        permissions_part = "Check the permissions"

        if not running_under_virtualenv() and not using_user_site:
            parts.extend(
                [
                    user_option_part,
                    " or ",
                    permissions_part.lower(),
                ]
            )
        else:
            parts.append(permissions_part)
        parts.append(".\n")

    # Suggest to check "pip config debug" in case of invalid proxy
    if type(error) is InvalidProxyURL:
        parts.append(
            'Consider checking your local proxy configuration with "pip config debug"'
        )
        parts.append(".\n")

    # On Windows, errors like EINVAL or ENOENT may occur
    # if a file or folder name exceeds 255 characters,
    # or if the full path exceeds 260 characters and long path support isn't enabled.
    # This condition checks for such cases and adds a hint to the error output.

    if WINDOWS and error.errno in (errno.EINVAL, errno.ENOENT) and error.filename:
        if any(len(part) > 255 for part in Path(error.filename).parts):
            parts.append(
                "HINT: This error might be caused by a file or folder name exceeding "
                "255 characters, which is a Windows limitation even if long paths "
                "are enabled.\n "
            )
        if len(error.filename) > 260:
            parts.append(
                "HINT: This error might have occurred since "
                "this system does not have Windows Long Path "
                "support enabled. You can find information on "
                "how to enable this at "
                "https://pip.pypa.io/warnings/enable-long-paths\n"
            )
    return "".join(parts).strip() + "\n"

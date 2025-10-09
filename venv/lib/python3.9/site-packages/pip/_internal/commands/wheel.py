import logging
import os
import shutil
from optparse import Values

from pip._internal.cache import WheelCache
from pip._internal.cli import cmdoptions
from pip._internal.cli.req_command import RequirementCommand, with_cleanup
from pip._internal.cli.status_codes import SUCCESS
from pip._internal.exceptions import CommandError
from pip._internal.operations.build.build_tracker import get_build_tracker
from pip._internal.req.req_install import (
    InstallRequirement,
    check_legacy_setup_py_options,
)
from pip._internal.utils.misc import ensure_dir, normalize_path
from pip._internal.utils.temp_dir import TempDirectory
from pip._internal.wheel_builder import build

logger = logging.getLogger(__name__)


class WheelCommand(RequirementCommand):
    """
    Build Wheel archives for your requirements and dependencies.

    Wheel is a built-package format, and offers the advantage of not
    recompiling your software during every install. For more details, see the
    wheel docs: https://wheel.readthedocs.io/en/latest/

    'pip wheel' uses the build system interface as described here:
    https://pip.pypa.io/en/stable/reference/build-system/

    """

    usage = """
      %prog [options] <requirement specifier> ...
      %prog [options] -r <requirements file> ...
      %prog [options] [-e] <vcs project url> ...
      %prog [options] [-e] <local project path> ...
      %prog [options] <archive url/path> ..."""

    def add_options(self) -> None:
        self.cmd_opts.add_option(
            "-w",
            "--wheel-dir",
            dest="wheel_dir",
            metavar="dir",
            default=os.curdir,
            help=(
                "Build wheels into <dir>, where the default is the "
                "current working directory."
            ),
        )
        self.cmd_opts.add_option(cmdoptions.no_binary())
        self.cmd_opts.add_option(cmdoptions.only_binary())
        self.cmd_opts.add_option(cmdoptions.prefer_binary())
        self.cmd_opts.add_option(cmdoptions.no_build_isolation())
        self.cmd_opts.add_option(cmdoptions.use_pep517())
        self.cmd_opts.add_option(cmdoptions.no_use_pep517())
        self.cmd_opts.add_option(cmdoptions.check_build_deps())
        self.cmd_opts.add_option(cmdoptions.constraints())
        self.cmd_opts.add_option(cmdoptions.editable())
        self.cmd_opts.add_option(cmdoptions.requirements())
        self.cmd_opts.add_option(cmdoptions.src())
        self.cmd_opts.add_option(cmdoptions.ignore_requires_python())
        self.cmd_opts.add_option(cmdoptions.no_deps())
        self.cmd_opts.add_option(cmdoptions.progress_bar())

        self.cmd_opts.add_option(
            "--no-verify",
            dest="no_verify",
            action="store_true",
            default=False,
            help="Don't verify if built wheel is valid.",
        )

        self.cmd_opts.add_option(cmdoptions.config_settings())
        self.cmd_opts.add_option(cmdoptions.build_options())
        self.cmd_opts.add_option(cmdoptions.global_options())

        self.cmd_opts.add_option(
            "--pre",
            action="store_true",
            default=False,
            help=(
                "Include pre-release and development versions. By default, "
                "pip only finds stable versions."
            ),
        )

        self.cmd_opts.add_option(cmdoptions.require_hashes())

        index_opts = cmdoptions.make_option_group(
            cmdoptions.index_group,
            self.parser,
        )

        self.parser.insert_option_group(0, index_opts)
        self.parser.insert_option_group(0, self.cmd_opts)

    @with_cleanup
    def run(self, options: Values, args: list[str]) -> int:
        session = self.get_default_session(options)

        finder = self._build_package_finder(options, session)

        options.wheel_dir = normalize_path(options.wheel_dir)
        ensure_dir(options.wheel_dir)

        build_tracker = self.enter_context(get_build_tracker())

        directory = TempDirectory(
            delete=not options.no_clean,
            kind="wheel",
            globally_managed=True,
        )

        reqs = self.get_requirements(args, options, finder, session)
        check_legacy_setup_py_options(options, reqs)

        wheel_cache = WheelCache(options.cache_dir)

        preparer = self.make_requirement_preparer(
            temp_build_dir=directory,
            options=options,
            build_tracker=build_tracker,
            session=session,
            finder=finder,
            download_dir=options.wheel_dir,
            use_user_site=False,
            verbosity=self.verbosity,
        )

        resolver = self.make_resolver(
            preparer=preparer,
            finder=finder,
            options=options,
            wheel_cache=wheel_cache,
            ignore_requires_python=options.ignore_requires_python,
            use_pep517=options.use_pep517,
        )

        self.trace_basic_info(finder)

        requirement_set = resolver.resolve(reqs, check_supported_wheels=True)

        reqs_to_build: list[InstallRequirement] = []
        for req in requirement_set.requirements.values():
            if req.is_wheel:
                preparer.save_linked_requirement(req)
            else:
                reqs_to_build.append(req)

        preparer.prepare_linked_requirements_more(requirement_set.requirements.values())

        # build wheels
        build_successes, build_failures = build(
            reqs_to_build,
            wheel_cache=wheel_cache,
            verify=(not options.no_verify),
            build_options=options.build_options or [],
            global_options=options.global_options or [],
        )
        for req in build_successes:
            assert req.link and req.link.is_wheel
            assert req.local_file_path
            # copy from cache to target directory
            try:
                shutil.copy(req.local_file_path, options.wheel_dir)
            except OSError as e:
                logger.warning(
                    "Building wheel for %s failed: %s",
                    req.name,
                    e,
                )
                build_failures.append(req)
        if len(build_failures) != 0:
            raise CommandError("Failed to build one or more wheels")

        return SUCCESS

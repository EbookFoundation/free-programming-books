import sys
from optparse import Values
from pathlib import Path

from pip._internal.cache import WheelCache
from pip._internal.cli import cmdoptions
from pip._internal.cli.req_command import (
    RequirementCommand,
    with_cleanup,
)
from pip._internal.cli.status_codes import SUCCESS
from pip._internal.models.pylock import Pylock, is_valid_pylock_file_name
from pip._internal.operations.build.build_tracker import get_build_tracker
from pip._internal.req.req_install import (
    check_legacy_setup_py_options,
)
from pip._internal.utils.logging import getLogger
from pip._internal.utils.misc import (
    get_pip_version,
)
from pip._internal.utils.temp_dir import TempDirectory

logger = getLogger(__name__)


class LockCommand(RequirementCommand):
    """
    EXPERIMENTAL - Lock packages and their dependencies from:

    - PyPI (and other indexes) using requirement specifiers.
    - VCS project urls.
    - Local project directories.
    - Local or remote source archives.

    pip also supports locking from "requirements files", which provide an easy
    way to specify a whole environment to be installed.

    The generated lock file is only guaranteed to be valid for the current
    python version and platform.
    """

    usage = """
      %prog [options] [-e] <local project path> ...
      %prog [options] <requirement specifier> [package-index-options] ...
      %prog [options] -r <requirements file> [package-index-options] ...
      %prog [options] <archive url/path> ..."""

    def add_options(self) -> None:
        self.cmd_opts.add_option(
            cmdoptions.PipOption(
                "--output",
                "-o",
                dest="output_file",
                metavar="path",
                type="path",
                default="pylock.toml",
                help="Lock file name (default=pylock.toml). Use - for stdout.",
            )
        )
        self.cmd_opts.add_option(cmdoptions.requirements())
        self.cmd_opts.add_option(cmdoptions.constraints())
        self.cmd_opts.add_option(cmdoptions.no_deps())
        self.cmd_opts.add_option(cmdoptions.pre())

        self.cmd_opts.add_option(cmdoptions.editable())

        self.cmd_opts.add_option(cmdoptions.src())

        self.cmd_opts.add_option(cmdoptions.ignore_requires_python())
        self.cmd_opts.add_option(cmdoptions.no_build_isolation())
        self.cmd_opts.add_option(cmdoptions.use_pep517())
        self.cmd_opts.add_option(cmdoptions.no_use_pep517())
        self.cmd_opts.add_option(cmdoptions.check_build_deps())

        self.cmd_opts.add_option(cmdoptions.config_settings())

        self.cmd_opts.add_option(cmdoptions.no_binary())
        self.cmd_opts.add_option(cmdoptions.only_binary())
        self.cmd_opts.add_option(cmdoptions.prefer_binary())
        self.cmd_opts.add_option(cmdoptions.require_hashes())
        self.cmd_opts.add_option(cmdoptions.progress_bar())

        index_opts = cmdoptions.make_option_group(
            cmdoptions.index_group,
            self.parser,
        )

        self.parser.insert_option_group(0, index_opts)
        self.parser.insert_option_group(0, self.cmd_opts)

    @with_cleanup
    def run(self, options: Values, args: list[str]) -> int:
        logger.verbose("Using %s", get_pip_version())

        logger.warning(
            "pip lock is currently an experimental command. "
            "It may be removed/changed in a future release "
            "without prior warning."
        )

        session = self.get_default_session(options)

        finder = self._build_package_finder(
            options=options,
            session=session,
            ignore_requires_python=options.ignore_requires_python,
        )
        build_tracker = self.enter_context(get_build_tracker())

        directory = TempDirectory(
            delete=not options.no_clean,
            kind="install",
            globally_managed=True,
        )

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
            use_user_site=False,
            verbosity=self.verbosity,
        )
        resolver = self.make_resolver(
            preparer=preparer,
            finder=finder,
            options=options,
            wheel_cache=wheel_cache,
            use_user_site=False,
            ignore_installed=True,
            ignore_requires_python=options.ignore_requires_python,
            upgrade_strategy="to-satisfy-only",
            use_pep517=options.use_pep517,
        )

        self.trace_basic_info(finder)

        requirement_set = resolver.resolve(reqs, check_supported_wheels=True)

        if options.output_file == "-":
            base_dir = Path.cwd()
        else:
            output_file_path = Path(options.output_file)
            if not is_valid_pylock_file_name(output_file_path):
                logger.warning(
                    "%s is not a valid lock file name.",
                    output_file_path,
                )
            base_dir = output_file_path.parent
        pylock_toml = Pylock.from_install_requirements(
            requirement_set.requirements.values(), base_dir=base_dir
        ).as_toml()
        if options.output_file == "-":
            sys.stdout.write(pylock_toml)
        else:
            output_file_path.write_text(pylock_toml, encoding="utf-8")

        return SUCCESS

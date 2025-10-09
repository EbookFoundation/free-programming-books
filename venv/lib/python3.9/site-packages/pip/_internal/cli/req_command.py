"""Contains the RequirementCommand base class.

This class is in a separate module so the commands that do not always
need PackageFinder capability don't unnecessarily import the
PackageFinder machinery and all its vendored dependencies, etc.
"""

from __future__ import annotations

import logging
from functools import partial
from optparse import Values
from typing import Any

from pip._internal.build_env import SubprocessBuildEnvironmentInstaller
from pip._internal.cache import WheelCache
from pip._internal.cli import cmdoptions
from pip._internal.cli.index_command import IndexGroupCommand
from pip._internal.cli.index_command import SessionCommandMixin as SessionCommandMixin
from pip._internal.exceptions import CommandError, PreviousBuildDirError
from pip._internal.index.collector import LinkCollector
from pip._internal.index.package_finder import PackageFinder
from pip._internal.models.selection_prefs import SelectionPreferences
from pip._internal.models.target_python import TargetPython
from pip._internal.network.session import PipSession
from pip._internal.operations.build.build_tracker import BuildTracker
from pip._internal.operations.prepare import RequirementPreparer
from pip._internal.req.constructors import (
    install_req_from_editable,
    install_req_from_line,
    install_req_from_parsed_requirement,
    install_req_from_req_string,
)
from pip._internal.req.req_dependency_group import parse_dependency_groups
from pip._internal.req.req_file import parse_requirements
from pip._internal.req.req_install import InstallRequirement
from pip._internal.resolution.base import BaseResolver
from pip._internal.utils.temp_dir import (
    TempDirectory,
    TempDirectoryTypeRegistry,
    tempdir_kinds,
)

logger = logging.getLogger(__name__)


KEEPABLE_TEMPDIR_TYPES = [
    tempdir_kinds.BUILD_ENV,
    tempdir_kinds.EPHEM_WHEEL_CACHE,
    tempdir_kinds.REQ_BUILD,
]


def with_cleanup(func: Any) -> Any:
    """Decorator for common logic related to managing temporary
    directories.
    """

    def configure_tempdir_registry(registry: TempDirectoryTypeRegistry) -> None:
        for t in KEEPABLE_TEMPDIR_TYPES:
            registry.set_delete(t, False)

    def wrapper(
        self: RequirementCommand, options: Values, args: list[Any]
    ) -> int | None:
        assert self.tempdir_registry is not None
        if options.no_clean:
            configure_tempdir_registry(self.tempdir_registry)

        try:
            return func(self, options, args)
        except PreviousBuildDirError:
            # This kind of conflict can occur when the user passes an explicit
            # build directory with a pre-existing folder. In that case we do
            # not want to accidentally remove it.
            configure_tempdir_registry(self.tempdir_registry)
            raise

    return wrapper


class RequirementCommand(IndexGroupCommand):
    def __init__(self, *args: Any, **kw: Any) -> None:
        super().__init__(*args, **kw)

        self.cmd_opts.add_option(cmdoptions.dependency_groups())
        self.cmd_opts.add_option(cmdoptions.no_clean())

    @staticmethod
    def determine_resolver_variant(options: Values) -> str:
        """Determines which resolver should be used, based on the given options."""
        if "legacy-resolver" in options.deprecated_features_enabled:
            return "legacy"

        return "resolvelib"

    @classmethod
    def make_requirement_preparer(
        cls,
        temp_build_dir: TempDirectory,
        options: Values,
        build_tracker: BuildTracker,
        session: PipSession,
        finder: PackageFinder,
        use_user_site: bool,
        download_dir: str | None = None,
        verbosity: int = 0,
    ) -> RequirementPreparer:
        """
        Create a RequirementPreparer instance for the given parameters.
        """
        temp_build_dir_path = temp_build_dir.path
        assert temp_build_dir_path is not None
        legacy_resolver = False

        resolver_variant = cls.determine_resolver_variant(options)
        if resolver_variant == "resolvelib":
            lazy_wheel = "fast-deps" in options.features_enabled
            if lazy_wheel:
                logger.warning(
                    "pip is using lazily downloaded wheels using HTTP "
                    "range requests to obtain dependency information. "
                    "This experimental feature is enabled through "
                    "--use-feature=fast-deps and it is not ready for "
                    "production."
                )
        else:
            legacy_resolver = True
            lazy_wheel = False
            if "fast-deps" in options.features_enabled:
                logger.warning(
                    "fast-deps has no effect when used with the legacy resolver."
                )

        return RequirementPreparer(
            build_dir=temp_build_dir_path,
            src_dir=options.src_dir,
            download_dir=download_dir,
            build_isolation=options.build_isolation,
            build_isolation_installer=SubprocessBuildEnvironmentInstaller(finder),
            check_build_deps=options.check_build_deps,
            build_tracker=build_tracker,
            session=session,
            progress_bar=options.progress_bar,
            finder=finder,
            require_hashes=options.require_hashes,
            use_user_site=use_user_site,
            lazy_wheel=lazy_wheel,
            verbosity=verbosity,
            legacy_resolver=legacy_resolver,
            resume_retries=options.resume_retries,
        )

    @classmethod
    def make_resolver(
        cls,
        preparer: RequirementPreparer,
        finder: PackageFinder,
        options: Values,
        wheel_cache: WheelCache | None = None,
        use_user_site: bool = False,
        ignore_installed: bool = True,
        ignore_requires_python: bool = False,
        force_reinstall: bool = False,
        upgrade_strategy: str = "to-satisfy-only",
        use_pep517: bool | None = None,
        py_version_info: tuple[int, ...] | None = None,
    ) -> BaseResolver:
        """
        Create a Resolver instance for the given parameters.
        """
        make_install_req = partial(
            install_req_from_req_string,
            isolated=options.isolated_mode,
            use_pep517=use_pep517,
        )
        resolver_variant = cls.determine_resolver_variant(options)
        # The long import name and duplicated invocation is needed to convince
        # Mypy into correctly typechecking. Otherwise it would complain the
        # "Resolver" class being redefined.
        if resolver_variant == "resolvelib":
            import pip._internal.resolution.resolvelib.resolver

            return pip._internal.resolution.resolvelib.resolver.Resolver(
                preparer=preparer,
                finder=finder,
                wheel_cache=wheel_cache,
                make_install_req=make_install_req,
                use_user_site=use_user_site,
                ignore_dependencies=options.ignore_dependencies,
                ignore_installed=ignore_installed,
                ignore_requires_python=ignore_requires_python,
                force_reinstall=force_reinstall,
                upgrade_strategy=upgrade_strategy,
                py_version_info=py_version_info,
            )
        import pip._internal.resolution.legacy.resolver

        return pip._internal.resolution.legacy.resolver.Resolver(
            preparer=preparer,
            finder=finder,
            wheel_cache=wheel_cache,
            make_install_req=make_install_req,
            use_user_site=use_user_site,
            ignore_dependencies=options.ignore_dependencies,
            ignore_installed=ignore_installed,
            ignore_requires_python=ignore_requires_python,
            force_reinstall=force_reinstall,
            upgrade_strategy=upgrade_strategy,
            py_version_info=py_version_info,
        )

    def get_requirements(
        self,
        args: list[str],
        options: Values,
        finder: PackageFinder,
        session: PipSession,
    ) -> list[InstallRequirement]:
        """
        Parse command-line arguments into the corresponding requirements.
        """
        requirements: list[InstallRequirement] = []
        for filename in options.constraints:
            for parsed_req in parse_requirements(
                filename,
                constraint=True,
                finder=finder,
                options=options,
                session=session,
            ):
                req_to_add = install_req_from_parsed_requirement(
                    parsed_req,
                    isolated=options.isolated_mode,
                    user_supplied=False,
                )
                requirements.append(req_to_add)

        for req in args:
            req_to_add = install_req_from_line(
                req,
                comes_from=None,
                isolated=options.isolated_mode,
                use_pep517=options.use_pep517,
                user_supplied=True,
                config_settings=getattr(options, "config_settings", None),
            )
            requirements.append(req_to_add)

        if options.dependency_groups:
            for req in parse_dependency_groups(options.dependency_groups):
                req_to_add = install_req_from_req_string(
                    req,
                    isolated=options.isolated_mode,
                    use_pep517=options.use_pep517,
                    user_supplied=True,
                )
                requirements.append(req_to_add)

        for req in options.editables:
            req_to_add = install_req_from_editable(
                req,
                user_supplied=True,
                isolated=options.isolated_mode,
                use_pep517=options.use_pep517,
                config_settings=getattr(options, "config_settings", None),
            )
            requirements.append(req_to_add)

        # NOTE: options.require_hashes may be set if --require-hashes is True
        for filename in options.requirements:
            for parsed_req in parse_requirements(
                filename, finder=finder, options=options, session=session
            ):
                req_to_add = install_req_from_parsed_requirement(
                    parsed_req,
                    isolated=options.isolated_mode,
                    use_pep517=options.use_pep517,
                    user_supplied=True,
                    config_settings=(
                        parsed_req.options.get("config_settings")
                        if parsed_req.options
                        else None
                    ),
                )
                requirements.append(req_to_add)

        # If any requirement has hash options, enable hash checking.
        if any(req.has_hash_options for req in requirements):
            options.require_hashes = True

        if not (
            args
            or options.editables
            or options.requirements
            or options.dependency_groups
        ):
            opts = {"name": self.name}
            if options.find_links:
                raise CommandError(
                    "You must give at least one requirement to {name} "
                    '(maybe you meant "pip {name} {links}"?)'.format(
                        **dict(opts, links=" ".join(options.find_links))
                    )
                )
            else:
                raise CommandError(
                    "You must give at least one requirement to {name} "
                    '(see "pip help {name}")'.format(**opts)
                )

        return requirements

    @staticmethod
    def trace_basic_info(finder: PackageFinder) -> None:
        """
        Trace basic information about the provided objects.
        """
        # Display where finder is looking for packages
        search_scope = finder.search_scope
        locations = search_scope.get_formatted_locations()
        if locations:
            logger.info(locations)

    def _build_package_finder(
        self,
        options: Values,
        session: PipSession,
        target_python: TargetPython | None = None,
        ignore_requires_python: bool | None = None,
    ) -> PackageFinder:
        """
        Create a package finder appropriate to this requirement command.

        :param ignore_requires_python: Whether to ignore incompatible
            "Requires-Python" values in links. Defaults to False.
        """
        link_collector = LinkCollector.create(session, options=options)
        selection_prefs = SelectionPreferences(
            allow_yanked=True,
            format_control=options.format_control,
            allow_all_prereleases=options.pre,
            prefer_binary=options.prefer_binary,
            ignore_requires_python=ignore_requires_python,
        )

        return PackageFinder.create(
            link_collector=link_collector,
            selection_prefs=selection_prefs,
            target_python=target_python,
        )

from __future__ import annotations

import configparser
import logging
import os

from pip._internal.exceptions import BadCommand, InstallationError
from pip._internal.utils.misc import HiddenText, display_path
from pip._internal.utils.subprocess import make_command
from pip._internal.utils.urls import path_to_url
from pip._internal.vcs.versioncontrol import (
    RevOptions,
    VersionControl,
    find_path_to_project_root_from_repo_root,
    vcs,
)

logger = logging.getLogger(__name__)


class Mercurial(VersionControl):
    name = "hg"
    dirname = ".hg"
    repo_name = "clone"
    schemes = (
        "hg+file",
        "hg+http",
        "hg+https",
        "hg+ssh",
        "hg+static-http",
    )

    @staticmethod
    def get_base_rev_args(rev: str) -> list[str]:
        return [f"--rev={rev}"]

    def fetch_new(
        self, dest: str, url: HiddenText, rev_options: RevOptions, verbosity: int
    ) -> None:
        rev_display = rev_options.to_display()
        logger.info(
            "Cloning hg %s%s to %s",
            url,
            rev_display,
            display_path(dest),
        )
        if verbosity <= 0:
            flags: tuple[str, ...] = ("--quiet",)
        elif verbosity == 1:
            flags = ()
        elif verbosity == 2:
            flags = ("--verbose",)
        else:
            flags = ("--verbose", "--debug")
        self.run_command(make_command("clone", "--noupdate", *flags, url, dest))
        self.run_command(
            make_command("update", *flags, rev_options.to_args()),
            cwd=dest,
        )

    def switch(
        self,
        dest: str,
        url: HiddenText,
        rev_options: RevOptions,
        verbosity: int = 0,
    ) -> None:
        extra_flags = []
        repo_config = os.path.join(dest, self.dirname, "hgrc")
        config = configparser.RawConfigParser()

        if verbosity <= 0:
            extra_flags.append("-q")

        try:
            config.read(repo_config)
            config.set("paths", "default", url.secret)
            with open(repo_config, "w") as config_file:
                config.write(config_file)
        except (OSError, configparser.NoSectionError) as exc:
            logger.warning("Could not switch Mercurial repository to %s: %s", url, exc)
        else:
            cmd_args = make_command("update", *extra_flags, rev_options.to_args())
            self.run_command(cmd_args, cwd=dest)

    def update(
        self,
        dest: str,
        url: HiddenText,
        rev_options: RevOptions,
        verbosity: int = 0,
    ) -> None:
        extra_flags = []

        if verbosity <= 0:
            extra_flags.append("-q")

        self.run_command(["pull", *extra_flags], cwd=dest)
        cmd_args = make_command("update", *extra_flags, rev_options.to_args())
        self.run_command(cmd_args, cwd=dest)

    @classmethod
    def get_remote_url(cls, location: str) -> str:
        url = cls.run_command(
            ["showconfig", "paths.default"],
            show_stdout=False,
            stdout_only=True,
            cwd=location,
        ).strip()
        if cls._is_local_repository(url):
            url = path_to_url(url)
        return url.strip()

    @classmethod
    def get_revision(cls, location: str) -> str:
        """
        Return the repository-local changeset revision number, as an integer.
        """
        current_revision = cls.run_command(
            ["parents", "--template={rev}"],
            show_stdout=False,
            stdout_only=True,
            cwd=location,
        ).strip()
        return current_revision

    @classmethod
    def get_requirement_revision(cls, location: str) -> str:
        """
        Return the changeset identification hash, as a 40-character
        hexadecimal string
        """
        current_rev_hash = cls.run_command(
            ["parents", "--template={node}"],
            show_stdout=False,
            stdout_only=True,
            cwd=location,
        ).strip()
        return current_rev_hash

    @classmethod
    def is_commit_id_equal(cls, dest: str, name: str | None) -> bool:
        """Always assume the versions don't match"""
        return False

    @classmethod
    def get_subdirectory(cls, location: str) -> str | None:
        """
        Return the path to Python project root, relative to the repo root.
        Return None if the project root is in the repo root.
        """
        # find the repo root
        repo_root = cls.run_command(
            ["root"], show_stdout=False, stdout_only=True, cwd=location
        ).strip()
        if not os.path.isabs(repo_root):
            repo_root = os.path.abspath(os.path.join(location, repo_root))
        return find_path_to_project_root_from_repo_root(location, repo_root)

    @classmethod
    def get_repository_root(cls, location: str) -> str | None:
        loc = super().get_repository_root(location)
        if loc:
            return loc
        try:
            r = cls.run_command(
                ["root"],
                cwd=location,
                show_stdout=False,
                stdout_only=True,
                on_returncode="raise",
                log_failed_cmd=False,
            )
        except BadCommand:
            logger.debug(
                "could not determine if %s is under hg control "
                "because hg is not available",
                location,
            )
            return None
        except InstallationError:
            return None
        return os.path.normpath(r.rstrip("\r\n"))


vcs.register(Mercurial)

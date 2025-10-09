from __future__ import annotations

import logging

from pip._internal.utils.misc import HiddenText, display_path
from pip._internal.utils.subprocess import make_command
from pip._internal.utils.urls import path_to_url
from pip._internal.vcs.versioncontrol import (
    AuthInfo,
    RemoteNotFoundError,
    RevOptions,
    VersionControl,
    vcs,
)

logger = logging.getLogger(__name__)


class Bazaar(VersionControl):
    name = "bzr"
    dirname = ".bzr"
    repo_name = "branch"
    schemes = (
        "bzr+http",
        "bzr+https",
        "bzr+ssh",
        "bzr+sftp",
        "bzr+ftp",
        "bzr+lp",
        "bzr+file",
    )

    @staticmethod
    def get_base_rev_args(rev: str) -> list[str]:
        return ["-r", rev]

    def fetch_new(
        self, dest: str, url: HiddenText, rev_options: RevOptions, verbosity: int
    ) -> None:
        rev_display = rev_options.to_display()
        logger.info(
            "Checking out %s%s to %s",
            url,
            rev_display,
            display_path(dest),
        )
        if verbosity <= 0:
            flags = ["--quiet"]
        elif verbosity == 1:
            flags = []
        else:
            flags = [f"-{'v'*verbosity}"]
        cmd_args = make_command(
            "checkout", "--lightweight", *flags, rev_options.to_args(), url, dest
        )
        self.run_command(cmd_args)

    def switch(
        self,
        dest: str,
        url: HiddenText,
        rev_options: RevOptions,
        verbosity: int = 0,
    ) -> None:
        self.run_command(make_command("switch", url), cwd=dest)

    def update(
        self,
        dest: str,
        url: HiddenText,
        rev_options: RevOptions,
        verbosity: int = 0,
    ) -> None:
        flags = []

        if verbosity <= 0:
            flags.append("-q")

        output = self.run_command(
            make_command("info"), show_stdout=False, stdout_only=True, cwd=dest
        )
        if output.startswith("Standalone "):
            # Older versions of pip used to create standalone branches.
            # Convert the standalone branch to a checkout by calling "bzr bind".
            cmd_args = make_command("bind", *flags, url)
            self.run_command(cmd_args, cwd=dest)

        cmd_args = make_command("update", *flags, rev_options.to_args())
        self.run_command(cmd_args, cwd=dest)

    @classmethod
    def get_url_rev_and_auth(cls, url: str) -> tuple[str, str | None, AuthInfo]:
        # hotfix the URL scheme after removing bzr+ from bzr+ssh:// re-add it
        url, rev, user_pass = super().get_url_rev_and_auth(url)
        if url.startswith("ssh://"):
            url = "bzr+" + url
        return url, rev, user_pass

    @classmethod
    def get_remote_url(cls, location: str) -> str:
        urls = cls.run_command(
            ["info"], show_stdout=False, stdout_only=True, cwd=location
        )
        for line in urls.splitlines():
            line = line.strip()
            for x in ("checkout of branch: ", "parent branch: "):
                if line.startswith(x):
                    repo = line.split(x)[1]
                    if cls._is_local_repository(repo):
                        return path_to_url(repo)
                    return repo
        raise RemoteNotFoundError

    @classmethod
    def get_revision(cls, location: str) -> str:
        revision = cls.run_command(
            ["revno"],
            show_stdout=False,
            stdout_only=True,
            cwd=location,
        )
        return revision.splitlines()[-1]

    @classmethod
    def is_commit_id_equal(cls, dest: str, name: str | None) -> bool:
        """Always assume the versions don't match"""
        return False


vcs.register(Bazaar)

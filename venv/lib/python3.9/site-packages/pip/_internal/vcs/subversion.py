from __future__ import annotations

import logging
import os
import re

from pip._internal.utils.misc import (
    HiddenText,
    display_path,
    is_console_interactive,
    is_installable_dir,
    split_auth_from_netloc,
)
from pip._internal.utils.subprocess import CommandArgs, make_command
from pip._internal.vcs.versioncontrol import (
    AuthInfo,
    RemoteNotFoundError,
    RevOptions,
    VersionControl,
    vcs,
)

logger = logging.getLogger(__name__)

_svn_xml_url_re = re.compile('url="([^"]+)"')
_svn_rev_re = re.compile(r'committed-rev="(\d+)"')
_svn_info_xml_rev_re = re.compile(r'\s*revision="(\d+)"')
_svn_info_xml_url_re = re.compile(r"<url>(.*)</url>")


class Subversion(VersionControl):
    name = "svn"
    dirname = ".svn"
    repo_name = "checkout"
    schemes = ("svn+ssh", "svn+http", "svn+https", "svn+svn", "svn+file")

    @classmethod
    def should_add_vcs_url_prefix(cls, remote_url: str) -> bool:
        return True

    @staticmethod
    def get_base_rev_args(rev: str) -> list[str]:
        return ["-r", rev]

    @classmethod
    def get_revision(cls, location: str) -> str:
        """
        Return the maximum revision for all files under a given location
        """
        # Note: taken from setuptools.command.egg_info
        revision = 0

        for base, dirs, _ in os.walk(location):
            if cls.dirname not in dirs:
                dirs[:] = []
                continue  # no sense walking uncontrolled subdirs
            dirs.remove(cls.dirname)
            entries_fn = os.path.join(base, cls.dirname, "entries")
            if not os.path.exists(entries_fn):
                # FIXME: should we warn?
                continue

            dirurl, localrev = cls._get_svn_url_rev(base)

            if base == location:
                assert dirurl is not None
                base = dirurl + "/"  # save the root url
            elif not dirurl or not dirurl.startswith(base):
                dirs[:] = []
                continue  # not part of the same svn tree, skip it
            revision = max(revision, localrev)
        return str(revision)

    @classmethod
    def get_netloc_and_auth(
        cls, netloc: str, scheme: str
    ) -> tuple[str, tuple[str | None, str | None]]:
        """
        This override allows the auth information to be passed to svn via the
        --username and --password options instead of via the URL.
        """
        if scheme == "ssh":
            # The --username and --password options can't be used for
            # svn+ssh URLs, so keep the auth information in the URL.
            return super().get_netloc_and_auth(netloc, scheme)

        return split_auth_from_netloc(netloc)

    @classmethod
    def get_url_rev_and_auth(cls, url: str) -> tuple[str, str | None, AuthInfo]:
        # hotfix the URL scheme after removing svn+ from svn+ssh:// re-add it
        url, rev, user_pass = super().get_url_rev_and_auth(url)
        if url.startswith("ssh://"):
            url = "svn+" + url
        return url, rev, user_pass

    @staticmethod
    def make_rev_args(username: str | None, password: HiddenText | None) -> CommandArgs:
        extra_args: CommandArgs = []
        if username:
            extra_args += ["--username", username]
        if password:
            extra_args += ["--password", password]

        return extra_args

    @classmethod
    def get_remote_url(cls, location: str) -> str:
        # In cases where the source is in a subdirectory, we have to look up in
        # the location until we find a valid project root.
        orig_location = location
        while not is_installable_dir(location):
            last_location = location
            location = os.path.dirname(location)
            if location == last_location:
                # We've traversed up to the root of the filesystem without
                # finding a Python project.
                logger.warning(
                    "Could not find Python project for directory %s (tried all "
                    "parent directories)",
                    orig_location,
                )
                raise RemoteNotFoundError

        url, _rev = cls._get_svn_url_rev(location)
        if url is None:
            raise RemoteNotFoundError

        return url

    @classmethod
    def _get_svn_url_rev(cls, location: str) -> tuple[str | None, int]:
        from pip._internal.exceptions import InstallationError

        entries_path = os.path.join(location, cls.dirname, "entries")
        if os.path.exists(entries_path):
            with open(entries_path) as f:
                data = f.read()
        else:  # subversion >= 1.7 does not have the 'entries' file
            data = ""

        url = None
        if data.startswith(("8", "9", "10")):
            entries = list(map(str.splitlines, data.split("\n\x0c\n")))
            del entries[0][0]  # get rid of the '8'
            url = entries[0][3]
            revs = [int(d[9]) for d in entries if len(d) > 9 and d[9]] + [0]
        elif data.startswith("<?xml"):
            match = _svn_xml_url_re.search(data)
            if not match:
                raise ValueError(f"Badly formatted data: {data!r}")
            url = match.group(1)  # get repository URL
            revs = [int(m.group(1)) for m in _svn_rev_re.finditer(data)] + [0]
        else:
            try:
                # subversion >= 1.7
                # Note that using get_remote_call_options is not necessary here
                # because `svn info` is being run against a local directory.
                # We don't need to worry about making sure interactive mode
                # is being used to prompt for passwords, because passwords
                # are only potentially needed for remote server requests.
                xml = cls.run_command(
                    ["info", "--xml", location],
                    show_stdout=False,
                    stdout_only=True,
                )
                match = _svn_info_xml_url_re.search(xml)
                assert match is not None
                url = match.group(1)
                revs = [int(m.group(1)) for m in _svn_info_xml_rev_re.finditer(xml)]
            except InstallationError:
                url, revs = None, []

        if revs:
            rev = max(revs)
        else:
            rev = 0

        return url, rev

    @classmethod
    def is_commit_id_equal(cls, dest: str, name: str | None) -> bool:
        """Always assume the versions don't match"""
        return False

    def __init__(self, use_interactive: bool | None = None) -> None:
        if use_interactive is None:
            use_interactive = is_console_interactive()
        self.use_interactive = use_interactive

        # This member is used to cache the fetched version of the current
        # ``svn`` client.
        # Special value definitions:
        #   None: Not evaluated yet.
        #   Empty tuple: Could not parse version.
        self._vcs_version: tuple[int, ...] | None = None

        super().__init__()

    def call_vcs_version(self) -> tuple[int, ...]:
        """Query the version of the currently installed Subversion client.

        :return: A tuple containing the parts of the version information or
            ``()`` if the version returned from ``svn`` could not be parsed.
        :raises: BadCommand: If ``svn`` is not installed.
        """
        # Example versions:
        #   svn, version 1.10.3 (r1842928)
        #      compiled Feb 25 2019, 14:20:39 on x86_64-apple-darwin17.0.0
        #   svn, version 1.7.14 (r1542130)
        #      compiled Mar 28 2018, 08:49:13 on x86_64-pc-linux-gnu
        #   svn, version 1.12.0-SlikSvn (SlikSvn/1.12.0)
        #      compiled May 28 2019, 13:44:56 on x86_64-microsoft-windows6.2
        version_prefix = "svn, version "
        version = self.run_command(["--version"], show_stdout=False, stdout_only=True)
        if not version.startswith(version_prefix):
            return ()

        version = version[len(version_prefix) :].split()[0]
        version_list = version.partition("-")[0].split(".")
        try:
            parsed_version = tuple(map(int, version_list))
        except ValueError:
            return ()

        return parsed_version

    def get_vcs_version(self) -> tuple[int, ...]:
        """Return the version of the currently installed Subversion client.

        If the version of the Subversion client has already been queried,
        a cached value will be used.

        :return: A tuple containing the parts of the version information or
            ``()`` if the version returned from ``svn`` could not be parsed.
        :raises: BadCommand: If ``svn`` is not installed.
        """
        if self._vcs_version is not None:
            # Use cached version, if available.
            # If parsing the version failed previously (empty tuple),
            # do not attempt to parse it again.
            return self._vcs_version

        vcs_version = self.call_vcs_version()
        self._vcs_version = vcs_version
        return vcs_version

    def get_remote_call_options(self) -> CommandArgs:
        """Return options to be used on calls to Subversion that contact the server.

        These options are applicable for the following ``svn`` subcommands used
        in this class.

            - checkout
            - switch
            - update

        :return: A list of command line arguments to pass to ``svn``.
        """
        if not self.use_interactive:
            # --non-interactive switch is available since Subversion 0.14.4.
            # Subversion < 1.8 runs in interactive mode by default.
            return ["--non-interactive"]

        svn_version = self.get_vcs_version()
        # By default, Subversion >= 1.8 runs in non-interactive mode if
        # stdin is not a TTY. Since that is how pip invokes SVN, in
        # call_subprocess(), pip must pass --force-interactive to ensure
        # the user can be prompted for a password, if required.
        #   SVN added the --force-interactive option in SVN 1.8. Since
        # e.g. RHEL/CentOS 7, which is supported until 2024, ships with
        # SVN 1.7, pip should continue to support SVN 1.7. Therefore, pip
        # can't safely add the option if the SVN version is < 1.8 (or unknown).
        if svn_version >= (1, 8):
            return ["--force-interactive"]

        return []

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
        else:
            flags = []
        cmd_args = make_command(
            "checkout",
            *flags,
            self.get_remote_call_options(),
            rev_options.to_args(),
            url,
            dest,
        )
        self.run_command(cmd_args)

    def switch(
        self,
        dest: str,
        url: HiddenText,
        rev_options: RevOptions,
        verbosity: int = 0,
    ) -> None:
        cmd_args = make_command(
            "switch",
            self.get_remote_call_options(),
            rev_options.to_args(),
            url,
            dest,
        )
        self.run_command(cmd_args)

    def update(
        self,
        dest: str,
        url: HiddenText,
        rev_options: RevOptions,
        verbosity: int = 0,
    ) -> None:
        cmd_args = make_command(
            "update",
            self.get_remote_call_options(),
            rev_options.to_args(),
            dest,
        )
        self.run_command(cmd_args)


vcs.register(Subversion)

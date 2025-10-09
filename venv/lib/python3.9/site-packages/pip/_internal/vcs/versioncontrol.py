"""Handles all VCS (version control) support"""

from __future__ import annotations

import logging
import os
import shutil
import sys
import urllib.parse
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import (
    Any,
    Literal,
    Optional,
)

from pip._internal.cli.spinners import SpinnerInterface
from pip._internal.exceptions import BadCommand, InstallationError
from pip._internal.utils.misc import (
    HiddenText,
    ask_path_exists,
    backup_dir,
    display_path,
    hide_url,
    hide_value,
    is_installable_dir,
    rmtree,
)
from pip._internal.utils.subprocess import (
    CommandArgs,
    call_subprocess,
    format_command_args,
    make_command,
)

__all__ = ["vcs"]


logger = logging.getLogger(__name__)

AuthInfo = tuple[Optional[str], Optional[str]]


def is_url(name: str) -> bool:
    """
    Return true if the name looks like a URL.
    """
    scheme = urllib.parse.urlsplit(name).scheme
    if not scheme:
        return False
    return scheme in ["http", "https", "file", "ftp"] + vcs.all_schemes


def make_vcs_requirement_url(
    repo_url: str, rev: str, project_name: str, subdir: str | None = None
) -> str:
    """
    Return the URL for a VCS requirement.

    Args:
      repo_url: the remote VCS url, with any needed VCS prefix (e.g. "git+").
      project_name: the (unescaped) project name.
    """
    egg_project_name = project_name.replace("-", "_")
    req = f"{repo_url}@{rev}#egg={egg_project_name}"
    if subdir:
        req += f"&subdirectory={subdir}"

    return req


def find_path_to_project_root_from_repo_root(
    location: str, repo_root: str
) -> str | None:
    """
    Find the the Python project's root by searching up the filesystem from
    `location`. Return the path to project root relative to `repo_root`.
    Return None if the project root is `repo_root`, or cannot be found.
    """
    # find project root.
    orig_location = location
    while not is_installable_dir(location):
        last_location = location
        location = os.path.dirname(location)
        if location == last_location:
            # We've traversed up to the root of the filesystem without
            # finding a Python project.
            logger.warning(
                "Could not find a Python project for directory %s (tried all "
                "parent directories)",
                orig_location,
            )
            return None

    if os.path.samefile(repo_root, location):
        return None

    return os.path.relpath(location, repo_root)


class RemoteNotFoundError(Exception):
    pass


class RemoteNotValidError(Exception):
    def __init__(self, url: str):
        super().__init__(url)
        self.url = url


@dataclass(frozen=True)
class RevOptions:
    """
    Encapsulates a VCS-specific revision to install, along with any VCS
    install options.

    Args:
        vc_class: a VersionControl subclass.
        rev: the name of the revision to install.
        extra_args: a list of extra options.
    """

    vc_class: type[VersionControl]
    rev: str | None = None
    extra_args: CommandArgs = field(default_factory=list)
    branch_name: str | None = None

    def __repr__(self) -> str:
        return f"<RevOptions {self.vc_class.name}: rev={self.rev!r}>"

    @property
    def arg_rev(self) -> str | None:
        if self.rev is None:
            return self.vc_class.default_arg_rev

        return self.rev

    def to_args(self) -> CommandArgs:
        """
        Return the VCS-specific command arguments.
        """
        args: CommandArgs = []
        rev = self.arg_rev
        if rev is not None:
            args += self.vc_class.get_base_rev_args(rev)
        args += self.extra_args

        return args

    def to_display(self) -> str:
        if not self.rev:
            return ""

        return f" (to revision {self.rev})"

    def make_new(self, rev: str) -> RevOptions:
        """
        Make a copy of the current instance, but with a new rev.

        Args:
          rev: the name of the revision for the new object.
        """
        return self.vc_class.make_rev_options(rev, extra_args=self.extra_args)


class VcsSupport:
    _registry: dict[str, VersionControl] = {}
    schemes = ["ssh", "git", "hg", "bzr", "sftp", "svn"]

    def __init__(self) -> None:
        # Register more schemes with urlparse for various version control
        # systems
        urllib.parse.uses_netloc.extend(self.schemes)
        super().__init__()

    def __iter__(self) -> Iterator[str]:
        return self._registry.__iter__()

    @property
    def backends(self) -> list[VersionControl]:
        return list(self._registry.values())

    @property
    def dirnames(self) -> list[str]:
        return [backend.dirname for backend in self.backends]

    @property
    def all_schemes(self) -> list[str]:
        schemes: list[str] = []
        for backend in self.backends:
            schemes.extend(backend.schemes)
        return schemes

    def register(self, cls: type[VersionControl]) -> None:
        if not hasattr(cls, "name"):
            logger.warning("Cannot register VCS %s", cls.__name__)
            return
        if cls.name not in self._registry:
            self._registry[cls.name] = cls()
            logger.debug("Registered VCS backend: %s", cls.name)

    def unregister(self, name: str) -> None:
        if name in self._registry:
            del self._registry[name]

    def get_backend_for_dir(self, location: str) -> VersionControl | None:
        """
        Return a VersionControl object if a repository of that type is found
        at the given directory.
        """
        vcs_backends = {}
        for vcs_backend in self._registry.values():
            repo_path = vcs_backend.get_repository_root(location)
            if not repo_path:
                continue
            logger.debug("Determine that %s uses VCS: %s", location, vcs_backend.name)
            vcs_backends[repo_path] = vcs_backend

        if not vcs_backends:
            return None

        # Choose the VCS in the inner-most directory. Since all repository
        # roots found here would be either `location` or one of its
        # parents, the longest path should have the most path components,
        # i.e. the backend representing the inner-most repository.
        inner_most_repo_path = max(vcs_backends, key=len)
        return vcs_backends[inner_most_repo_path]

    def get_backend_for_scheme(self, scheme: str) -> VersionControl | None:
        """
        Return a VersionControl object or None.
        """
        for vcs_backend in self._registry.values():
            if scheme in vcs_backend.schemes:
                return vcs_backend
        return None

    def get_backend(self, name: str) -> VersionControl | None:
        """
        Return a VersionControl object or None.
        """
        name = name.lower()
        return self._registry.get(name)


vcs = VcsSupport()


class VersionControl:
    name = ""
    dirname = ""
    repo_name = ""
    # List of supported schemes for this Version Control
    schemes: tuple[str, ...] = ()
    # Iterable of environment variable names to pass to call_subprocess().
    unset_environ: tuple[str, ...] = ()
    default_arg_rev: str | None = None

    @classmethod
    def should_add_vcs_url_prefix(cls, remote_url: str) -> bool:
        """
        Return whether the vcs prefix (e.g. "git+") should be added to a
        repository's remote url when used in a requirement.
        """
        return not remote_url.lower().startswith(f"{cls.name}:")

    @classmethod
    def get_subdirectory(cls, location: str) -> str | None:
        """
        Return the path to Python project root, relative to the repo root.
        Return None if the project root is in the repo root.
        """
        return None

    @classmethod
    def get_requirement_revision(cls, repo_dir: str) -> str:
        """
        Return the revision string that should be used in a requirement.
        """
        return cls.get_revision(repo_dir)

    @classmethod
    def get_src_requirement(cls, repo_dir: str, project_name: str) -> str:
        """
        Return the requirement string to use to redownload the files
        currently at the given repository directory.

        Args:
          project_name: the (unescaped) project name.

        The return value has a form similar to the following:

            {repository_url}@{revision}#egg={project_name}
        """
        repo_url = cls.get_remote_url(repo_dir)

        if cls.should_add_vcs_url_prefix(repo_url):
            repo_url = f"{cls.name}+{repo_url}"

        revision = cls.get_requirement_revision(repo_dir)
        subdir = cls.get_subdirectory(repo_dir)
        req = make_vcs_requirement_url(repo_url, revision, project_name, subdir=subdir)

        return req

    @staticmethod
    def get_base_rev_args(rev: str) -> list[str]:
        """
        Return the base revision arguments for a vcs command.

        Args:
          rev: the name of a revision to install.  Cannot be None.
        """
        raise NotImplementedError

    def is_immutable_rev_checkout(self, url: str, dest: str) -> bool:
        """
        Return true if the commit hash checked out at dest matches
        the revision in url.

        Always return False, if the VCS does not support immutable commit
        hashes.

        This method does not check if there are local uncommitted changes
        in dest after checkout, as pip currently has no use case for that.
        """
        return False

    @classmethod
    def make_rev_options(
        cls, rev: str | None = None, extra_args: CommandArgs | None = None
    ) -> RevOptions:
        """
        Return a RevOptions object.

        Args:
          rev: the name of a revision to install.
          extra_args: a list of extra options.
        """
        return RevOptions(cls, rev, extra_args=extra_args or [])

    @classmethod
    def _is_local_repository(cls, repo: str) -> bool:
        """
        posix absolute paths start with os.path.sep,
        win32 ones start with drive (like c:\\folder)
        """
        drive, tail = os.path.splitdrive(repo)
        return repo.startswith(os.path.sep) or bool(drive)

    @classmethod
    def get_netloc_and_auth(
        cls, netloc: str, scheme: str
    ) -> tuple[str, tuple[str | None, str | None]]:
        """
        Parse the repository URL's netloc, and return the new netloc to use
        along with auth information.

        Args:
          netloc: the original repository URL netloc.
          scheme: the repository URL's scheme without the vcs prefix.

        This is mainly for the Subversion class to override, so that auth
        information can be provided via the --username and --password options
        instead of through the URL.  For other subclasses like Git without
        such an option, auth information must stay in the URL.

        Returns: (netloc, (username, password)).
        """
        return netloc, (None, None)

    @classmethod
    def get_url_rev_and_auth(cls, url: str) -> tuple[str, str | None, AuthInfo]:
        """
        Parse the repository URL to use, and return the URL, revision,
        and auth info to use.

        Returns: (url, rev, (username, password)).
        """
        scheme, netloc, path, query, frag = urllib.parse.urlsplit(url)
        if "+" not in scheme:
            raise ValueError(
                f"Sorry, {url!r} is a malformed VCS url. "
                "The format is <vcs>+<protocol>://<url>, "
                "e.g. svn+http://myrepo/svn/MyApp#egg=MyApp"
            )
        # Remove the vcs prefix.
        scheme = scheme.split("+", 1)[1]
        netloc, user_pass = cls.get_netloc_and_auth(netloc, scheme)
        rev = None
        if "@" in path:
            path, rev = path.rsplit("@", 1)
            if not rev:
                raise InstallationError(
                    f"The URL {url!r} has an empty revision (after @) "
                    "which is not supported. Include a revision after @ "
                    "or remove @ from the URL."
                )
        url = urllib.parse.urlunsplit((scheme, netloc, path, query, ""))
        return url, rev, user_pass

    @staticmethod
    def make_rev_args(username: str | None, password: HiddenText | None) -> CommandArgs:
        """
        Return the RevOptions "extra arguments" to use in obtain().
        """
        return []

    def get_url_rev_options(self, url: HiddenText) -> tuple[HiddenText, RevOptions]:
        """
        Return the URL and RevOptions object to use in obtain(),
        as a tuple (url, rev_options).
        """
        secret_url, rev, user_pass = self.get_url_rev_and_auth(url.secret)
        username, secret_password = user_pass
        password: HiddenText | None = None
        if secret_password is not None:
            password = hide_value(secret_password)
        extra_args = self.make_rev_args(username, password)
        rev_options = self.make_rev_options(rev, extra_args=extra_args)

        return hide_url(secret_url), rev_options

    @staticmethod
    def normalize_url(url: str) -> str:
        """
        Normalize a URL for comparison by unquoting it and removing any
        trailing slash.
        """
        return urllib.parse.unquote(url).rstrip("/")

    @classmethod
    def compare_urls(cls, url1: str, url2: str) -> bool:
        """
        Compare two repo URLs for identity, ignoring incidental differences.
        """
        return cls.normalize_url(url1) == cls.normalize_url(url2)

    def fetch_new(
        self, dest: str, url: HiddenText, rev_options: RevOptions, verbosity: int
    ) -> None:
        """
        Fetch a revision from a repository, in the case that this is the
        first fetch from the repository.

        Args:
          dest: the directory to fetch the repository to.
          rev_options: a RevOptions object.
          verbosity: verbosity level.
        """
        raise NotImplementedError

    def switch(
        self,
        dest: str,
        url: HiddenText,
        rev_options: RevOptions,
        verbosity: int = 0,
    ) -> None:
        """
        Switch the repo at ``dest`` to point to ``URL``.

        Args:
          rev_options: a RevOptions object.
        """
        raise NotImplementedError

    def update(
        self,
        dest: str,
        url: HiddenText,
        rev_options: RevOptions,
        verbosity: int = 0,
    ) -> None:
        """
        Update an already-existing repo to the given ``rev_options``.

        Args:
          rev_options: a RevOptions object.
        """
        raise NotImplementedError

    @classmethod
    def is_commit_id_equal(cls, dest: str, name: str | None) -> bool:
        """
        Return whether the id of the current commit equals the given name.

        Args:
          dest: the repository directory.
          name: a string name.
        """
        raise NotImplementedError

    def obtain(self, dest: str, url: HiddenText, verbosity: int) -> None:
        """
        Install or update in editable mode the package represented by this
        VersionControl object.

        :param dest: the repository directory in which to install or update.
        :param url: the repository URL starting with a vcs prefix.
        :param verbosity: verbosity level.
        """
        url, rev_options = self.get_url_rev_options(url)

        if not os.path.exists(dest):
            self.fetch_new(dest, url, rev_options, verbosity=verbosity)
            return

        rev_display = rev_options.to_display()
        if self.is_repository_directory(dest):
            existing_url = self.get_remote_url(dest)
            if self.compare_urls(existing_url, url.secret):
                logger.debug(
                    "%s in %s exists, and has correct URL (%s)",
                    self.repo_name.title(),
                    display_path(dest),
                    url,
                )
                if not self.is_commit_id_equal(dest, rev_options.rev):
                    logger.info(
                        "Updating %s %s%s",
                        display_path(dest),
                        self.repo_name,
                        rev_display,
                    )
                    self.update(dest, url, rev_options, verbosity=verbosity)
                else:
                    logger.info("Skipping because already up-to-date.")
                return

            logger.warning(
                "%s %s in %s exists with URL %s",
                self.name,
                self.repo_name,
                display_path(dest),
                existing_url,
            )
            prompt = ("(s)witch, (i)gnore, (w)ipe, (b)ackup ", ("s", "i", "w", "b"))
        else:
            logger.warning(
                "Directory %s already exists, and is not a %s %s.",
                dest,
                self.name,
                self.repo_name,
            )
            # https://github.com/python/mypy/issues/1174
            prompt = ("(i)gnore, (w)ipe, (b)ackup ", ("i", "w", "b"))  # type: ignore

        logger.warning(
            "The plan is to install the %s repository %s",
            self.name,
            url,
        )
        response = ask_path_exists(f"What to do?  {prompt[0]}", prompt[1])

        if response == "a":
            sys.exit(-1)

        if response == "w":
            logger.warning("Deleting %s", display_path(dest))
            rmtree(dest)
            self.fetch_new(dest, url, rev_options, verbosity=verbosity)
            return

        if response == "b":
            dest_dir = backup_dir(dest)
            logger.warning("Backing up %s to %s", display_path(dest), dest_dir)
            shutil.move(dest, dest_dir)
            self.fetch_new(dest, url, rev_options, verbosity=verbosity)
            return

        # Do nothing if the response is "i".
        if response == "s":
            logger.info(
                "Switching %s %s to %s%s",
                self.repo_name,
                display_path(dest),
                url,
                rev_display,
            )
            self.switch(dest, url, rev_options, verbosity=verbosity)

    def unpack(self, location: str, url: HiddenText, verbosity: int) -> None:
        """
        Clean up current location and download the url repository
        (and vcs infos) into location

        :param url: the repository URL starting with a vcs prefix.
        :param verbosity: verbosity level.
        """
        if os.path.exists(location):
            rmtree(location)
        self.obtain(location, url=url, verbosity=verbosity)

    @classmethod
    def get_remote_url(cls, location: str) -> str:
        """
        Return the url used at location

        Raises RemoteNotFoundError if the repository does not have a remote
        url configured.
        """
        raise NotImplementedError

    @classmethod
    def get_revision(cls, location: str) -> str:
        """
        Return the current commit id of the files at the given location.
        """
        raise NotImplementedError

    @classmethod
    def run_command(
        cls,
        cmd: list[str] | CommandArgs,
        show_stdout: bool = True,
        cwd: str | None = None,
        on_returncode: Literal["raise", "warn", "ignore"] = "raise",
        extra_ok_returncodes: Iterable[int] | None = None,
        command_desc: str | None = None,
        extra_environ: Mapping[str, Any] | None = None,
        spinner: SpinnerInterface | None = None,
        log_failed_cmd: bool = True,
        stdout_only: bool = False,
    ) -> str:
        """
        Run a VCS subcommand
        This is simply a wrapper around call_subprocess that adds the VCS
        command name, and checks that the VCS is available
        """
        cmd = make_command(cls.name, *cmd)
        if command_desc is None:
            command_desc = format_command_args(cmd)
        try:
            return call_subprocess(
                cmd,
                show_stdout,
                cwd,
                on_returncode=on_returncode,
                extra_ok_returncodes=extra_ok_returncodes,
                command_desc=command_desc,
                extra_environ=extra_environ,
                unset_environ=cls.unset_environ,
                spinner=spinner,
                log_failed_cmd=log_failed_cmd,
                stdout_only=stdout_only,
            )
        except NotADirectoryError:
            raise BadCommand(f"Cannot find command {cls.name!r} - invalid PATH")
        except FileNotFoundError:
            # errno.ENOENT = no such file or directory
            # In other words, the VCS executable isn't available
            raise BadCommand(
                f"Cannot find command {cls.name!r} - do you have "
                f"{cls.name!r} installed and in your PATH?"
            )
        except PermissionError:
            # errno.EACCES = Permission denied
            # This error occurs, for instance, when the command is installed
            # only for another user. So, the current user don't have
            # permission to call the other user command.
            raise BadCommand(
                f"No permission to execute {cls.name!r} - install it "
                f"locally, globally (ask admin), or check your PATH. "
                f"See possible solutions at "
                f"https://pip.pypa.io/en/latest/reference/pip_freeze/"
                f"#fixing-permission-denied."
            )

    @classmethod
    def is_repository_directory(cls, path: str) -> bool:
        """
        Return whether a directory path is a repository directory.
        """
        logger.debug("Checking in %s for %s (%s)...", path, cls.dirname, cls.name)
        return os.path.exists(os.path.join(path, cls.dirname))

    @classmethod
    def get_repository_root(cls, location: str) -> str | None:
        """
        Return the "root" (top-level) directory controlled by the vcs,
        or `None` if the directory is not in any.

        It is meant to be overridden to implement smarter detection
        mechanisms for specific vcs.

        This can do more than is_repository_directory() alone. For
        example, the Git override checks that Git is actually available.
        """
        if cls.is_repository_directory(location):
            return location
        return None

"""Network Authentication Helpers

Contains interface (MultiDomainBasicAuth) and associated glue code for
providing credentials in the context of network requests.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sysconfig
import typing
import urllib.parse
from abc import ABC, abstractmethod
from functools import cache
from os.path import commonprefix
from pathlib import Path
from typing import Any, NamedTuple

from pip._vendor.requests.auth import AuthBase, HTTPBasicAuth
from pip._vendor.requests.models import Request, Response
from pip._vendor.requests.utils import get_netrc_auth

from pip._internal.utils.logging import getLogger
from pip._internal.utils.misc import (
    ask,
    ask_input,
    ask_password,
    remove_auth_from_url,
    split_auth_netloc_from_url,
)
from pip._internal.vcs.versioncontrol import AuthInfo

logger = getLogger(__name__)

KEYRING_DISABLED = False


class Credentials(NamedTuple):
    url: str
    username: str
    password: str


class KeyRingBaseProvider(ABC):
    """Keyring base provider interface"""

    has_keyring: bool

    @abstractmethod
    def get_auth_info(self, url: str, username: str | None) -> AuthInfo | None: ...

    @abstractmethod
    def save_auth_info(self, url: str, username: str, password: str) -> None: ...


class KeyRingNullProvider(KeyRingBaseProvider):
    """Keyring null provider"""

    has_keyring = False

    def get_auth_info(self, url: str, username: str | None) -> AuthInfo | None:
        return None

    def save_auth_info(self, url: str, username: str, password: str) -> None:
        return None


class KeyRingPythonProvider(KeyRingBaseProvider):
    """Keyring interface which uses locally imported `keyring`"""

    has_keyring = True

    def __init__(self) -> None:
        import keyring

        self.keyring = keyring

    def get_auth_info(self, url: str, username: str | None) -> AuthInfo | None:
        # Support keyring's get_credential interface which supports getting
        # credentials without a username. This is only available for
        # keyring>=15.2.0.
        if hasattr(self.keyring, "get_credential"):
            logger.debug("Getting credentials from keyring for %s", url)
            cred = self.keyring.get_credential(url, username)
            if cred is not None:
                return cred.username, cred.password
            return None

        if username is not None:
            logger.debug("Getting password from keyring for %s", url)
            password = self.keyring.get_password(url, username)
            if password:
                return username, password
        return None

    def save_auth_info(self, url: str, username: str, password: str) -> None:
        self.keyring.set_password(url, username, password)


class KeyRingCliProvider(KeyRingBaseProvider):
    """Provider which uses `keyring` cli

    Instead of calling the keyring package installed alongside pip
    we call keyring on the command line which will enable pip to
    use which ever installation of keyring is available first in
    PATH.
    """

    has_keyring = True

    def __init__(self, cmd: str) -> None:
        self.keyring = cmd

    def get_auth_info(self, url: str, username: str | None) -> AuthInfo | None:
        # This is the default implementation of keyring.get_credential
        # https://github.com/jaraco/keyring/blob/97689324abcf01bd1793d49063e7ca01e03d7d07/keyring/backend.py#L134-L139
        if username is not None:
            password = self._get_password(url, username)
            if password is not None:
                return username, password
        return None

    def save_auth_info(self, url: str, username: str, password: str) -> None:
        return self._set_password(url, username, password)

    def _get_password(self, service_name: str, username: str) -> str | None:
        """Mirror the implementation of keyring.get_password using cli"""
        if self.keyring is None:
            return None

        cmd = [self.keyring, "get", service_name, username]
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        res = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            env=env,
        )
        if res.returncode:
            return None
        return res.stdout.decode("utf-8").strip(os.linesep)

    def _set_password(self, service_name: str, username: str, password: str) -> None:
        """Mirror the implementation of keyring.set_password using cli"""
        if self.keyring is None:
            return None
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        subprocess.run(
            [self.keyring, "set", service_name, username],
            input=f"{password}{os.linesep}".encode(),
            env=env,
            check=True,
        )
        return None


@cache
def get_keyring_provider(provider: str) -> KeyRingBaseProvider:
    logger.verbose("Keyring provider requested: %s", provider)

    # keyring has previously failed and been disabled
    if KEYRING_DISABLED:
        provider = "disabled"
    if provider in ["import", "auto"]:
        try:
            impl = KeyRingPythonProvider()
            logger.verbose("Keyring provider set: import")
            return impl
        except ImportError:
            pass
        except Exception as exc:
            # In the event of an unexpected exception
            # we should warn the user
            msg = "Installed copy of keyring fails with exception %s"
            if provider == "auto":
                msg = msg + ", trying to find a keyring executable as a fallback"
            logger.warning(msg, exc, exc_info=logger.isEnabledFor(logging.DEBUG))
    if provider in ["subprocess", "auto"]:
        cli = shutil.which("keyring")
        if cli and cli.startswith(sysconfig.get_path("scripts")):
            # all code within this function is stolen from shutil.which implementation
            @typing.no_type_check
            def PATH_as_shutil_which_determines_it() -> str:
                path = os.environ.get("PATH", None)
                if path is None:
                    try:
                        path = os.confstr("CS_PATH")
                    except (AttributeError, ValueError):
                        # os.confstr() or CS_PATH is not available
                        path = os.defpath
                # bpo-35755: Don't use os.defpath if the PATH environment variable is
                # set to an empty string

                return path

            scripts = Path(sysconfig.get_path("scripts"))

            paths = []
            for path in PATH_as_shutil_which_determines_it().split(os.pathsep):
                p = Path(path)
                try:
                    if not p.samefile(scripts):
                        paths.append(path)
                except FileNotFoundError:
                    pass

            path = os.pathsep.join(paths)

            cli = shutil.which("keyring", path=path)

        if cli:
            logger.verbose("Keyring provider set: subprocess with executable %s", cli)
            return KeyRingCliProvider(cli)

    logger.verbose("Keyring provider set: disabled")
    return KeyRingNullProvider()


class MultiDomainBasicAuth(AuthBase):
    def __init__(
        self,
        prompting: bool = True,
        index_urls: list[str] | None = None,
        keyring_provider: str = "auto",
    ) -> None:
        self.prompting = prompting
        self.index_urls = index_urls
        self.keyring_provider = keyring_provider
        self.passwords: dict[str, AuthInfo] = {}
        # When the user is prompted to enter credentials and keyring is
        # available, we will offer to save them. If the user accepts,
        # this value is set to the credentials they entered. After the
        # request authenticates, the caller should call
        # ``save_credentials`` to save these.
        self._credentials_to_save: Credentials | None = None

    @property
    def keyring_provider(self) -> KeyRingBaseProvider:
        return get_keyring_provider(self._keyring_provider)

    @keyring_provider.setter
    def keyring_provider(self, provider: str) -> None:
        # The free function get_keyring_provider has been decorated with
        # functools.cache. If an exception occurs in get_keyring_auth that
        # cache will be cleared and keyring disabled, take that into account
        # if you want to remove this indirection.
        self._keyring_provider = provider

    @property
    def use_keyring(self) -> bool:
        # We won't use keyring when --no-input is passed unless
        # a specific provider is requested because it might require
        # user interaction
        return self.prompting or self._keyring_provider not in ["auto", "disabled"]

    def _get_keyring_auth(
        self,
        url: str | None,
        username: str | None,
    ) -> AuthInfo | None:
        """Return the tuple auth for a given url from keyring."""
        # Do nothing if no url was provided
        if not url:
            return None

        try:
            return self.keyring_provider.get_auth_info(url, username)
        except Exception as exc:
            # Log the full exception (with stacktrace) at debug, so it'll only
            # show up when running in verbose mode.
            logger.debug("Keyring is skipped due to an exception", exc_info=True)
            # Always log a shortened version of the exception.
            logger.warning(
                "Keyring is skipped due to an exception: %s",
                str(exc),
            )
            global KEYRING_DISABLED
            KEYRING_DISABLED = True
            get_keyring_provider.cache_clear()
            return None

    def _get_index_url(self, url: str) -> str | None:
        """Return the original index URL matching the requested URL.

        Cached or dynamically generated credentials may work against
        the original index URL rather than just the netloc.

        The provided url should have had its username and password
        removed already. If the original index url had credentials then
        they will be included in the return value.

        Returns None if no matching index was found, or if --no-index
        was specified by the user.
        """
        if not url or not self.index_urls:
            return None

        url = remove_auth_from_url(url).rstrip("/") + "/"
        parsed_url = urllib.parse.urlsplit(url)

        candidates = []

        for index in self.index_urls:
            index = index.rstrip("/") + "/"
            parsed_index = urllib.parse.urlsplit(remove_auth_from_url(index))
            if parsed_url == parsed_index:
                return index

            if parsed_url.netloc != parsed_index.netloc:
                continue

            candidate = urllib.parse.urlsplit(index)
            candidates.append(candidate)

        if not candidates:
            return None

        candidates.sort(
            reverse=True,
            key=lambda candidate: commonprefix(
                [
                    parsed_url.path,
                    candidate.path,
                ]
            ).rfind("/"),
        )

        return urllib.parse.urlunsplit(candidates[0])

    def _get_new_credentials(
        self,
        original_url: str,
        *,
        allow_netrc: bool = True,
        allow_keyring: bool = False,
    ) -> AuthInfo:
        """Find and return credentials for the specified URL."""
        # Split the credentials and netloc from the url.
        url, netloc, url_user_password = split_auth_netloc_from_url(
            original_url,
        )

        # Start with the credentials embedded in the url
        username, password = url_user_password
        if username is not None and password is not None:
            logger.debug("Found credentials in url for %s", netloc)
            return url_user_password

        # Find a matching index url for this request
        index_url = self._get_index_url(url)
        if index_url:
            # Split the credentials from the url.
            index_info = split_auth_netloc_from_url(index_url)
            if index_info:
                index_url, _, index_url_user_password = index_info
                logger.debug("Found index url %s", index_url)

        # If an index URL was found, try its embedded credentials
        if index_url and index_url_user_password[0] is not None:
            username, password = index_url_user_password
            if username is not None and password is not None:
                logger.debug("Found credentials in index url for %s", netloc)
                return index_url_user_password

        # Get creds from netrc if we still don't have them
        if allow_netrc:
            netrc_auth = get_netrc_auth(original_url)
            if netrc_auth:
                logger.debug("Found credentials in netrc for %s", netloc)
                return netrc_auth

        # If we don't have a password and keyring is available, use it.
        if allow_keyring:
            # The index url is more specific than the netloc, so try it first
            # fmt: off
            kr_auth = (
                self._get_keyring_auth(index_url, username) or
                self._get_keyring_auth(netloc, username)
            )
            # fmt: on
            if kr_auth:
                logger.debug("Found credentials in keyring for %s", netloc)
                return kr_auth

        return username, password

    def _get_url_and_credentials(
        self, original_url: str
    ) -> tuple[str, str | None, str | None]:
        """Return the credentials to use for the provided URL.

        If allowed, netrc and keyring may be used to obtain the
        correct credentials.

        Returns (url_without_credentials, username, password). Note
        that even if the original URL contains credentials, this
        function may return a different username and password.
        """
        url, netloc, _ = split_auth_netloc_from_url(original_url)

        # Try to get credentials from original url
        username, password = self._get_new_credentials(original_url)

        # If credentials not found, use any stored credentials for this netloc.
        # Do this if either the username or the password is missing.
        # This accounts for the situation in which the user has specified
        # the username in the index url, but the password comes from keyring.
        if (username is None or password is None) and netloc in self.passwords:
            un, pw = self.passwords[netloc]
            # It is possible that the cached credentials are for a different username,
            # in which case the cache should be ignored.
            if username is None or username == un:
                username, password = un, pw

        if username is not None or password is not None:
            # Convert the username and password if they're None, so that
            # this netloc will show up as "cached" in the conditional above.
            # Further, HTTPBasicAuth doesn't accept None, so it makes sense to
            # cache the value that is going to be used.
            username = username or ""
            password = password or ""

            # Store any acquired credentials.
            self.passwords[netloc] = (username, password)

        assert (
            # Credentials were found
            (username is not None and password is not None)
            # Credentials were not found
            or (username is None and password is None)
        ), f"Could not load credentials from url: {original_url}"

        return url, username, password

    def __call__(self, req: Request) -> Request:
        # Get credentials for this request
        url, username, password = self._get_url_and_credentials(req.url)

        # Set the url of the request to the url without any credentials
        req.url = url

        if username is not None and password is not None:
            # Send the basic auth with this request
            req = HTTPBasicAuth(username, password)(req)

        # Attach a hook to handle 401 responses
        req.register_hook("response", self.handle_401)

        return req

    # Factored out to allow for easy patching in tests
    def _prompt_for_password(self, netloc: str) -> tuple[str | None, str | None, bool]:
        username = ask_input(f"User for {netloc}: ") if self.prompting else None
        if not username:
            return None, None, False
        if self.use_keyring:
            auth = self._get_keyring_auth(netloc, username)
            if auth and auth[0] is not None and auth[1] is not None:
                return auth[0], auth[1], False
        password = ask_password("Password: ")
        return username, password, True

    # Factored out to allow for easy patching in tests
    def _should_save_password_to_keyring(self) -> bool:
        if (
            not self.prompting
            or not self.use_keyring
            or not self.keyring_provider.has_keyring
        ):
            return False
        return ask("Save credentials to keyring [y/N]: ", ["y", "n"]) == "y"

    def handle_401(self, resp: Response, **kwargs: Any) -> Response:
        # We only care about 401 responses, anything else we want to just
        #   pass through the actual response
        if resp.status_code != 401:
            return resp

        username, password = None, None

        # Query the keyring for credentials:
        if self.use_keyring:
            username, password = self._get_new_credentials(
                resp.url,
                allow_netrc=False,
                allow_keyring=True,
            )

        # We are not able to prompt the user so simply return the response
        if not self.prompting and not username and not password:
            return resp

        parsed = urllib.parse.urlparse(resp.url)

        # Prompt the user for a new username and password
        save = False
        if not username and not password:
            username, password, save = self._prompt_for_password(parsed.netloc)

        # Store the new username and password to use for future requests
        self._credentials_to_save = None
        if username is not None and password is not None:
            self.passwords[parsed.netloc] = (username, password)

            # Prompt to save the password to keyring
            if save and self._should_save_password_to_keyring():
                self._credentials_to_save = Credentials(
                    url=parsed.netloc,
                    username=username,
                    password=password,
                )

        # Consume content and release the original connection to allow our new
        #   request to reuse the same one.
        # The result of the assignment isn't used, it's just needed to consume
        # the content.
        _ = resp.content
        resp.raw.release_conn()

        # Add our new username and password to the request
        req = HTTPBasicAuth(username or "", password or "")(resp.request)
        req.register_hook("response", self.warn_on_401)

        # On successful request, save the credentials that were used to
        # keyring. (Note that if the user responded "no" above, this member
        # is not set and nothing will be saved.)
        if self._credentials_to_save:
            req.register_hook("response", self.save_credentials)

        # Send our new request
        new_resp = resp.connection.send(req, **kwargs)
        new_resp.history.append(resp)

        return new_resp

    def warn_on_401(self, resp: Response, **kwargs: Any) -> None:
        """Response callback to warn about incorrect credentials."""
        if resp.status_code == 401:
            logger.warning(
                "401 Error, Credentials not correct for %s",
                resp.request.url,
            )

    def save_credentials(self, resp: Response, **kwargs: Any) -> None:
        """Response callback to save credentials on success."""
        assert (
            self.keyring_provider.has_keyring
        ), "should never reach here without keyring"

        creds = self._credentials_to_save
        self._credentials_to_save = None
        if creds and resp.status_code < 400:
            try:
                logger.info("Saving credentials to keyring")
                self.keyring_provider.save_auth_info(
                    creds.url, creds.username, creds.password
                )
            except Exception:
                logger.exception("Failed to save credentials")

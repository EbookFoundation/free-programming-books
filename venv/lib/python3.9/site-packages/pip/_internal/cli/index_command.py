"""
Contains command classes which may interact with an index / the network.

Unlike its sister module, req_command, this module still uses lazy imports
so commands which don't always hit the network (e.g. list w/o --outdated or
--uptodate) don't need waste time importing PipSession and friends.
"""

from __future__ import annotations

import logging
import os
import sys
from functools import lru_cache
from optparse import Values
from typing import TYPE_CHECKING

from pip._vendor import certifi

from pip._internal.cli.base_command import Command
from pip._internal.cli.command_context import CommandContextMixIn

if TYPE_CHECKING:
    from ssl import SSLContext

    from pip._internal.network.session import PipSession

logger = logging.getLogger(__name__)


@lru_cache
def _create_truststore_ssl_context() -> SSLContext | None:
    if sys.version_info < (3, 10):
        logger.debug("Disabling truststore because Python version isn't 3.10+")
        return None

    try:
        import ssl
    except ImportError:
        logger.warning("Disabling truststore since ssl support is missing")
        return None

    try:
        from pip._vendor import truststore
    except ImportError:
        logger.warning("Disabling truststore because platform isn't supported")
        return None

    ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations(certifi.where())
    return ctx


class SessionCommandMixin(CommandContextMixIn):
    """
    A class mixin for command classes needing _build_session().
    """

    def __init__(self) -> None:
        super().__init__()
        self._session: PipSession | None = None

    @classmethod
    def _get_index_urls(cls, options: Values) -> list[str] | None:
        """Return a list of index urls from user-provided options."""
        index_urls = []
        if not getattr(options, "no_index", False):
            url = getattr(options, "index_url", None)
            if url:
                index_urls.append(url)
        urls = getattr(options, "extra_index_urls", None)
        if urls:
            index_urls.extend(urls)
        # Return None rather than an empty list
        return index_urls or None

    def get_default_session(self, options: Values) -> PipSession:
        """Get a default-managed session."""
        if self._session is None:
            self._session = self.enter_context(self._build_session(options))
            # there's no type annotation on requests.Session, so it's
            # automatically ContextManager[Any] and self._session becomes Any,
            # then https://github.com/python/mypy/issues/7696 kicks in
            assert self._session is not None
        return self._session

    def _build_session(
        self,
        options: Values,
        retries: int | None = None,
        timeout: int | None = None,
    ) -> PipSession:
        from pip._internal.network.session import PipSession

        cache_dir = options.cache_dir
        assert not cache_dir or os.path.isabs(cache_dir)

        if "legacy-certs" not in options.deprecated_features_enabled:
            ssl_context = _create_truststore_ssl_context()
        else:
            ssl_context = None

        session = PipSession(
            cache=os.path.join(cache_dir, "http-v2") if cache_dir else None,
            retries=retries if retries is not None else options.retries,
            trusted_hosts=options.trusted_hosts,
            index_urls=self._get_index_urls(options),
            ssl_context=ssl_context,
        )

        # Handle custom ca-bundles from the user
        if options.cert:
            session.verify = options.cert

        # Handle SSL client certificate
        if options.client_cert:
            session.cert = options.client_cert

        # Handle timeouts
        if options.timeout or timeout:
            session.timeout = timeout if timeout is not None else options.timeout

        # Handle configured proxies
        if options.proxy:
            session.proxies = {
                "http": options.proxy,
                "https": options.proxy,
            }
            session.trust_env = False
            session.pip_proxy = options.proxy

        # Determine if we can prompt the user for authentication or not
        session.auth.prompting = not options.no_input
        session.auth.keyring_provider = options.keyring_provider

        return session


def _pip_self_version_check(session: PipSession, options: Values) -> None:
    from pip._internal.self_outdated_check import pip_self_version_check as check

    check(session, options)


class IndexGroupCommand(Command, SessionCommandMixin):
    """
    Abstract base class for commands with the index_group options.

    This also corresponds to the commands that permit the pip version check.
    """

    def handle_pip_version_check(self, options: Values) -> None:
        """
        Do the pip version check if not disabled.

        This overrides the default behavior of not doing the check.
        """
        # Make sure the index_group options are present.
        assert hasattr(options, "no_index")

        if options.disable_pip_version_check or options.no_index:
            return

        try:
            # Otherwise, check if we're using the latest version of pip available.
            session = self._build_session(
                options,
                retries=0,
                timeout=min(5, options.timeout),
            )
            with session:
                _pip_self_version_check(session, options)
        except Exception:
            logger.warning("There was an error checking the latest version of pip.")
            logger.debug("See below for error", exc_info=True)

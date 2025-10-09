"""PipSession and supporting code, containing all pip-specific
network request configuration and behavior.
"""

from __future__ import annotations

import email.utils
import functools
import io
import ipaddress
import json
import logging
import mimetypes
import os
import platform
import shutil
import subprocess
import sys
import urllib.parse
import warnings
from collections.abc import Generator, Mapping, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    Union,
)

from pip._vendor import requests, urllib3
from pip._vendor.cachecontrol import CacheControlAdapter as _BaseCacheControlAdapter
from pip._vendor.requests.adapters import DEFAULT_POOLBLOCK, BaseAdapter
from pip._vendor.requests.adapters import HTTPAdapter as _BaseHTTPAdapter
from pip._vendor.requests.models import PreparedRequest, Response
from pip._vendor.requests.structures import CaseInsensitiveDict
from pip._vendor.urllib3.connectionpool import ConnectionPool
from pip._vendor.urllib3.exceptions import InsecureRequestWarning

from pip import __version__
from pip._internal.metadata import get_default_environment
from pip._internal.models.link import Link
from pip._internal.network.auth import MultiDomainBasicAuth
from pip._internal.network.cache import SafeFileCache

# Import ssl from compat so the initial import occurs in only one place.
from pip._internal.utils.compat import has_tls
from pip._internal.utils.glibc import libc_ver
from pip._internal.utils.misc import build_url_from_netloc, parse_netloc
from pip._internal.utils.urls import url_to_path

if TYPE_CHECKING:
    from ssl import SSLContext

    from pip._vendor.urllib3.poolmanager import PoolManager
    from pip._vendor.urllib3.proxymanager import ProxyManager


logger = logging.getLogger(__name__)

SecureOrigin = tuple[str, str, Optional[Union[int, str]]]


# Ignore warning raised when using --trusted-host.
warnings.filterwarnings("ignore", category=InsecureRequestWarning)


SECURE_ORIGINS: list[SecureOrigin] = [
    # protocol, hostname, port
    # Taken from Chrome's list of secure origins (See: http://bit.ly/1qrySKC)
    ("https", "*", "*"),
    ("*", "localhost", "*"),
    ("*", "127.0.0.0/8", "*"),
    ("*", "::1/128", "*"),
    ("file", "*", None),
    # ssh is always secure.
    ("ssh", "*", "*"),
]


# These are environment variables present when running under various
# CI systems.  For each variable, some CI systems that use the variable
# are indicated.  The collection was chosen so that for each of a number
# of popular systems, at least one of the environment variables is used.
# This list is used to provide some indication of and lower bound for
# CI traffic to PyPI.  Thus, it is okay if the list is not comprehensive.
# For more background, see: https://github.com/pypa/pip/issues/5499
CI_ENVIRONMENT_VARIABLES = (
    # Azure Pipelines
    "BUILD_BUILDID",
    # Jenkins
    "BUILD_ID",
    # AppVeyor, CircleCI, Codeship, Gitlab CI, Shippable, Travis CI
    "CI",
    # Explicit environment variable.
    "PIP_IS_CI",
)


def looks_like_ci() -> bool:
    """
    Return whether it looks like pip is running under CI.
    """
    # We don't use the method of checking for a tty (e.g. using isatty())
    # because some CI systems mimic a tty (e.g. Travis CI).  Thus that
    # method doesn't provide definitive information in either direction.
    return any(name in os.environ for name in CI_ENVIRONMENT_VARIABLES)


@functools.lru_cache(maxsize=1)
def user_agent() -> str:
    """
    Return a string representing the user agent.
    """
    data: dict[str, Any] = {
        "installer": {"name": "pip", "version": __version__},
        "python": platform.python_version(),
        "implementation": {
            "name": platform.python_implementation(),
        },
    }

    if data["implementation"]["name"] == "CPython":
        data["implementation"]["version"] = platform.python_version()
    elif data["implementation"]["name"] == "PyPy":
        pypy_version_info = sys.pypy_version_info  # type: ignore
        if pypy_version_info.releaselevel == "final":
            pypy_version_info = pypy_version_info[:3]
        data["implementation"]["version"] = ".".join(
            [str(x) for x in pypy_version_info]
        )
    elif data["implementation"]["name"] == "Jython":
        # Complete Guess
        data["implementation"]["version"] = platform.python_version()
    elif data["implementation"]["name"] == "IronPython":
        # Complete Guess
        data["implementation"]["version"] = platform.python_version()

    if sys.platform.startswith("linux"):
        from pip._vendor import distro

        linux_distribution = distro.name(), distro.version(), distro.codename()
        distro_infos: dict[str, Any] = dict(
            filter(
                lambda x: x[1],
                zip(["name", "version", "id"], linux_distribution),
            )
        )
        libc = dict(
            filter(
                lambda x: x[1],
                zip(["lib", "version"], libc_ver()),
            )
        )
        if libc:
            distro_infos["libc"] = libc
        if distro_infos:
            data["distro"] = distro_infos

    if sys.platform.startswith("darwin") and platform.mac_ver()[0]:
        data["distro"] = {"name": "macOS", "version": platform.mac_ver()[0]}

    if platform.system():
        data.setdefault("system", {})["name"] = platform.system()

    if platform.release():
        data.setdefault("system", {})["release"] = platform.release()

    if platform.machine():
        data["cpu"] = platform.machine()

    if has_tls():
        import _ssl as ssl

        data["openssl_version"] = ssl.OPENSSL_VERSION

    setuptools_dist = get_default_environment().get_distribution("setuptools")
    if setuptools_dist is not None:
        data["setuptools_version"] = str(setuptools_dist.version)

    if shutil.which("rustc") is not None:
        # If for any reason `rustc --version` fails, silently ignore it
        try:
            rustc_output = subprocess.check_output(
                ["rustc", "--version"], stderr=subprocess.STDOUT, timeout=0.5
            )
        except Exception:
            pass
        else:
            if rustc_output.startswith(b"rustc "):
                # The format of `rustc --version` is:
                # `b'rustc 1.52.1 (9bc8c42bb 2021-05-09)\n'`
                # We extract just the middle (1.52.1) part
                data["rustc_version"] = rustc_output.split(b" ")[1].decode()

    # Use None rather than False so as not to give the impression that
    # pip knows it is not being run under CI.  Rather, it is a null or
    # inconclusive result.  Also, we include some value rather than no
    # value to make it easier to know that the check has been run.
    data["ci"] = True if looks_like_ci() else None

    user_data = os.environ.get("PIP_USER_AGENT_USER_DATA")
    if user_data is not None:
        data["user_data"] = user_data

    return "{data[installer][name]}/{data[installer][version]} {json}".format(
        data=data,
        json=json.dumps(data, separators=(",", ":"), sort_keys=True),
    )


class LocalFSAdapter(BaseAdapter):
    def send(
        self,
        request: PreparedRequest,
        stream: bool = False,
        timeout: float | tuple[float, float] | None = None,
        verify: bool | str = True,
        cert: str | tuple[str, str] | None = None,
        proxies: Mapping[str, str] | None = None,
    ) -> Response:
        pathname = url_to_path(request.url)

        resp = Response()
        resp.status_code = 200
        resp.url = request.url

        try:
            stats = os.stat(pathname)
        except OSError as exc:
            # format the exception raised as a io.BytesIO object,
            # to return a better error message:
            resp.status_code = 404
            resp.reason = type(exc).__name__
            resp.raw = io.BytesIO(f"{resp.reason}: {exc}".encode())
        else:
            modified = email.utils.formatdate(stats.st_mtime, usegmt=True)
            content_type = mimetypes.guess_type(pathname)[0] or "text/plain"
            resp.headers = CaseInsensitiveDict(
                {
                    "Content-Type": content_type,
                    "Content-Length": stats.st_size,
                    "Last-Modified": modified,
                }
            )

            resp.raw = open(pathname, "rb")
            resp.close = resp.raw.close

        return resp

    def close(self) -> None:
        pass


class _SSLContextAdapterMixin:
    """Mixin to add the ``ssl_context`` constructor argument to HTTP adapters.

    The additional argument is forwarded directly to the pool manager. This allows us
    to dynamically decide what SSL store to use at runtime, which is used to implement
    the optional ``truststore`` backend.
    """

    def __init__(
        self,
        *,
        ssl_context: SSLContext | None = None,
        **kwargs: Any,
    ) -> None:
        self._ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(
        self,
        connections: int,
        maxsize: int,
        block: bool = DEFAULT_POOLBLOCK,
        **pool_kwargs: Any,
    ) -> PoolManager:
        if self._ssl_context is not None:
            pool_kwargs.setdefault("ssl_context", self._ssl_context)
        return super().init_poolmanager(  # type: ignore[misc]
            connections=connections,
            maxsize=maxsize,
            block=block,
            **pool_kwargs,
        )

    def proxy_manager_for(self, proxy: str, **proxy_kwargs: Any) -> ProxyManager:
        # Proxy manager replaces the pool manager, so inject our SSL
        # context here too. https://github.com/pypa/pip/issues/13288
        if self._ssl_context is not None:
            proxy_kwargs.setdefault("ssl_context", self._ssl_context)
        return super().proxy_manager_for(proxy, **proxy_kwargs)  # type: ignore[misc]


class HTTPAdapter(_SSLContextAdapterMixin, _BaseHTTPAdapter):
    pass


class CacheControlAdapter(_SSLContextAdapterMixin, _BaseCacheControlAdapter):
    pass


class InsecureHTTPAdapter(HTTPAdapter):
    def cert_verify(
        self,
        conn: ConnectionPool,
        url: str,
        verify: bool | str,
        cert: str | tuple[str, str] | None,
    ) -> None:
        super().cert_verify(conn=conn, url=url, verify=False, cert=cert)


class InsecureCacheControlAdapter(CacheControlAdapter):
    def cert_verify(
        self,
        conn: ConnectionPool,
        url: str,
        verify: bool | str,
        cert: str | tuple[str, str] | None,
    ) -> None:
        super().cert_verify(conn=conn, url=url, verify=False, cert=cert)


class PipSession(requests.Session):
    timeout: int | None = None

    def __init__(
        self,
        *args: Any,
        retries: int = 0,
        cache: str | None = None,
        trusted_hosts: Sequence[str] = (),
        index_urls: list[str] | None = None,
        ssl_context: SSLContext | None = None,
        **kwargs: Any,
    ) -> None:
        """
        :param trusted_hosts: Domains not to emit warnings for when not using
            HTTPS.
        """
        super().__init__(*args, **kwargs)

        # Namespace the attribute with "pip_" just in case to prevent
        # possible conflicts with the base class.
        self.pip_trusted_origins: list[tuple[str, int | None]] = []
        self.pip_proxy = None

        # Attach our User Agent to the request
        self.headers["User-Agent"] = user_agent()

        # Attach our Authentication handler to the session
        self.auth = MultiDomainBasicAuth(index_urls=index_urls)

        # Create our urllib3.Retry instance which will allow us to customize
        # how we handle retries.
        retries = urllib3.Retry(
            # Set the total number of retries that a particular request can
            # have.
            total=retries,
            # A 503 error from PyPI typically means that the Fastly -> Origin
            # connection got interrupted in some way. A 503 error in general
            # is typically considered a transient error so we'll go ahead and
            # retry it.
            # A 500 may indicate transient error in Amazon S3
            # A 502 may be a transient error from a CDN like CloudFlare or CloudFront
            # A 520 or 527 - may indicate transient error in CloudFlare
            status_forcelist=[500, 502, 503, 520, 527],
            # Add a small amount of back off between failed requests in
            # order to prevent hammering the service.
            backoff_factor=0.25,
        )  # type: ignore

        # Our Insecure HTTPAdapter disables HTTPS validation. It does not
        # support caching so we'll use it for all http:// URLs.
        # If caching is disabled, we will also use it for
        # https:// hosts that we've marked as ignoring
        # TLS errors for (trusted-hosts).
        insecure_adapter = InsecureHTTPAdapter(max_retries=retries)

        # We want to _only_ cache responses on securely fetched origins or when
        # the host is specified as trusted. We do this because
        # we can't validate the response of an insecurely/untrusted fetched
        # origin, and we don't want someone to be able to poison the cache and
        # require manual eviction from the cache to fix it.
        if cache:
            secure_adapter = CacheControlAdapter(
                cache=SafeFileCache(cache),
                max_retries=retries,
                ssl_context=ssl_context,
            )
            self._trusted_host_adapter = InsecureCacheControlAdapter(
                cache=SafeFileCache(cache),
                max_retries=retries,
            )
        else:
            secure_adapter = HTTPAdapter(max_retries=retries, ssl_context=ssl_context)
            self._trusted_host_adapter = insecure_adapter

        self.mount("https://", secure_adapter)
        self.mount("http://", insecure_adapter)

        # Enable file:// urls
        self.mount("file://", LocalFSAdapter())

        for host in trusted_hosts:
            self.add_trusted_host(host, suppress_logging=True)

    def update_index_urls(self, new_index_urls: list[str]) -> None:
        """
        :param new_index_urls: New index urls to update the authentication
            handler with.
        """
        self.auth.index_urls = new_index_urls

    def add_trusted_host(
        self, host: str, source: str | None = None, suppress_logging: bool = False
    ) -> None:
        """
        :param host: It is okay to provide a host that has previously been
            added.
        :param source: An optional source string, for logging where the host
            string came from.
        """
        if not suppress_logging:
            msg = f"adding trusted host: {host!r}"
            if source is not None:
                msg += f" (from {source})"
            logger.info(msg)

        parsed_host, parsed_port = parse_netloc(host)
        if parsed_host is None:
            raise ValueError(f"Trusted host URL must include a host part: {host!r}")
        if (parsed_host, parsed_port) not in self.pip_trusted_origins:
            self.pip_trusted_origins.append((parsed_host, parsed_port))

        self.mount(
            build_url_from_netloc(host, scheme="http") + "/", self._trusted_host_adapter
        )
        self.mount(build_url_from_netloc(host) + "/", self._trusted_host_adapter)
        if not parsed_port:
            self.mount(
                build_url_from_netloc(host, scheme="http") + ":",
                self._trusted_host_adapter,
            )
            # Mount wildcard ports for the same host.
            self.mount(build_url_from_netloc(host) + ":", self._trusted_host_adapter)

    def iter_secure_origins(self) -> Generator[SecureOrigin, None, None]:
        yield from SECURE_ORIGINS
        for host, port in self.pip_trusted_origins:
            yield ("*", host, "*" if port is None else port)

    def is_secure_origin(self, location: Link) -> bool:
        # Determine if this url used a secure transport mechanism
        parsed = urllib.parse.urlparse(str(location))
        origin_protocol, origin_host, origin_port = (
            parsed.scheme,
            parsed.hostname,
            parsed.port,
        )

        # The protocol to use to see if the protocol matches.
        # Don't count the repository type as part of the protocol: in
        # cases such as "git+ssh", only use "ssh". (I.e., Only verify against
        # the last scheme.)
        origin_protocol = origin_protocol.rsplit("+", 1)[-1]

        # Determine if our origin is a secure origin by looking through our
        # hardcoded list of secure origins, as well as any additional ones
        # configured on this PackageFinder instance.
        for secure_origin in self.iter_secure_origins():
            secure_protocol, secure_host, secure_port = secure_origin
            if origin_protocol != secure_protocol and secure_protocol != "*":
                continue

            try:
                addr = ipaddress.ip_address(origin_host or "")
                network = ipaddress.ip_network(secure_host)
            except ValueError:
                # We don't have both a valid address or a valid network, so
                # we'll check this origin against hostnames.
                if (
                    origin_host
                    and origin_host.lower() != secure_host.lower()
                    and secure_host != "*"
                ):
                    continue
            else:
                # We have a valid address and network, so see if the address
                # is contained within the network.
                if addr not in network:
                    continue

            # Check to see if the port matches.
            if (
                origin_port != secure_port
                and secure_port != "*"
                and secure_port is not None
            ):
                continue

            # If we've gotten here, then this origin matches the current
            # secure origin and we should return True
            return True

        # If we've gotten to this point, then the origin isn't secure and we
        # will not accept it as a valid location to search. We will however
        # log a warning that we are ignoring it.
        logger.warning(
            "The repository located at %s is not a trusted or secure host and "
            "is being ignored. If this repository is available via HTTPS we "
            "recommend you use HTTPS instead, otherwise you may silence "
            "this warning and allow it anyway with '--trusted-host %s'.",
            origin_host,
            origin_host,
        )

        return False

    def request(self, method: str, url: str, *args: Any, **kwargs: Any) -> Response:
        # Allow setting a default timeout on a session
        kwargs.setdefault("timeout", self.timeout)
        # Allow setting a default proxies on a session
        kwargs.setdefault("proxies", self.proxies)

        # Dispatch the actual request
        return super().request(method, url, *args, **kwargs)

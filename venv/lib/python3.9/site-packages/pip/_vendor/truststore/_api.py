import os
import platform
import socket
import ssl
import sys
import typing

import _ssl

from ._ssl_constants import (
    _original_SSLContext,
    _original_super_SSLContext,
    _truststore_SSLContext_dunder_class,
    _truststore_SSLContext_super_class,
)

if platform.system() == "Windows":
    from ._windows import _configure_context, _verify_peercerts_impl
elif platform.system() == "Darwin":
    from ._macos import _configure_context, _verify_peercerts_impl
else:
    from ._openssl import _configure_context, _verify_peercerts_impl

if typing.TYPE_CHECKING:
    from typing_extensions import Buffer

# From typeshed/stdlib/ssl.pyi
_StrOrBytesPath: typing.TypeAlias = str | bytes | os.PathLike[str] | os.PathLike[bytes]
_PasswordType: typing.TypeAlias = str | bytes | typing.Callable[[], str | bytes]


def inject_into_ssl() -> None:
    """Injects the :class:`truststore.SSLContext` into the ``ssl``
    module by replacing :class:`ssl.SSLContext`.
    """
    setattr(ssl, "SSLContext", SSLContext)
    # urllib3 holds on to its own reference of ssl.SSLContext
    # so we need to replace that reference too.
    try:
        import pip._vendor.urllib3.util.ssl_ as urllib3_ssl

        setattr(urllib3_ssl, "SSLContext", SSLContext)
    except ImportError:
        pass

    # requests starting with 2.32.0 added a preloaded SSL context to improve concurrent performance;
    # this unfortunately leads to a RecursionError, which can be avoided by patching the preloaded SSL context with
    # the truststore patched instance
    # also see https://github.com/psf/requests/pull/6667
    try:
        from pip._vendor.requests import adapters as requests_adapters

        preloaded_context = getattr(requests_adapters, "_preloaded_ssl_context", None)
        if preloaded_context is not None:
            setattr(
                requests_adapters,
                "_preloaded_ssl_context",
                SSLContext(ssl.PROTOCOL_TLS_CLIENT),
            )
    except ImportError:
        pass


def extract_from_ssl() -> None:
    """Restores the :class:`ssl.SSLContext` class to its original state"""
    setattr(ssl, "SSLContext", _original_SSLContext)
    try:
        import pip._vendor.urllib3.util.ssl_ as urllib3_ssl

        urllib3_ssl.SSLContext = _original_SSLContext  # type: ignore[assignment]
    except ImportError:
        pass


class SSLContext(_truststore_SSLContext_super_class):  # type: ignore[misc]
    """SSLContext API that uses system certificates on all platforms"""

    @property  # type: ignore[misc]
    def __class__(self) -> type:
        # Dirty hack to get around isinstance() checks
        # for ssl.SSLContext instances in aiohttp/trustme
        # when using non-CPython implementations.
        return _truststore_SSLContext_dunder_class or SSLContext

    def __init__(self, protocol: int = None) -> None:  # type: ignore[assignment]
        self._ctx = _original_SSLContext(protocol)

        class TruststoreSSLObject(ssl.SSLObject):
            # This object exists because wrap_bio() doesn't
            # immediately do the handshake so we need to do
            # certificate verifications after SSLObject.do_handshake()

            def do_handshake(self) -> None:
                ret = super().do_handshake()
                _verify_peercerts(self, server_hostname=self.server_hostname)
                return ret

        self._ctx.sslobject_class = TruststoreSSLObject

    def wrap_socket(
        self,
        sock: socket.socket,
        server_side: bool = False,
        do_handshake_on_connect: bool = True,
        suppress_ragged_eofs: bool = True,
        server_hostname: str | None = None,
        session: ssl.SSLSession | None = None,
    ) -> ssl.SSLSocket:
        # Use a context manager here because the
        # inner SSLContext holds on to our state
        # but also does the actual handshake.
        with _configure_context(self._ctx):
            ssl_sock = self._ctx.wrap_socket(
                sock,
                server_side=server_side,
                server_hostname=server_hostname,
                do_handshake_on_connect=do_handshake_on_connect,
                suppress_ragged_eofs=suppress_ragged_eofs,
                session=session,
            )
        try:
            _verify_peercerts(ssl_sock, server_hostname=server_hostname)
        except Exception:
            ssl_sock.close()
            raise
        return ssl_sock

    def wrap_bio(
        self,
        incoming: ssl.MemoryBIO,
        outgoing: ssl.MemoryBIO,
        server_side: bool = False,
        server_hostname: str | None = None,
        session: ssl.SSLSession | None = None,
    ) -> ssl.SSLObject:
        with _configure_context(self._ctx):
            ssl_obj = self._ctx.wrap_bio(
                incoming,
                outgoing,
                server_hostname=server_hostname,
                server_side=server_side,
                session=session,
            )
        return ssl_obj

    def load_verify_locations(
        self,
        cafile: str | bytes | os.PathLike[str] | os.PathLike[bytes] | None = None,
        capath: str | bytes | os.PathLike[str] | os.PathLike[bytes] | None = None,
        cadata: typing.Union[str, "Buffer", None] = None,
    ) -> None:
        return self._ctx.load_verify_locations(
            cafile=cafile, capath=capath, cadata=cadata
        )

    def load_cert_chain(
        self,
        certfile: _StrOrBytesPath,
        keyfile: _StrOrBytesPath | None = None,
        password: _PasswordType | None = None,
    ) -> None:
        return self._ctx.load_cert_chain(
            certfile=certfile, keyfile=keyfile, password=password
        )

    def load_default_certs(
        self, purpose: ssl.Purpose = ssl.Purpose.SERVER_AUTH
    ) -> None:
        return self._ctx.load_default_certs(purpose)

    def set_alpn_protocols(self, alpn_protocols: typing.Iterable[str]) -> None:
        return self._ctx.set_alpn_protocols(alpn_protocols)

    def set_npn_protocols(self, npn_protocols: typing.Iterable[str]) -> None:
        return self._ctx.set_npn_protocols(npn_protocols)

    def set_ciphers(self, __cipherlist: str) -> None:
        return self._ctx.set_ciphers(__cipherlist)

    def get_ciphers(self) -> typing.Any:
        return self._ctx.get_ciphers()

    def session_stats(self) -> dict[str, int]:
        return self._ctx.session_stats()

    def cert_store_stats(self) -> dict[str, int]:
        raise NotImplementedError()

    def set_default_verify_paths(self) -> None:
        self._ctx.set_default_verify_paths()

    @typing.overload
    def get_ca_certs(
        self, binary_form: typing.Literal[False] = ...
    ) -> list[typing.Any]: ...

    @typing.overload
    def get_ca_certs(self, binary_form: typing.Literal[True] = ...) -> list[bytes]: ...

    @typing.overload
    def get_ca_certs(self, binary_form: bool = ...) -> typing.Any: ...

    def get_ca_certs(self, binary_form: bool = False) -> list[typing.Any] | list[bytes]:
        raise NotImplementedError()

    @property
    def check_hostname(self) -> bool:
        return self._ctx.check_hostname

    @check_hostname.setter
    def check_hostname(self, value: bool) -> None:
        self._ctx.check_hostname = value

    @property
    def hostname_checks_common_name(self) -> bool:
        return self._ctx.hostname_checks_common_name

    @hostname_checks_common_name.setter
    def hostname_checks_common_name(self, value: bool) -> None:
        self._ctx.hostname_checks_common_name = value

    @property
    def keylog_filename(self) -> str:
        return self._ctx.keylog_filename

    @keylog_filename.setter
    def keylog_filename(self, value: str) -> None:
        self._ctx.keylog_filename = value

    @property
    def maximum_version(self) -> ssl.TLSVersion:
        return self._ctx.maximum_version

    @maximum_version.setter
    def maximum_version(self, value: ssl.TLSVersion) -> None:
        _original_super_SSLContext.maximum_version.__set__(  # type: ignore[attr-defined]
            self._ctx, value
        )

    @property
    def minimum_version(self) -> ssl.TLSVersion:
        return self._ctx.minimum_version

    @minimum_version.setter
    def minimum_version(self, value: ssl.TLSVersion) -> None:
        _original_super_SSLContext.minimum_version.__set__(  # type: ignore[attr-defined]
            self._ctx, value
        )

    @property
    def options(self) -> ssl.Options:
        return self._ctx.options

    @options.setter
    def options(self, value: ssl.Options) -> None:
        _original_super_SSLContext.options.__set__(  # type: ignore[attr-defined]
            self._ctx, value
        )

    @property
    def post_handshake_auth(self) -> bool:
        return self._ctx.post_handshake_auth

    @post_handshake_auth.setter
    def post_handshake_auth(self, value: bool) -> None:
        self._ctx.post_handshake_auth = value

    @property
    def protocol(self) -> ssl._SSLMethod:
        return self._ctx.protocol

    @property
    def security_level(self) -> int:
        return self._ctx.security_level

    @property
    def verify_flags(self) -> ssl.VerifyFlags:
        return self._ctx.verify_flags

    @verify_flags.setter
    def verify_flags(self, value: ssl.VerifyFlags) -> None:
        _original_super_SSLContext.verify_flags.__set__(  # type: ignore[attr-defined]
            self._ctx, value
        )

    @property
    def verify_mode(self) -> ssl.VerifyMode:
        return self._ctx.verify_mode

    @verify_mode.setter
    def verify_mode(self, value: ssl.VerifyMode) -> None:
        _original_super_SSLContext.verify_mode.__set__(  # type: ignore[attr-defined]
            self._ctx, value
        )


# Python 3.13+ makes get_unverified_chain() a public API that only returns DER
# encoded certificates. We detect whether we need to call public_bytes() for 3.10->3.12
# Pre-3.13 returned None instead of an empty list from get_unverified_chain()
if sys.version_info >= (3, 13):

    def _get_unverified_chain_bytes(sslobj: ssl.SSLObject) -> list[bytes]:
        unverified_chain = sslobj.get_unverified_chain() or ()  # type: ignore[attr-defined]
        return [
            cert if isinstance(cert, bytes) else cert.public_bytes(_ssl.ENCODING_DER)
            for cert in unverified_chain
        ]

else:

    def _get_unverified_chain_bytes(sslobj: ssl.SSLObject) -> list[bytes]:
        unverified_chain = sslobj.get_unverified_chain() or ()  # type: ignore[attr-defined]
        return [cert.public_bytes(_ssl.ENCODING_DER) for cert in unverified_chain]


def _verify_peercerts(
    sock_or_sslobj: ssl.SSLSocket | ssl.SSLObject, server_hostname: str | None
) -> None:
    """
    Verifies the peer certificates from an SSLSocket or SSLObject
    against the certificates in the OS trust store.
    """
    sslobj: ssl.SSLObject = sock_or_sslobj  # type: ignore[assignment]
    try:
        while not hasattr(sslobj, "get_unverified_chain"):
            sslobj = sslobj._sslobj  # type: ignore[attr-defined]
    except AttributeError:
        pass

    cert_bytes = _get_unverified_chain_bytes(sslobj)
    _verify_peercerts_impl(
        sock_or_sslobj.context, cert_bytes, server_hostname=server_hostname
    )

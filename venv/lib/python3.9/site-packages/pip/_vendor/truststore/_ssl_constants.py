import ssl
import sys
import typing

# Hold on to the original class so we can create it consistently
# even if we inject our own SSLContext into the ssl module.
_original_SSLContext = ssl.SSLContext
_original_super_SSLContext = super(_original_SSLContext, _original_SSLContext)

# CPython is known to be good, but non-CPython implementations
# may implement SSLContext differently so to be safe we don't
# subclass the SSLContext.

# This is returned by truststore.SSLContext.__class__()
_truststore_SSLContext_dunder_class: typing.Optional[type]

# This value is the superclass of truststore.SSLContext.
_truststore_SSLContext_super_class: type

if sys.implementation.name == "cpython":
    _truststore_SSLContext_super_class = _original_SSLContext
    _truststore_SSLContext_dunder_class = None
else:
    _truststore_SSLContext_super_class = object
    _truststore_SSLContext_dunder_class = _original_SSLContext


def _set_ssl_context_verify_mode(
    ssl_context: ssl.SSLContext, verify_mode: ssl.VerifyMode
) -> None:
    _original_super_SSLContext.verify_mode.__set__(ssl_context, verify_mode)  # type: ignore[attr-defined]

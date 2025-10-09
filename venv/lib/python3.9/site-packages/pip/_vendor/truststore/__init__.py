"""Verify certificates using native system trust stores"""

import sys as _sys

if _sys.version_info < (3, 10):
    raise ImportError("truststore requires Python 3.10 or later")

# Detect Python runtimes which don't implement SSLObject.get_unverified_chain() API
# This API only became public in Python 3.13 but was available in CPython and PyPy since 3.10.
if _sys.version_info < (3, 13) and _sys.implementation.name not in ("cpython", "pypy"):
    try:
        import ssl as _ssl
    except ImportError:
        raise ImportError("truststore requires the 'ssl' module")
    else:
        _sslmem = _ssl.MemoryBIO()
        _sslobj = _ssl.create_default_context().wrap_bio(
            _sslmem,
            _sslmem,
        )
        try:
            while not hasattr(_sslobj, "get_unverified_chain"):
                _sslobj = _sslobj._sslobj  # type: ignore[attr-defined]
        except AttributeError:
            raise ImportError(
                "truststore requires peer certificate chain APIs to be available"
            ) from None

        del _ssl, _sslobj, _sslmem  # noqa: F821

from ._api import SSLContext, extract_from_ssl, inject_into_ssl  # noqa: E402

del _api, _sys  # type: ignore[name-defined] # noqa: F821

__all__ = ["SSLContext", "inject_into_ssl", "extract_from_ssl"]
__version__ = "0.10.1"

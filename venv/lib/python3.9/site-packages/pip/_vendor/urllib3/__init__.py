"""
Python HTTP library with thread-safe connection pooling, file post support, user friendly, and more
"""
from __future__ import absolute_import

# Set default logging handler to avoid "No handler found" warnings.
import logging
import warnings
from logging import NullHandler

from . import exceptions
from ._version import __version__
from .connectionpool import HTTPConnectionPool, HTTPSConnectionPool, connection_from_url
from .filepost import encode_multipart_formdata
from .poolmanager import PoolManager, ProxyManager, proxy_from_url
from .response import HTTPResponse
from .util.request import make_headers
from .util.retry import Retry
from .util.timeout import Timeout
from .util.url import get_host

# === NOTE TO REPACKAGERS AND VENDORS ===
# Please delete this block, this logic is only
# for urllib3 being distributed via PyPI.
# See: https://github.com/urllib3/urllib3/issues/2680
try:
    import urllib3_secure_extra  # type: ignore # noqa: F401
except ImportError:
    pass
else:
    warnings.warn(
        "'urllib3[secure]' extra is deprecated and will be removed "
        "in a future release of urllib3 2.x. Read more in this issue: "
        "https://github.com/urllib3/urllib3/issues/2680",
        category=DeprecationWarning,
        stacklevel=2,
    )

__author__ = "Andrey Petrov (andrey.petrov@shazow.net)"
__license__ = "MIT"
__version__ = __version__

__all__ = (
    "HTTPConnectionPool",
    "HTTPSConnectionPool",
    "PoolManager",
    "ProxyManager",
    "HTTPResponse",
    "Retry",
    "Timeout",
    "add_stderr_logger",
    "connection_from_url",
    "disable_warnings",
    "encode_multipart_formdata",
    "get_host",
    "make_headers",
    "proxy_from_url",
)

logging.getLogger(__name__).addHandler(NullHandler())


def add_stderr_logger(level=logging.DEBUG):
    """
    Helper for quickly adding a StreamHandler to the logger. Useful for
    debugging.

    Returns the handler after adding it.
    """
    # This method needs to be in this __init__.py to get the __name__ correct
    # even if urllib3 is vendored within another package.
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.debug("Added a stderr logging handler to logger: %s", __name__)
    return handler


# ... Clean up.
del NullHandler


# All warning filters *must* be appended unless you're really certain that they
# shouldn't be: otherwise, it's very hard for users to use most Python
# mechanisms to silence them.
# SecurityWarning's always go off by default.
warnings.simplefilter("always", exceptions.SecurityWarning, append=True)
# SubjectAltNameWarning's should go off once per host
warnings.simplefilter("default", exceptions.SubjectAltNameWarning, append=True)
# InsecurePlatformWarning's don't vary between requests, so we keep it default.
warnings.simplefilter("default", exceptions.InsecurePlatformWarning, append=True)
# SNIMissingWarnings should go off only once.
warnings.simplefilter("default", exceptions.SNIMissingWarning, append=True)


def disable_warnings(category=exceptions.HTTPWarning):
    """
    Helper for quickly disabling all urllib3 warnings.
    """
    warnings.simplefilter("ignore", category)

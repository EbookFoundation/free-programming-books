from __future__ import absolute_import

import email
import logging
import re
import time
import warnings
from collections import namedtuple
from itertools import takewhile

from ..exceptions import (
    ConnectTimeoutError,
    InvalidHeader,
    MaxRetryError,
    ProtocolError,
    ProxyError,
    ReadTimeoutError,
    ResponseError,
)
from ..packages import six

log = logging.getLogger(__name__)


# Data structure for representing the metadata of requests that result in a retry.
RequestHistory = namedtuple(
    "RequestHistory", ["method", "url", "error", "status", "redirect_location"]
)


# TODO: In v2 we can remove this sentinel and metaclass with deprecated options.
_Default = object()


class _RetryMeta(type):
    @property
    def DEFAULT_METHOD_WHITELIST(cls):
        warnings.warn(
            "Using 'Retry.DEFAULT_METHOD_WHITELIST' is deprecated and "
            "will be removed in v2.0. Use 'Retry.DEFAULT_ALLOWED_METHODS' instead",
            DeprecationWarning,
        )
        return cls.DEFAULT_ALLOWED_METHODS

    @DEFAULT_METHOD_WHITELIST.setter
    def DEFAULT_METHOD_WHITELIST(cls, value):
        warnings.warn(
            "Using 'Retry.DEFAULT_METHOD_WHITELIST' is deprecated and "
            "will be removed in v2.0. Use 'Retry.DEFAULT_ALLOWED_METHODS' instead",
            DeprecationWarning,
        )
        cls.DEFAULT_ALLOWED_METHODS = value

    @property
    def DEFAULT_REDIRECT_HEADERS_BLACKLIST(cls):
        warnings.warn(
            "Using 'Retry.DEFAULT_REDIRECT_HEADERS_BLACKLIST' is deprecated and "
            "will be removed in v2.0. Use 'Retry.DEFAULT_REMOVE_HEADERS_ON_REDIRECT' instead",
            DeprecationWarning,
        )
        return cls.DEFAULT_REMOVE_HEADERS_ON_REDIRECT

    @DEFAULT_REDIRECT_HEADERS_BLACKLIST.setter
    def DEFAULT_REDIRECT_HEADERS_BLACKLIST(cls, value):
        warnings.warn(
            "Using 'Retry.DEFAULT_REDIRECT_HEADERS_BLACKLIST' is deprecated and "
            "will be removed in v2.0. Use 'Retry.DEFAULT_REMOVE_HEADERS_ON_REDIRECT' instead",
            DeprecationWarning,
        )
        cls.DEFAULT_REMOVE_HEADERS_ON_REDIRECT = value

    @property
    def BACKOFF_MAX(cls):
        warnings.warn(
            "Using 'Retry.BACKOFF_MAX' is deprecated and "
            "will be removed in v2.0. Use 'Retry.DEFAULT_BACKOFF_MAX' instead",
            DeprecationWarning,
        )
        return cls.DEFAULT_BACKOFF_MAX

    @BACKOFF_MAX.setter
    def BACKOFF_MAX(cls, value):
        warnings.warn(
            "Using 'Retry.BACKOFF_MAX' is deprecated and "
            "will be removed in v2.0. Use 'Retry.DEFAULT_BACKOFF_MAX' instead",
            DeprecationWarning,
        )
        cls.DEFAULT_BACKOFF_MAX = value


@six.add_metaclass(_RetryMeta)
class Retry(object):
    """Retry configuration.

    Each retry attempt will create a new Retry object with updated values, so
    they can be safely reused.

    Retries can be defined as a default for a pool::

        retries = Retry(connect=5, read=2, redirect=5)
        http = PoolManager(retries=retries)
        response = http.request('GET', 'http://example.com/')

    Or per-request (which overrides the default for the pool)::

        response = http.request('GET', 'http://example.com/', retries=Retry(10))

    Retries can be disabled by passing ``False``::

        response = http.request('GET', 'http://example.com/', retries=False)

    Errors will be wrapped in :class:`~urllib3.exceptions.MaxRetryError` unless
    retries are disabled, in which case the causing exception will be raised.

    :param int total:
        Total number of retries to allow. Takes precedence over other counts.

        Set to ``None`` to remove this constraint and fall back on other
        counts.

        Set to ``0`` to fail on the first retry.

        Set to ``False`` to disable and imply ``raise_on_redirect=False``.

    :param int connect:
        How many connection-related errors to retry on.

        These are errors raised before the request is sent to the remote server,
        which we assume has not triggered the server to process the request.

        Set to ``0`` to fail on the first retry of this type.

    :param int read:
        How many times to retry on read errors.

        These errors are raised after the request was sent to the server, so the
        request may have side-effects.

        Set to ``0`` to fail on the first retry of this type.

    :param int redirect:
        How many redirects to perform. Limit this to avoid infinite redirect
        loops.

        A redirect is a HTTP response with a status code 301, 302, 303, 307 or
        308.

        Set to ``0`` to fail on the first retry of this type.

        Set to ``False`` to disable and imply ``raise_on_redirect=False``.

    :param int status:
        How many times to retry on bad status codes.

        These are retries made on responses, where status code matches
        ``status_forcelist``.

        Set to ``0`` to fail on the first retry of this type.

    :param int other:
        How many times to retry on other errors.

        Other errors are errors that are not connect, read, redirect or status errors.
        These errors might be raised after the request was sent to the server, so the
        request might have side-effects.

        Set to ``0`` to fail on the first retry of this type.

        If ``total`` is not set, it's a good idea to set this to 0 to account
        for unexpected edge cases and avoid infinite retry loops.

    :param iterable allowed_methods:
        Set of uppercased HTTP method verbs that we should retry on.

        By default, we only retry on methods which are considered to be
        idempotent (multiple requests with the same parameters end with the
        same state). See :attr:`Retry.DEFAULT_ALLOWED_METHODS`.

        Set to a ``False`` value to retry on any verb.

        .. warning::

            Previously this parameter was named ``method_whitelist``, that
            usage is deprecated in v1.26.0 and will be removed in v2.0.

    :param iterable status_forcelist:
        A set of integer HTTP status codes that we should force a retry on.
        A retry is initiated if the request method is in ``allowed_methods``
        and the response status code is in ``status_forcelist``.

        By default, this is disabled with ``None``.

    :param float backoff_factor:
        A backoff factor to apply between attempts after the second try
        (most errors are resolved immediately by a second try without a
        delay). urllib3 will sleep for::

            {backoff factor} * (2 ** ({number of total retries} - 1))

        seconds. If the backoff_factor is 0.1, then :func:`.sleep` will sleep
        for [0.0s, 0.2s, 0.4s, ...] between retries. It will never be longer
        than :attr:`Retry.DEFAULT_BACKOFF_MAX`.

        By default, backoff is disabled (set to 0).

    :param bool raise_on_redirect: Whether, if the number of redirects is
        exhausted, to raise a MaxRetryError, or to return a response with a
        response code in the 3xx range.

    :param bool raise_on_status: Similar meaning to ``raise_on_redirect``:
        whether we should raise an exception, or return a response,
        if status falls in ``status_forcelist`` range and retries have
        been exhausted.

    :param tuple history: The history of the request encountered during
        each call to :meth:`~Retry.increment`. The list is in the order
        the requests occurred. Each list item is of class :class:`RequestHistory`.

    :param bool respect_retry_after_header:
        Whether to respect Retry-After header on status codes defined as
        :attr:`Retry.RETRY_AFTER_STATUS_CODES` or not.

    :param iterable remove_headers_on_redirect:
        Sequence of headers to remove from the request when a response
        indicating a redirect is returned before firing off the redirected
        request.
    """

    #: Default methods to be used for ``allowed_methods``
    DEFAULT_ALLOWED_METHODS = frozenset(
        ["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"]
    )

    #: Default status codes to be used for ``status_forcelist``
    RETRY_AFTER_STATUS_CODES = frozenset([413, 429, 503])

    #: Default headers to be used for ``remove_headers_on_redirect``
    DEFAULT_REMOVE_HEADERS_ON_REDIRECT = frozenset(
        ["Cookie", "Authorization", "Proxy-Authorization"]
    )

    #: Maximum backoff time.
    DEFAULT_BACKOFF_MAX = 120

    def __init__(
        self,
        total=10,
        connect=None,
        read=None,
        redirect=None,
        status=None,
        other=None,
        allowed_methods=_Default,
        status_forcelist=None,
        backoff_factor=0,
        raise_on_redirect=True,
        raise_on_status=True,
        history=None,
        respect_retry_after_header=True,
        remove_headers_on_redirect=_Default,
        # TODO: Deprecated, remove in v2.0
        method_whitelist=_Default,
    ):

        if method_whitelist is not _Default:
            if allowed_methods is not _Default:
                raise ValueError(
                    "Using both 'allowed_methods' and "
                    "'method_whitelist' together is not allowed. "
                    "Instead only use 'allowed_methods'"
                )
            warnings.warn(
                "Using 'method_whitelist' with Retry is deprecated and "
                "will be removed in v2.0. Use 'allowed_methods' instead",
                DeprecationWarning,
                stacklevel=2,
            )
            allowed_methods = method_whitelist
        if allowed_methods is _Default:
            allowed_methods = self.DEFAULT_ALLOWED_METHODS
        if remove_headers_on_redirect is _Default:
            remove_headers_on_redirect = self.DEFAULT_REMOVE_HEADERS_ON_REDIRECT

        self.total = total
        self.connect = connect
        self.read = read
        self.status = status
        self.other = other

        if redirect is False or total is False:
            redirect = 0
            raise_on_redirect = False

        self.redirect = redirect
        self.status_forcelist = status_forcelist or set()
        self.allowed_methods = allowed_methods
        self.backoff_factor = backoff_factor
        self.raise_on_redirect = raise_on_redirect
        self.raise_on_status = raise_on_status
        self.history = history or tuple()
        self.respect_retry_after_header = respect_retry_after_header
        self.remove_headers_on_redirect = frozenset(
            [h.lower() for h in remove_headers_on_redirect]
        )

    def new(self, **kw):
        params = dict(
            total=self.total,
            connect=self.connect,
            read=self.read,
            redirect=self.redirect,
            status=self.status,
            other=self.other,
            status_forcelist=self.status_forcelist,
            backoff_factor=self.backoff_factor,
            raise_on_redirect=self.raise_on_redirect,
            raise_on_status=self.raise_on_status,
            history=self.history,
            remove_headers_on_redirect=self.remove_headers_on_redirect,
            respect_retry_after_header=self.respect_retry_after_header,
        )

        # TODO: If already given in **kw we use what's given to us
        # If not given we need to figure out what to pass. We decide
        # based on whether our class has the 'method_whitelist' property
        # and if so we pass the deprecated 'method_whitelist' otherwise
        # we use 'allowed_methods'. Remove in v2.0
        if "method_whitelist" not in kw and "allowed_methods" not in kw:
            if "method_whitelist" in self.__dict__:
                warnings.warn(
                    "Using 'method_whitelist' with Retry is deprecated and "
                    "will be removed in v2.0. Use 'allowed_methods' instead",
                    DeprecationWarning,
                )
                params["method_whitelist"] = self.allowed_methods
            else:
                params["allowed_methods"] = self.allowed_methods

        params.update(kw)
        return type(self)(**params)

    @classmethod
    def from_int(cls, retries, redirect=True, default=None):
        """Backwards-compatibility for the old retries format."""
        if retries is None:
            retries = default if default is not None else cls.DEFAULT

        if isinstance(retries, Retry):
            return retries

        redirect = bool(redirect) and None
        new_retries = cls(retries, redirect=redirect)
        log.debug("Converted retries value: %r -> %r", retries, new_retries)
        return new_retries

    def get_backoff_time(self):
        """Formula for computing the current backoff

        :rtype: float
        """
        # We want to consider only the last consecutive errors sequence (Ignore redirects).
        consecutive_errors_len = len(
            list(
                takewhile(lambda x: x.redirect_location is None, reversed(self.history))
            )
        )
        if consecutive_errors_len <= 1:
            return 0

        backoff_value = self.backoff_factor * (2 ** (consecutive_errors_len - 1))
        return min(self.DEFAULT_BACKOFF_MAX, backoff_value)

    def parse_retry_after(self, retry_after):
        # Whitespace: https://tools.ietf.org/html/rfc7230#section-3.2.4
        if re.match(r"^\s*[0-9]+\s*$", retry_after):
            seconds = int(retry_after)
        else:
            retry_date_tuple = email.utils.parsedate_tz(retry_after)
            if retry_date_tuple is None:
                raise InvalidHeader("Invalid Retry-After header: %s" % retry_after)
            if retry_date_tuple[9] is None:  # Python 2
                # Assume UTC if no timezone was specified
                # On Python2.7, parsedate_tz returns None for a timezone offset
                # instead of 0 if no timezone is given, where mktime_tz treats
                # a None timezone offset as local time.
                retry_date_tuple = retry_date_tuple[:9] + (0,) + retry_date_tuple[10:]

            retry_date = email.utils.mktime_tz(retry_date_tuple)
            seconds = retry_date - time.time()

        if seconds < 0:
            seconds = 0

        return seconds

    def get_retry_after(self, response):
        """Get the value of Retry-After in seconds."""

        retry_after = response.headers.get("Retry-After")

        if retry_after is None:
            return None

        return self.parse_retry_after(retry_after)

    def sleep_for_retry(self, response=None):
        retry_after = self.get_retry_after(response)
        if retry_after:
            time.sleep(retry_after)
            return True

        return False

    def _sleep_backoff(self):
        backoff = self.get_backoff_time()
        if backoff <= 0:
            return
        time.sleep(backoff)

    def sleep(self, response=None):
        """Sleep between retry attempts.

        This method will respect a server's ``Retry-After`` response header
        and sleep the duration of the time requested. If that is not present, it
        will use an exponential backoff. By default, the backoff factor is 0 and
        this method will return immediately.
        """

        if self.respect_retry_after_header and response:
            slept = self.sleep_for_retry(response)
            if slept:
                return

        self._sleep_backoff()

    def _is_connection_error(self, err):
        """Errors when we're fairly sure that the server did not receive the
        request, so it should be safe to retry.
        """
        if isinstance(err, ProxyError):
            err = err.original_error
        return isinstance(err, ConnectTimeoutError)

    def _is_read_error(self, err):
        """Errors that occur after the request has been started, so we should
        assume that the server began processing it.
        """
        return isinstance(err, (ReadTimeoutError, ProtocolError))

    def _is_method_retryable(self, method):
        """Checks if a given HTTP method should be retried upon, depending if
        it is included in the allowed_methods
        """
        # TODO: For now favor if the Retry implementation sets its own method_whitelist
        # property outside of our constructor to avoid breaking custom implementations.
        if "method_whitelist" in self.__dict__:
            warnings.warn(
                "Using 'method_whitelist' with Retry is deprecated and "
                "will be removed in v2.0. Use 'allowed_methods' instead",
                DeprecationWarning,
            )
            allowed_methods = self.method_whitelist
        else:
            allowed_methods = self.allowed_methods

        if allowed_methods and method.upper() not in allowed_methods:
            return False
        return True

    def is_retry(self, method, status_code, has_retry_after=False):
        """Is this method/status code retryable? (Based on allowlists and control
        variables such as the number of total retries to allow, whether to
        respect the Retry-After header, whether this header is present, and
        whether the returned status code is on the list of status codes to
        be retried upon on the presence of the aforementioned header)
        """
        if not self._is_method_retryable(method):
            return False

        if self.status_forcelist and status_code in self.status_forcelist:
            return True

        return (
            self.total
            and self.respect_retry_after_header
            and has_retry_after
            and (status_code in self.RETRY_AFTER_STATUS_CODES)
        )

    def is_exhausted(self):
        """Are we out of retries?"""
        retry_counts = (
            self.total,
            self.connect,
            self.read,
            self.redirect,
            self.status,
            self.other,
        )
        retry_counts = list(filter(None, retry_counts))
        if not retry_counts:
            return False

        return min(retry_counts) < 0

    def increment(
        self,
        method=None,
        url=None,
        response=None,
        error=None,
        _pool=None,
        _stacktrace=None,
    ):
        """Return a new Retry object with incremented retry counters.

        :param response: A response object, or None, if the server did not
            return a response.
        :type response: :class:`~urllib3.response.HTTPResponse`
        :param Exception error: An error encountered during the request, or
            None if the response was received successfully.

        :return: A new ``Retry`` object.
        """
        if self.total is False and error:
            # Disabled, indicate to re-raise the error.
            raise six.reraise(type(error), error, _stacktrace)

        total = self.total
        if total is not None:
            total -= 1

        connect = self.connect
        read = self.read
        redirect = self.redirect
        status_count = self.status
        other = self.other
        cause = "unknown"
        status = None
        redirect_location = None

        if error and self._is_connection_error(error):
            # Connect retry?
            if connect is False:
                raise six.reraise(type(error), error, _stacktrace)
            elif connect is not None:
                connect -= 1

        elif error and self._is_read_error(error):
            # Read retry?
            if read is False or not self._is_method_retryable(method):
                raise six.reraise(type(error), error, _stacktrace)
            elif read is not None:
                read -= 1

        elif error:
            # Other retry?
            if other is not None:
                other -= 1

        elif response and response.get_redirect_location():
            # Redirect retry?
            if redirect is not None:
                redirect -= 1
            cause = "too many redirects"
            redirect_location = response.get_redirect_location()
            status = response.status

        else:
            # Incrementing because of a server error like a 500 in
            # status_forcelist and the given method is in the allowed_methods
            cause = ResponseError.GENERIC_ERROR
            if response and response.status:
                if status_count is not None:
                    status_count -= 1
                cause = ResponseError.SPECIFIC_ERROR.format(status_code=response.status)
                status = response.status

        history = self.history + (
            RequestHistory(method, url, error, status, redirect_location),
        )

        new_retry = self.new(
            total=total,
            connect=connect,
            read=read,
            redirect=redirect,
            status=status_count,
            other=other,
            history=history,
        )

        if new_retry.is_exhausted():
            raise MaxRetryError(_pool, url, error or ResponseError(cause))

        log.debug("Incremented Retry for (url='%s'): %r", url, new_retry)

        return new_retry

    def __repr__(self):
        return (
            "{cls.__name__}(total={self.total}, connect={self.connect}, "
            "read={self.read}, redirect={self.redirect}, status={self.status})"
        ).format(cls=type(self), self=self)

    def __getattr__(self, item):
        if item == "method_whitelist":
            # TODO: Remove this deprecated alias in v2.0
            warnings.warn(
                "Using 'method_whitelist' with Retry is deprecated and "
                "will be removed in v2.0. Use 'allowed_methods' instead",
                DeprecationWarning,
            )
            return self.allowed_methods
        try:
            return getattr(super(Retry, self), item)
        except AttributeError:
            return getattr(Retry, item)


# For backwards compatibility (equivalent to pre-v1.9):
Retry.DEFAULT = Retry(3)

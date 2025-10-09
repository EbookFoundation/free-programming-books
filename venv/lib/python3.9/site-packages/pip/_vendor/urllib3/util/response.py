from __future__ import absolute_import

from email.errors import MultipartInvariantViolationDefect, StartBoundaryNotFoundDefect

from ..exceptions import HeaderParsingError
from ..packages.six.moves import http_client as httplib


def is_fp_closed(obj):
    """
    Checks whether a given file-like object is closed.

    :param obj:
        The file-like object to check.
    """

    try:
        # Check `isclosed()` first, in case Python3 doesn't set `closed`.
        # GH Issue #928
        return obj.isclosed()
    except AttributeError:
        pass

    try:
        # Check via the official file-like-object way.
        return obj.closed
    except AttributeError:
        pass

    try:
        # Check if the object is a container for another file-like object that
        # gets released on exhaustion (e.g. HTTPResponse).
        return obj.fp is None
    except AttributeError:
        pass

    raise ValueError("Unable to determine whether fp is closed.")


def assert_header_parsing(headers):
    """
    Asserts whether all headers have been successfully parsed.
    Extracts encountered errors from the result of parsing headers.

    Only works on Python 3.

    :param http.client.HTTPMessage headers: Headers to verify.

    :raises urllib3.exceptions.HeaderParsingError:
        If parsing errors are found.
    """

    # This will fail silently if we pass in the wrong kind of parameter.
    # To make debugging easier add an explicit check.
    if not isinstance(headers, httplib.HTTPMessage):
        raise TypeError("expected httplib.Message, got {0}.".format(type(headers)))

    defects = getattr(headers, "defects", None)
    get_payload = getattr(headers, "get_payload", None)

    unparsed_data = None
    if get_payload:
        # get_payload is actually email.message.Message.get_payload;
        # we're only interested in the result if it's not a multipart message
        if not headers.is_multipart():
            payload = get_payload()

            if isinstance(payload, (bytes, str)):
                unparsed_data = payload
    if defects:
        # httplib is assuming a response body is available
        # when parsing headers even when httplib only sends
        # header data to parse_headers() This results in
        # defects on multipart responses in particular.
        # See: https://github.com/urllib3/urllib3/issues/800

        # So we ignore the following defects:
        # - StartBoundaryNotFoundDefect:
        #     The claimed start boundary was never found.
        # - MultipartInvariantViolationDefect:
        #     A message claimed to be a multipart but no subparts were found.
        defects = [
            defect
            for defect in defects
            if not isinstance(
                defect, (StartBoundaryNotFoundDefect, MultipartInvariantViolationDefect)
            )
        ]

    if defects or unparsed_data:
        raise HeaderParsingError(defects=defects, unparsed_data=unparsed_data)


def is_response_to_head(response):
    """
    Checks whether the request of a response has been a HEAD-request.
    Handles the quirks of AppEngine.

    :param http.client.HTTPResponse response:
        Response to check if the originating request
        used 'HEAD' as a method.
    """
    # FIXME: Can we do this somehow without accessing private httplib _method?
    method = response._method
    if isinstance(method, int):  # Platform-specific: Appengine
        return method == 3
    return method.upper() == "HEAD"

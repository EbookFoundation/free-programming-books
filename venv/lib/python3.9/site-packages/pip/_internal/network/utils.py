from collections.abc import Generator

from pip._vendor.requests.models import Response

from pip._internal.exceptions import NetworkConnectionError

# The following comments and HTTP headers were originally added by
# Donald Stufft in git commit 22c562429a61bb77172039e480873fb239dd8c03.
#
# We use Accept-Encoding: identity here because requests defaults to
# accepting compressed responses. This breaks in a variety of ways
# depending on how the server is configured.
# - Some servers will notice that the file isn't a compressible file
#   and will leave the file alone and with an empty Content-Encoding
# - Some servers will notice that the file is already compressed and
#   will leave the file alone, adding a Content-Encoding: gzip header
# - Some servers won't notice anything at all and will take a file
#   that's already been compressed and compress it again, and set
#   the Content-Encoding: gzip header
# By setting this to request only the identity encoding we're hoping
# to eliminate the third case.  Hopefully there does not exist a server
# which when given a file will notice it is already compressed and that
# you're not asking for a compressed file and will then decompress it
# before sending because if that's the case I don't think it'll ever be
# possible to make this work.
HEADERS: dict[str, str] = {"Accept-Encoding": "identity"}

DOWNLOAD_CHUNK_SIZE = 256 * 1024


def raise_for_status(resp: Response) -> None:
    http_error_msg = ""
    if isinstance(resp.reason, bytes):
        # We attempt to decode utf-8 first because some servers
        # choose to localize their reason strings. If the string
        # isn't utf-8, we fall back to iso-8859-1 for all other
        # encodings.
        try:
            reason = resp.reason.decode("utf-8")
        except UnicodeDecodeError:
            reason = resp.reason.decode("iso-8859-1")
    else:
        reason = resp.reason

    if 400 <= resp.status_code < 500:
        http_error_msg = (
            f"{resp.status_code} Client Error: {reason} for url: {resp.url}"
        )

    elif 500 <= resp.status_code < 600:
        http_error_msg = (
            f"{resp.status_code} Server Error: {reason} for url: {resp.url}"
        )

    if http_error_msg:
        raise NetworkConnectionError(http_error_msg, response=resp)


def response_chunks(
    response: Response, chunk_size: int = DOWNLOAD_CHUNK_SIZE
) -> Generator[bytes, None, None]:
    """Given a requests Response, provide the data chunks."""
    try:
        # Special case for urllib3.
        for chunk in response.raw.stream(
            chunk_size,
            # We use decode_content=False here because we don't
            # want urllib3 to mess with the raw bytes we get
            # from the server. If we decompress inside of
            # urllib3 then we cannot verify the checksum
            # because the checksum will be of the compressed
            # file. This breakage will only occur if the
            # server adds a Content-Encoding header, which
            # depends on how the server was configured:
            # - Some servers will notice that the file isn't a
            #   compressible file and will leave the file alone
            #   and with an empty Content-Encoding
            # - Some servers will notice that the file is
            #   already compressed and will leave the file
            #   alone and will add a Content-Encoding: gzip
            #   header
            # - Some servers won't notice anything at all and
            #   will take a file that's already been compressed
            #   and compress it again and set the
            #   Content-Encoding: gzip header
            #
            # By setting this not to decode automatically we
            # hope to eliminate problems with the second case.
            decode_content=False,
        ):
            yield chunk
    except AttributeError:
        # Standard file-like object.
        while True:
            chunk = response.raw.read(chunk_size)
            if not chunk:
                break
            yield chunk

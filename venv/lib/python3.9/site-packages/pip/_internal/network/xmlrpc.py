"""xmlrpclib.Transport implementation"""

import logging
import urllib.parse
import xmlrpc.client
from typing import TYPE_CHECKING

from pip._internal.exceptions import NetworkConnectionError
from pip._internal.network.session import PipSession
from pip._internal.network.utils import raise_for_status

if TYPE_CHECKING:
    from xmlrpc.client import _HostType, _Marshallable

    from _typeshed import SizedBuffer

logger = logging.getLogger(__name__)


class PipXmlrpcTransport(xmlrpc.client.Transport):
    """Provide a `xmlrpclib.Transport` implementation via a `PipSession`
    object.
    """

    def __init__(
        self, index_url: str, session: PipSession, use_datetime: bool = False
    ) -> None:
        super().__init__(use_datetime)
        index_parts = urllib.parse.urlparse(index_url)
        self._scheme = index_parts.scheme
        self._session = session

    def request(
        self,
        host: "_HostType",
        handler: str,
        request_body: "SizedBuffer",
        verbose: bool = False,
    ) -> tuple["_Marshallable", ...]:
        assert isinstance(host, str)
        parts = (self._scheme, host, handler, None, None, None)
        url = urllib.parse.urlunparse(parts)
        try:
            headers = {"Content-Type": "text/xml"}
            response = self._session.post(
                url,
                data=request_body,
                headers=headers,
                stream=True,
            )
            raise_for_status(response)
            self.verbose = verbose
            return self.parse_response(response.raw)
        except NetworkConnectionError as exc:
            assert exc.response
            logger.critical(
                "HTTP error %s while getting %s",
                exc.response.status_code,
                url,
            )
            raise

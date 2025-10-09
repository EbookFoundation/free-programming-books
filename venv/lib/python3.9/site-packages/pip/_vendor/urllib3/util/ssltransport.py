import io
import socket
import ssl

from ..exceptions import ProxySchemeUnsupported
from ..packages import six

SSL_BLOCKSIZE = 16384


class SSLTransport:
    """
    The SSLTransport wraps an existing socket and establishes an SSL connection.

    Contrary to Python's implementation of SSLSocket, it allows you to chain
    multiple TLS connections together. It's particularly useful if you need to
    implement TLS within TLS.

    The class supports most of the socket API operations.
    """

    @staticmethod
    def _validate_ssl_context_for_tls_in_tls(ssl_context):
        """
        Raises a ProxySchemeUnsupported if the provided ssl_context can't be used
        for TLS in TLS.

        The only requirement is that the ssl_context provides the 'wrap_bio'
        methods.
        """

        if not hasattr(ssl_context, "wrap_bio"):
            if six.PY2:
                raise ProxySchemeUnsupported(
                    "TLS in TLS requires SSLContext.wrap_bio() which isn't "
                    "supported on Python 2"
                )
            else:
                raise ProxySchemeUnsupported(
                    "TLS in TLS requires SSLContext.wrap_bio() which isn't "
                    "available on non-native SSLContext"
                )

    def __init__(
        self, socket, ssl_context, server_hostname=None, suppress_ragged_eofs=True
    ):
        """
        Create an SSLTransport around socket using the provided ssl_context.
        """
        self.incoming = ssl.MemoryBIO()
        self.outgoing = ssl.MemoryBIO()

        self.suppress_ragged_eofs = suppress_ragged_eofs
        self.socket = socket

        self.sslobj = ssl_context.wrap_bio(
            self.incoming, self.outgoing, server_hostname=server_hostname
        )

        # Perform initial handshake.
        self._ssl_io_loop(self.sslobj.do_handshake)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def fileno(self):
        return self.socket.fileno()

    def read(self, len=1024, buffer=None):
        return self._wrap_ssl_read(len, buffer)

    def recv(self, len=1024, flags=0):
        if flags != 0:
            raise ValueError("non-zero flags not allowed in calls to recv")
        return self._wrap_ssl_read(len)

    def recv_into(self, buffer, nbytes=None, flags=0):
        if flags != 0:
            raise ValueError("non-zero flags not allowed in calls to recv_into")
        if buffer and (nbytes is None):
            nbytes = len(buffer)
        elif nbytes is None:
            nbytes = 1024
        return self.read(nbytes, buffer)

    def sendall(self, data, flags=0):
        if flags != 0:
            raise ValueError("non-zero flags not allowed in calls to sendall")
        count = 0
        with memoryview(data) as view, view.cast("B") as byte_view:
            amount = len(byte_view)
            while count < amount:
                v = self.send(byte_view[count:])
                count += v

    def send(self, data, flags=0):
        if flags != 0:
            raise ValueError("non-zero flags not allowed in calls to send")
        response = self._ssl_io_loop(self.sslobj.write, data)
        return response

    def makefile(
        self, mode="r", buffering=None, encoding=None, errors=None, newline=None
    ):
        """
        Python's httpclient uses makefile and buffered io when reading HTTP
        messages and we need to support it.

        This is unfortunately a copy and paste of socket.py makefile with small
        changes to point to the socket directly.
        """
        if not set(mode) <= {"r", "w", "b"}:
            raise ValueError("invalid mode %r (only r, w, b allowed)" % (mode,))

        writing = "w" in mode
        reading = "r" in mode or not writing
        assert reading or writing
        binary = "b" in mode
        rawmode = ""
        if reading:
            rawmode += "r"
        if writing:
            rawmode += "w"
        raw = socket.SocketIO(self, rawmode)
        self.socket._io_refs += 1
        if buffering is None:
            buffering = -1
        if buffering < 0:
            buffering = io.DEFAULT_BUFFER_SIZE
        if buffering == 0:
            if not binary:
                raise ValueError("unbuffered streams must be binary")
            return raw
        if reading and writing:
            buffer = io.BufferedRWPair(raw, raw, buffering)
        elif reading:
            buffer = io.BufferedReader(raw, buffering)
        else:
            assert writing
            buffer = io.BufferedWriter(raw, buffering)
        if binary:
            return buffer
        text = io.TextIOWrapper(buffer, encoding, errors, newline)
        text.mode = mode
        return text

    def unwrap(self):
        self._ssl_io_loop(self.sslobj.unwrap)

    def close(self):
        self.socket.close()

    def getpeercert(self, binary_form=False):
        return self.sslobj.getpeercert(binary_form)

    def version(self):
        return self.sslobj.version()

    def cipher(self):
        return self.sslobj.cipher()

    def selected_alpn_protocol(self):
        return self.sslobj.selected_alpn_protocol()

    def selected_npn_protocol(self):
        return self.sslobj.selected_npn_protocol()

    def shared_ciphers(self):
        return self.sslobj.shared_ciphers()

    def compression(self):
        return self.sslobj.compression()

    def settimeout(self, value):
        self.socket.settimeout(value)

    def gettimeout(self):
        return self.socket.gettimeout()

    def _decref_socketios(self):
        self.socket._decref_socketios()

    def _wrap_ssl_read(self, len, buffer=None):
        try:
            return self._ssl_io_loop(self.sslobj.read, len, buffer)
        except ssl.SSLError as e:
            if e.errno == ssl.SSL_ERROR_EOF and self.suppress_ragged_eofs:
                return 0  # eof, return 0.
            else:
                raise

    def _ssl_io_loop(self, func, *args):
        """Performs an I/O loop between incoming/outgoing and the socket."""
        should_loop = True
        ret = None

        while should_loop:
            errno = None
            try:
                ret = func(*args)
            except ssl.SSLError as e:
                if e.errno not in (ssl.SSL_ERROR_WANT_READ, ssl.SSL_ERROR_WANT_WRITE):
                    # WANT_READ, and WANT_WRITE are expected, others are not.
                    raise e
                errno = e.errno

            buf = self.outgoing.read()
            self.socket.sendall(buf)

            if errno is None:
                should_loop = False
            elif errno == ssl.SSL_ERROR_WANT_READ:
                buf = self.socket.recv(SSL_BLOCKSIZE)
                if buf:
                    self.incoming.write(buf)
                else:
                    self.incoming.write_eof()
        return ret

import datetime
import struct
from collections import namedtuple


class ExtType(namedtuple("ExtType", "code data")):
    """ExtType represents ext type in msgpack."""

    def __new__(cls, code, data):
        if not isinstance(code, int):
            raise TypeError("code must be int")
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        if not 0 <= code <= 127:
            raise ValueError("code must be 0~127")
        return super().__new__(cls, code, data)


class Timestamp:
    """Timestamp represents the Timestamp extension type in msgpack.

    When built with Cython, msgpack uses C methods to pack and unpack `Timestamp`.
    When using pure-Python msgpack, :func:`to_bytes` and :func:`from_bytes` are used to pack and
    unpack `Timestamp`.

    This class is immutable: Do not override seconds and nanoseconds.
    """

    __slots__ = ["seconds", "nanoseconds"]

    def __init__(self, seconds, nanoseconds=0):
        """Initialize a Timestamp object.

        :param int seconds:
            Number of seconds since the UNIX epoch (00:00:00 UTC Jan 1 1970, minus leap seconds).
            May be negative.

        :param int nanoseconds:
            Number of nanoseconds to add to `seconds` to get fractional time.
            Maximum is 999_999_999.  Default is 0.

        Note: Negative times (before the UNIX epoch) are represented as neg. seconds + pos. ns.
        """
        if not isinstance(seconds, int):
            raise TypeError("seconds must be an integer")
        if not isinstance(nanoseconds, int):
            raise TypeError("nanoseconds must be an integer")
        if not (0 <= nanoseconds < 10**9):
            raise ValueError("nanoseconds must be a non-negative integer less than 999999999.")
        self.seconds = seconds
        self.nanoseconds = nanoseconds

    def __repr__(self):
        """String representation of Timestamp."""
        return f"Timestamp(seconds={self.seconds}, nanoseconds={self.nanoseconds})"

    def __eq__(self, other):
        """Check for equality with another Timestamp object"""
        if type(other) is self.__class__:
            return self.seconds == other.seconds and self.nanoseconds == other.nanoseconds
        return False

    def __ne__(self, other):
        """not-equals method (see :func:`__eq__()`)"""
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.seconds, self.nanoseconds))

    @staticmethod
    def from_bytes(b):
        """Unpack bytes into a `Timestamp` object.

        Used for pure-Python msgpack unpacking.

        :param b: Payload from msgpack ext message with code -1
        :type b: bytes

        :returns: Timestamp object unpacked from msgpack ext payload
        :rtype: Timestamp
        """
        if len(b) == 4:
            seconds = struct.unpack("!L", b)[0]
            nanoseconds = 0
        elif len(b) == 8:
            data64 = struct.unpack("!Q", b)[0]
            seconds = data64 & 0x00000003FFFFFFFF
            nanoseconds = data64 >> 34
        elif len(b) == 12:
            nanoseconds, seconds = struct.unpack("!Iq", b)
        else:
            raise ValueError(
                "Timestamp type can only be created from 32, 64, or 96-bit byte objects"
            )
        return Timestamp(seconds, nanoseconds)

    def to_bytes(self):
        """Pack this Timestamp object into bytes.

        Used for pure-Python msgpack packing.

        :returns data: Payload for EXT message with code -1 (timestamp type)
        :rtype: bytes
        """
        if (self.seconds >> 34) == 0:  # seconds is non-negative and fits in 34 bits
            data64 = self.nanoseconds << 34 | self.seconds
            if data64 & 0xFFFFFFFF00000000 == 0:
                # nanoseconds is zero and seconds < 2**32, so timestamp 32
                data = struct.pack("!L", data64)
            else:
                # timestamp 64
                data = struct.pack("!Q", data64)
        else:
            # timestamp 96
            data = struct.pack("!Iq", self.nanoseconds, self.seconds)
        return data

    @staticmethod
    def from_unix(unix_sec):
        """Create a Timestamp from posix timestamp in seconds.

        :param unix_float: Posix timestamp in seconds.
        :type unix_float: int or float
        """
        seconds = int(unix_sec // 1)
        nanoseconds = int((unix_sec % 1) * 10**9)
        return Timestamp(seconds, nanoseconds)

    def to_unix(self):
        """Get the timestamp as a floating-point value.

        :returns: posix timestamp
        :rtype: float
        """
        return self.seconds + self.nanoseconds / 1e9

    @staticmethod
    def from_unix_nano(unix_ns):
        """Create a Timestamp from posix timestamp in nanoseconds.

        :param int unix_ns: Posix timestamp in nanoseconds.
        :rtype: Timestamp
        """
        return Timestamp(*divmod(unix_ns, 10**9))

    def to_unix_nano(self):
        """Get the timestamp as a unixtime in nanoseconds.

        :returns: posix timestamp in nanoseconds
        :rtype: int
        """
        return self.seconds * 10**9 + self.nanoseconds

    def to_datetime(self):
        """Get the timestamp as a UTC datetime.

        :rtype: `datetime.datetime`
        """
        utc = datetime.timezone.utc
        return datetime.datetime.fromtimestamp(0, utc) + datetime.timedelta(
            seconds=self.seconds, microseconds=self.nanoseconds // 1000
        )

    @staticmethod
    def from_datetime(dt):
        """Create a Timestamp from datetime with tzinfo.

        :rtype: Timestamp
        """
        return Timestamp(seconds=int(dt.timestamp()), nanoseconds=dt.microsecond * 1000)

from typing import Any, Union

from .core import decode, encode


def ToASCII(label: str) -> bytes:
    return encode(label)


def ToUnicode(label: Union[bytes, bytearray]) -> str:
    return decode(label)


def nameprep(s: Any) -> None:
    raise NotImplementedError("IDNA 2008 does not utilise nameprep protocol")

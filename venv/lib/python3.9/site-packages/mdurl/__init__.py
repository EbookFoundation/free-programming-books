__all__ = (
    "decode",
    "DECODE_DEFAULT_CHARS",
    "DECODE_COMPONENT_CHARS",
    "encode",
    "ENCODE_DEFAULT_CHARS",
    "ENCODE_COMPONENT_CHARS",
    "format",
    "parse",
    "URL",
)
__version__ = "0.1.2"  # DO NOT EDIT THIS LINE MANUALLY. LET bump2version UTILITY DO IT

from mdurl._decode import DECODE_COMPONENT_CHARS, DECODE_DEFAULT_CHARS, decode
from mdurl._encode import ENCODE_COMPONENT_CHARS, ENCODE_DEFAULT_CHARS, encode
from mdurl._format import format
from mdurl._parse import url_parse as parse
from mdurl._url import URL

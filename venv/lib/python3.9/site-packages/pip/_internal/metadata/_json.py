# Extracted from https://github.com/pfmoore/pkg_metadata
from __future__ import annotations

from email.header import Header, decode_header, make_header
from email.message import Message
from typing import Any, cast

METADATA_FIELDS = [
    # Name, Multiple-Use
    ("Metadata-Version", False),
    ("Name", False),
    ("Version", False),
    ("Dynamic", True),
    ("Platform", True),
    ("Supported-Platform", True),
    ("Summary", False),
    ("Description", False),
    ("Description-Content-Type", False),
    ("Keywords", False),
    ("Home-page", False),
    ("Download-URL", False),
    ("Author", False),
    ("Author-email", False),
    ("Maintainer", False),
    ("Maintainer-email", False),
    ("License", False),
    ("License-Expression", False),
    ("License-File", True),
    ("Classifier", True),
    ("Requires-Dist", True),
    ("Requires-Python", False),
    ("Requires-External", True),
    ("Project-URL", True),
    ("Provides-Extra", True),
    ("Provides-Dist", True),
    ("Obsoletes-Dist", True),
]


def json_name(field: str) -> str:
    return field.lower().replace("-", "_")


def msg_to_json(msg: Message) -> dict[str, Any]:
    """Convert a Message object into a JSON-compatible dictionary."""

    def sanitise_header(h: Header | str) -> str:
        if isinstance(h, Header):
            chunks = []
            for bytes, encoding in decode_header(h):
                if encoding == "unknown-8bit":
                    try:
                        # See if UTF-8 works
                        bytes.decode("utf-8")
                        encoding = "utf-8"
                    except UnicodeDecodeError:
                        # If not, latin1 at least won't fail
                        encoding = "latin1"
                chunks.append((bytes, encoding))
            return str(make_header(chunks))
        return str(h)

    result = {}
    for field, multi in METADATA_FIELDS:
        if field not in msg:
            continue
        key = json_name(field)
        if multi:
            value: str | list[str] = [
                sanitise_header(v) for v in msg.get_all(field)  # type: ignore
            ]
        else:
            value = sanitise_header(msg.get(field))  # type: ignore
            if key == "keywords":
                # Accept both comma-separated and space-separated
                # forms, for better compatibility with old data.
                if "," in value:
                    value = [v.strip() for v in value.split(",")]
                else:
                    value = value.split()
        result[key] = value

    payload = cast(str, msg.get_payload())
    if payload:
        result["description"] = payload

    return result

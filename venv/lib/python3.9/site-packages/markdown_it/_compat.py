from __future__ import annotations

from collections.abc import Mapping
import sys
from typing import Any

DATACLASS_KWARGS: Mapping[str, Any]
if sys.version_info >= (3, 10):
    DATACLASS_KWARGS = {"slots": True}
else:
    DATACLASS_KWARGS = {}

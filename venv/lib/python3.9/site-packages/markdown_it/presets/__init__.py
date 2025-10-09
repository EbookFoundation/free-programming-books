__all__ = ("commonmark", "default", "zero", "js_default", "gfm_like")

from . import commonmark, default, zero
from ..utils import PresetType

js_default = default


class gfm_like:  # noqa: N801
    """GitHub Flavoured Markdown (GFM) like.

    This adds the linkify, table and strikethrough components to CommmonMark.

    Note, it lacks task-list items and raw HTML filtering,
    to meet the the full GFM specification
    (see https://github.github.com/gfm/#autolinks-extension-).
    """

    @staticmethod
    def make() -> PresetType:
        config = commonmark.make()
        config["components"]["core"]["rules"].append("linkify")
        config["components"]["block"]["rules"].append("table")
        config["components"]["inline"]["rules"].extend(["strikethrough", "linkify"])
        config["components"]["inline"]["rules2"].append("strikethrough")
        config["options"]["linkify"] = True
        config["options"]["html"] = True
        return config

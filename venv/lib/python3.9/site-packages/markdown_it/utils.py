from __future__ import annotations

from collections.abc import MutableMapping as MutableMappingABC
from pathlib import Path
from typing import Any, Callable, Iterable, MutableMapping, TypedDict, cast

EnvType = MutableMapping[str, Any]  # note: could use TypeAlias in python 3.10
"""Type for the environment sandbox used in parsing and rendering,
which stores mutable variables for use by plugins and rules.
"""


class OptionsType(TypedDict):
    """Options for parsing."""

    maxNesting: int
    """Internal protection, recursion limit."""
    html: bool
    """Enable HTML tags in source."""
    linkify: bool
    """Enable autoconversion of URL-like texts to links."""
    typographer: bool
    """Enable smartquotes and replacements."""
    quotes: str
    """Quote characters."""
    xhtmlOut: bool
    """Use '/' to close single tags (<br />)."""
    breaks: bool
    """Convert newlines in paragraphs into <br>."""
    langPrefix: str
    """CSS language prefix for fenced blocks."""
    highlight: Callable[[str, str, str], str] | None
    """Highlighter function: (content, lang, attrs) -> str."""


class PresetType(TypedDict):
    """Preset configuration for markdown-it."""

    options: OptionsType
    """Options for parsing."""
    components: MutableMapping[str, MutableMapping[str, list[str]]]
    """Components for parsing and rendering."""


class OptionsDict(MutableMappingABC):  # type: ignore
    """A dictionary, with attribute access to core markdownit configuration options."""

    # Note: ideally we would probably just remove attribute access entirely,
    # but we keep it for backwards compatibility.

    def __init__(self, options: OptionsType) -> None:
        self._options = cast(OptionsType, dict(options))

    def __getitem__(self, key: str) -> Any:
        return self._options[key]  # type: ignore[literal-required]

    def __setitem__(self, key: str, value: Any) -> None:
        self._options[key] = value  # type: ignore[literal-required]

    def __delitem__(self, key: str) -> None:
        del self._options[key]  # type: ignore

    def __iter__(self) -> Iterable[str]:  # type: ignore
        return iter(self._options)

    def __len__(self) -> int:
        return len(self._options)

    def __repr__(self) -> str:
        return repr(self._options)

    def __str__(self) -> str:
        return str(self._options)

    @property
    def maxNesting(self) -> int:
        """Internal protection, recursion limit."""
        return self._options["maxNesting"]

    @maxNesting.setter
    def maxNesting(self, value: int) -> None:
        self._options["maxNesting"] = value

    @property
    def html(self) -> bool:
        """Enable HTML tags in source."""
        return self._options["html"]

    @html.setter
    def html(self, value: bool) -> None:
        self._options["html"] = value

    @property
    def linkify(self) -> bool:
        """Enable autoconversion of URL-like texts to links."""
        return self._options["linkify"]

    @linkify.setter
    def linkify(self, value: bool) -> None:
        self._options["linkify"] = value

    @property
    def typographer(self) -> bool:
        """Enable smartquotes and replacements."""
        return self._options["typographer"]

    @typographer.setter
    def typographer(self, value: bool) -> None:
        self._options["typographer"] = value

    @property
    def quotes(self) -> str:
        """Quote characters."""
        return self._options["quotes"]

    @quotes.setter
    def quotes(self, value: str) -> None:
        self._options["quotes"] = value

    @property
    def xhtmlOut(self) -> bool:
        """Use '/' to close single tags (<br />)."""
        return self._options["xhtmlOut"]

    @xhtmlOut.setter
    def xhtmlOut(self, value: bool) -> None:
        self._options["xhtmlOut"] = value

    @property
    def breaks(self) -> bool:
        """Convert newlines in paragraphs into <br>."""
        return self._options["breaks"]

    @breaks.setter
    def breaks(self, value: bool) -> None:
        self._options["breaks"] = value

    @property
    def langPrefix(self) -> str:
        """CSS language prefix for fenced blocks."""
        return self._options["langPrefix"]

    @langPrefix.setter
    def langPrefix(self, value: str) -> None:
        self._options["langPrefix"] = value

    @property
    def highlight(self) -> Callable[[str, str, str], str] | None:
        """Highlighter function: (content, langName, langAttrs) -> escaped HTML."""
        return self._options["highlight"]

    @highlight.setter
    def highlight(self, value: Callable[[str, str, str], str] | None) -> None:
        self._options["highlight"] = value


def read_fixture_file(path: str | Path) -> list[list[Any]]:
    text = Path(path).read_text(encoding="utf-8")
    tests = []
    section = 0
    last_pos = 0
    lines = text.splitlines(keepends=True)
    for i in range(len(lines)):
        if lines[i].rstrip() == ".":
            if section == 0:
                tests.append([i, lines[i - 1].strip()])
                section = 1
            elif section == 1:
                tests[-1].append("".join(lines[last_pos + 1 : i]))
                section = 2
            elif section == 2:
                tests[-1].append("".join(lines[last_pos + 1 : i]))
                section = 0

            last_pos = i
    return tests

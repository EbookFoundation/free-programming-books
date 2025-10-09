from __future__ import annotations

from collections.abc import Callable, MutableMapping
import dataclasses as dc
from typing import Any, Literal
import warnings

from markdown_it._compat import DATACLASS_KWARGS


def convert_attrs(value: Any) -> Any:
    """Convert Token.attrs set as ``None`` or ``[[key, value], ...]`` to a dict.

    This improves compatibility with upstream markdown-it.
    """
    if not value:
        return {}
    if isinstance(value, list):
        return dict(value)
    return value


@dc.dataclass(**DATACLASS_KWARGS)
class Token:
    type: str
    """Type of the token (string, e.g. "paragraph_open")"""

    tag: str
    """HTML tag name, e.g. 'p'"""

    nesting: Literal[-1, 0, 1]
    """Level change (number in {-1, 0, 1} set), where:
    -  `1` means the tag is opening
    -  `0` means the tag is self-closing
    - `-1` means the tag is closing
    """

    attrs: dict[str, str | int | float] = dc.field(default_factory=dict)
    """HTML attributes.
    Note this differs from the upstream "list of lists" format,
    although than an instance can still be initialised with this format.
    """

    map: list[int] | None = None
    """Source map info. Format: `[ line_begin, line_end ]`"""

    level: int = 0
    """Nesting level, the same as `state.level`"""

    children: list[Token] | None = None
    """Array of child nodes (inline and img tokens)."""

    content: str = ""
    """Inner content, in the case of a self-closing tag (code, html, fence, etc.),"""

    markup: str = ""
    """'*' or '_' for emphasis, fence string for fence, etc."""

    info: str = ""
    """Additional information:
    - Info string for "fence" tokens
    - The value "auto" for autolink "link_open" and "link_close" tokens
    - The string value of the item marker for ordered-list "list_item_open" tokens
    """

    meta: dict[Any, Any] = dc.field(default_factory=dict)
    """A place for plugins to store any arbitrary data"""

    block: bool = False
    """True for block-level tokens, false for inline tokens.
    Used in renderer to calculate line breaks
    """

    hidden: bool = False
    """If true, ignore this element when rendering.
    Used for tight lists to hide paragraphs.
    """

    def __post_init__(self) -> None:
        self.attrs = convert_attrs(self.attrs)

    def attrIndex(self, name: str) -> int:
        warnings.warn(  # noqa: B028
            "Token.attrIndex should not be used, since Token.attrs is a dictionary",
            UserWarning,
        )
        if name not in self.attrs:
            return -1
        return list(self.attrs.keys()).index(name)

    def attrItems(self) -> list[tuple[str, str | int | float]]:
        """Get (key, value) list of attrs."""
        return list(self.attrs.items())

    def attrPush(self, attrData: tuple[str, str | int | float]) -> None:
        """Add `[ name, value ]` attribute to list. Init attrs if necessary."""
        name, value = attrData
        self.attrSet(name, value)

    def attrSet(self, name: str, value: str | int | float) -> None:
        """Set `name` attribute to `value`. Override old value if exists."""
        self.attrs[name] = value

    def attrGet(self, name: str) -> None | str | int | float:
        """Get the value of attribute `name`, or null if it does not exist."""
        return self.attrs.get(name, None)

    def attrJoin(self, name: str, value: str) -> None:
        """Join value to existing attribute via space.
        Or create new attribute if not exists.
        Useful to operate with token classes.
        """
        if name in self.attrs:
            current = self.attrs[name]
            if not isinstance(current, str):
                raise TypeError(
                    f"existing attr 'name' is not a str: {self.attrs[name]}"
                )
            self.attrs[name] = f"{current} {value}"
        else:
            self.attrs[name] = value

    def copy(self, **changes: Any) -> Token:
        """Return a shallow copy of the instance."""
        return dc.replace(self, **changes)

    def as_dict(
        self,
        *,
        children: bool = True,
        as_upstream: bool = True,
        meta_serializer: Callable[[dict[Any, Any]], Any] | None = None,
        filter: Callable[[str, Any], bool] | None = None,
        dict_factory: Callable[..., MutableMapping[str, Any]] = dict,
    ) -> MutableMapping[str, Any]:
        """Return the token as a dictionary.

        :param children: Also convert children to dicts
        :param as_upstream: Ensure the output dictionary is equal to that created by markdown-it
            For example, attrs are converted to null or lists
        :param meta_serializer: hook for serializing ``Token.meta``
        :param filter: A callable whose return code determines whether an
            attribute or element is included (``True``) or dropped (``False``).
            Is called with the (key, value) pair.
        :param dict_factory: A callable to produce dictionaries from.
            For example, to produce ordered dictionaries instead of normal Python
            dictionaries, pass in ``collections.OrderedDict``.

        """
        mapping = dict_factory((f.name, getattr(self, f.name)) for f in dc.fields(self))
        if filter:
            mapping = dict_factory((k, v) for k, v in mapping.items() if filter(k, v))
        if as_upstream and "attrs" in mapping:
            mapping["attrs"] = (
                None
                if not mapping["attrs"]
                else [[k, v] for k, v in mapping["attrs"].items()]
            )
        if meta_serializer and "meta" in mapping:
            mapping["meta"] = meta_serializer(mapping["meta"])
        if children and mapping.get("children", None):
            mapping["children"] = [
                child.as_dict(
                    children=children,
                    filter=filter,
                    dict_factory=dict_factory,
                    as_upstream=as_upstream,
                    meta_serializer=meta_serializer,
                )
                for child in mapping["children"]
            ]
        return mapping

    @classmethod
    def from_dict(cls, dct: MutableMapping[str, Any]) -> Token:
        """Convert a dict to a Token."""
        token = cls(**dct)
        if token.children:
            token.children = [cls.from_dict(c) for c in token.children]  # type: ignore[arg-type]
        return token

import inspect
from inspect import cleandoc, getdoc, getfile, isclass, ismodule, signature
from typing import Any, Collection, Iterable, Optional, Tuple, Type, Union

from .console import Group, RenderableType
from .control import escape_control_codes
from .highlighter import ReprHighlighter
from .jupyter import JupyterMixin
from .panel import Panel
from .pretty import Pretty
from .table import Table
from .text import Text, TextType


def _first_paragraph(doc: str) -> str:
    """Get the first paragraph from a docstring."""
    paragraph, _, _ = doc.partition("\n\n")
    return paragraph


class Inspect(JupyterMixin):
    """A renderable to inspect any Python Object.

    Args:
        obj (Any): An object to inspect.
        title (str, optional): Title to display over inspect result, or None use type. Defaults to None.
        help (bool, optional): Show full help text rather than just first paragraph. Defaults to False.
        methods (bool, optional): Enable inspection of callables. Defaults to False.
        docs (bool, optional): Also render doc strings. Defaults to True.
        private (bool, optional): Show private attributes (beginning with underscore). Defaults to False.
        dunder (bool, optional): Show attributes starting with double underscore. Defaults to False.
        sort (bool, optional): Sort attributes alphabetically. Defaults to True.
        all (bool, optional): Show all attributes. Defaults to False.
        value (bool, optional): Pretty print value of object. Defaults to True.
    """

    def __init__(
        self,
        obj: Any,
        *,
        title: Optional[TextType] = None,
        help: bool = False,
        methods: bool = False,
        docs: bool = True,
        private: bool = False,
        dunder: bool = False,
        sort: bool = True,
        all: bool = True,
        value: bool = True,
    ) -> None:
        self.highlighter = ReprHighlighter()
        self.obj = obj
        self.title = title or self._make_title(obj)
        if all:
            methods = private = dunder = True
        self.help = help
        self.methods = methods
        self.docs = docs or help
        self.private = private or dunder
        self.dunder = dunder
        self.sort = sort
        self.value = value

    def _make_title(self, obj: Any) -> Text:
        """Make a default title."""
        title_str = (
            str(obj)
            if (isclass(obj) or callable(obj) or ismodule(obj))
            else str(type(obj))
        )
        title_text = self.highlighter(title_str)
        return title_text

    def __rich__(self) -> Panel:
        return Panel.fit(
            Group(*self._render()),
            title=self.title,
            border_style="scope.border",
            padding=(0, 1),
        )

    def _get_signature(self, name: str, obj: Any) -> Optional[Text]:
        """Get a signature for a callable."""
        try:
            _signature = str(signature(obj)) + ":"
        except ValueError:
            _signature = "(...)"
        except TypeError:
            return None

        source_filename: Optional[str] = None
        try:
            source_filename = getfile(obj)
        except (OSError, TypeError):
            # OSError is raised if obj has no source file, e.g. when defined in REPL.
            pass

        callable_name = Text(name, style="inspect.callable")
        if source_filename:
            callable_name.stylize(f"link file://{source_filename}")
        signature_text = self.highlighter(_signature)

        qualname = name or getattr(obj, "__qualname__", name)

        # If obj is a module, there may be classes (which are callable) to display
        if inspect.isclass(obj):
            prefix = "class"
        elif inspect.iscoroutinefunction(obj):
            prefix = "async def"
        else:
            prefix = "def"

        qual_signature = Text.assemble(
            (f"{prefix} ", f"inspect.{prefix.replace(' ', '_')}"),
            (qualname, "inspect.callable"),
            signature_text,
        )

        return qual_signature

    def _render(self) -> Iterable[RenderableType]:
        """Render object."""

        def sort_items(item: Tuple[str, Any]) -> Tuple[bool, str]:
            key, (_error, value) = item
            return (callable(value), key.strip("_").lower())

        def safe_getattr(attr_name: str) -> Tuple[Any, Any]:
            """Get attribute or any exception."""
            try:
                return (None, getattr(obj, attr_name))
            except Exception as error:
                return (error, None)

        obj = self.obj
        keys = dir(obj)
        total_items = len(keys)
        if not self.dunder:
            keys = [key for key in keys if not key.startswith("__")]
        if not self.private:
            keys = [key for key in keys if not key.startswith("_")]
        not_shown_count = total_items - len(keys)
        items = [(key, safe_getattr(key)) for key in keys]
        if self.sort:
            items.sort(key=sort_items)

        items_table = Table.grid(padding=(0, 1), expand=False)
        items_table.add_column(justify="right")
        add_row = items_table.add_row
        highlighter = self.highlighter

        if callable(obj):
            signature = self._get_signature("", obj)
            if signature is not None:
                yield signature
                yield ""

        if self.docs:
            _doc = self._get_formatted_doc(obj)
            if _doc is not None:
                doc_text = Text(_doc, style="inspect.help")
                doc_text = highlighter(doc_text)
                yield doc_text
                yield ""

        if self.value and not (isclass(obj) or callable(obj) or ismodule(obj)):
            yield Panel(
                Pretty(obj, indent_guides=True, max_length=10, max_string=60),
                border_style="inspect.value.border",
            )
            yield ""

        for key, (error, value) in items:
            key_text = Text.assemble(
                (
                    key,
                    "inspect.attr.dunder" if key.startswith("__") else "inspect.attr",
                ),
                (" =", "inspect.equals"),
            )
            if error is not None:
                warning = key_text.copy()
                warning.stylize("inspect.error")
                add_row(warning, highlighter(repr(error)))
                continue

            if callable(value):
                if not self.methods:
                    continue

                _signature_text = self._get_signature(key, value)
                if _signature_text is None:
                    add_row(key_text, Pretty(value, highlighter=highlighter))
                else:
                    if self.docs:
                        docs = self._get_formatted_doc(value)
                        if docs is not None:
                            _signature_text.append("\n" if "\n" in docs else " ")
                            doc = highlighter(docs)
                            doc.stylize("inspect.doc")
                            _signature_text.append(doc)

                    add_row(key_text, _signature_text)
            else:
                add_row(key_text, Pretty(value, highlighter=highlighter))
        if items_table.row_count:
            yield items_table
        elif not_shown_count:
            yield Text.from_markup(
                f"[b cyan]{not_shown_count}[/][i] attribute(s) not shown.[/i] "
                f"Run [b][magenta]inspect[/]([not b]inspect[/])[/b] for options."
            )

    def _get_formatted_doc(self, object_: Any) -> Optional[str]:
        """
        Extract the docstring of an object, process it and returns it.
        The processing consists in cleaning up the docstring's indentation,
        taking only its 1st paragraph if `self.help` is not True,
        and escape its control codes.

        Args:
            object_ (Any): the object to get the docstring from.

        Returns:
            Optional[str]: the processed docstring, or None if no docstring was found.
        """
        docs = getdoc(object_)
        if docs is None:
            return None
        docs = cleandoc(docs).strip()
        if not self.help:
            docs = _first_paragraph(docs)
        return escape_control_codes(docs)


def get_object_types_mro(obj: Union[object, Type[Any]]) -> Tuple[type, ...]:
    """Returns the MRO of an object's class, or of the object itself if it's a class."""
    if not hasattr(obj, "__mro__"):
        # N.B. we cannot use `if type(obj) is type` here because it doesn't work with
        # some types of classes, such as the ones that use abc.ABCMeta.
        obj = type(obj)
    return getattr(obj, "__mro__", ())


def get_object_types_mro_as_strings(obj: object) -> Collection[str]:
    """
    Returns the MRO of an object's class as full qualified names, or of the object itself if it's a class.

    Examples:
        `object_types_mro_as_strings(JSONDecoder)` will return `['json.decoder.JSONDecoder', 'builtins.object']`
    """
    return [
        f'{getattr(type_, "__module__", "")}.{getattr(type_, "__qualname__", "")}'
        for type_ in get_object_types_mro(obj)
    ]


def is_object_one_of_types(
    obj: object, fully_qualified_types_names: Collection[str]
) -> bool:
    """
    Returns `True` if the given object's class (or the object itself, if it's a class) has one of the
    fully qualified names in its MRO.
    """
    for type_name in get_object_types_mro_as_strings(obj):
        if type_name in fully_qualified_types_names:
            return True
    return False

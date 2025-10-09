from __future__ import annotations

from pip._internal.models.format_control import FormatControl


# TODO: This needs Python 3.10's improved slots support for dataclasses
# to be converted into a dataclass.
class SelectionPreferences:
    """
    Encapsulates the candidate selection preferences for downloading
    and installing files.
    """

    __slots__ = [
        "allow_yanked",
        "allow_all_prereleases",
        "format_control",
        "prefer_binary",
        "ignore_requires_python",
    ]

    # Don't include an allow_yanked default value to make sure each call
    # site considers whether yanked releases are allowed. This also causes
    # that decision to be made explicit in the calling code, which helps
    # people when reading the code.
    def __init__(
        self,
        allow_yanked: bool,
        allow_all_prereleases: bool = False,
        format_control: FormatControl | None = None,
        prefer_binary: bool = False,
        ignore_requires_python: bool | None = None,
    ) -> None:
        """Create a SelectionPreferences object.

        :param allow_yanked: Whether files marked as yanked (in the sense
            of PEP 592) are permitted to be candidates for install.
        :param format_control: A FormatControl object or None. Used to control
            the selection of source packages / binary packages when consulting
            the index and links.
        :param prefer_binary: Whether to prefer an old, but valid, binary
            dist over a new source dist.
        :param ignore_requires_python: Whether to ignore incompatible
            "Requires-Python" values in links. Defaults to False.
        """
        if ignore_requires_python is None:
            ignore_requires_python = False

        self.allow_yanked = allow_yanked
        self.allow_all_prereleases = allow_all_prereleases
        self.format_control = format_control
        self.prefer_binary = prefer_binary
        self.ignore_requires_python = ignore_requires_python

import configparser
from typing import IO, Dict, List, Mapping, Optional

from .default_styles import DEFAULT_STYLES
from .style import Style, StyleType


class Theme:
    """A container for style information, used by :class:`~rich.console.Console`.

    Args:
        styles (Dict[str, Style], optional): A mapping of style names on to styles. Defaults to None for a theme with no styles.
        inherit (bool, optional): Inherit default styles. Defaults to True.
    """

    styles: Dict[str, Style]

    def __init__(
        self, styles: Optional[Mapping[str, StyleType]] = None, inherit: bool = True
    ):
        self.styles = DEFAULT_STYLES.copy() if inherit else {}
        if styles is not None:
            self.styles.update(
                {
                    name: style if isinstance(style, Style) else Style.parse(style)
                    for name, style in styles.items()
                }
            )

    @property
    def config(self) -> str:
        """Get contents of a config file for this theme."""
        config = "[styles]\n" + "\n".join(
            f"{name} = {style}" for name, style in sorted(self.styles.items())
        )
        return config

    @classmethod
    def from_file(
        cls, config_file: IO[str], source: Optional[str] = None, inherit: bool = True
    ) -> "Theme":
        """Load a theme from a text mode file.

        Args:
            config_file (IO[str]): An open conf file.
            source (str, optional): The filename of the open file. Defaults to None.
            inherit (bool, optional): Inherit default styles. Defaults to True.

        Returns:
            Theme: A New theme instance.
        """
        config = configparser.ConfigParser()
        config.read_file(config_file, source=source)
        styles = {name: Style.parse(value) for name, value in config.items("styles")}
        theme = Theme(styles, inherit=inherit)
        return theme

    @classmethod
    def read(
        cls, path: str, inherit: bool = True, encoding: Optional[str] = None
    ) -> "Theme":
        """Read a theme from a path.

        Args:
            path (str): Path to a config file readable by Python configparser module.
            inherit (bool, optional): Inherit default styles. Defaults to True.
            encoding (str, optional): Encoding of the config file. Defaults to None.

        Returns:
            Theme: A new theme instance.
        """
        with open(path, encoding=encoding) as config_file:
            return cls.from_file(config_file, source=path, inherit=inherit)


class ThemeStackError(Exception):
    """Base exception for errors related to the theme stack."""


class ThemeStack:
    """A stack of themes.

    Args:
        theme (Theme): A theme instance
    """

    def __init__(self, theme: Theme) -> None:
        self._entries: List[Dict[str, Style]] = [theme.styles]
        self.get = self._entries[-1].get

    def push_theme(self, theme: Theme, inherit: bool = True) -> None:
        """Push a theme on the top of the stack.

        Args:
            theme (Theme): A Theme instance.
            inherit (boolean, optional): Inherit styles from current top of stack.
        """
        styles: Dict[str, Style]
        styles = (
            {**self._entries[-1], **theme.styles} if inherit else theme.styles.copy()
        )
        self._entries.append(styles)
        self.get = self._entries[-1].get

    def pop_theme(self) -> None:
        """Pop (and discard) the top-most theme."""
        if len(self._entries) == 1:
            raise ThemeStackError("Unable to pop base theme")
        self._entries.pop()
        self.get = self._entries[-1].get


if __name__ == "__main__":  # pragma: no cover
    theme = Theme()
    print(theme.config)

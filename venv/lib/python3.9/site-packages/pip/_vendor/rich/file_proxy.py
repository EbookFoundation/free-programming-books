import io
from typing import IO, TYPE_CHECKING, Any, List

from .ansi import AnsiDecoder
from .text import Text

if TYPE_CHECKING:
    from .console import Console


class FileProxy(io.TextIOBase):
    """Wraps a file (e.g. sys.stdout) and redirects writes to a console."""

    def __init__(self, console: "Console", file: IO[str]) -> None:
        self.__console = console
        self.__file = file
        self.__buffer: List[str] = []
        self.__ansi_decoder = AnsiDecoder()

    @property
    def rich_proxied_file(self) -> IO[str]:
        """Get proxied file."""
        return self.__file

    def __getattr__(self, name: str) -> Any:
        return getattr(self.__file, name)

    def write(self, text: str) -> int:
        if not isinstance(text, str):
            raise TypeError(f"write() argument must be str, not {type(text).__name__}")
        buffer = self.__buffer
        lines: List[str] = []
        while text:
            line, new_line, text = text.partition("\n")
            if new_line:
                lines.append("".join(buffer) + line)
                buffer.clear()
            else:
                buffer.append(line)
                break
        if lines:
            console = self.__console
            with console:
                output = Text("\n").join(
                    self.__ansi_decoder.decode_line(line) for line in lines
                )
                console.print(output)
        return len(text)

    def flush(self) -> None:
        output = "".join(self.__buffer)
        if output:
            self.__console.print(output)
        del self.__buffer[:]

    def fileno(self) -> int:
        return self.__file.fileno()

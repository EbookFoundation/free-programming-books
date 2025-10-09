"""
This module contains implementations for the termui module. To keep the
import time of Click down, some infrequently used functionality is
placed in this module and only imported as needed.
"""

import contextlib
import math
import os
import sys
import time
import typing as t
from gettext import gettext as _
from io import StringIO
from shutil import which
from types import TracebackType

from ._compat import _default_text_stdout
from ._compat import CYGWIN
from ._compat import get_best_encoding
from ._compat import isatty
from ._compat import open_stream
from ._compat import strip_ansi
from ._compat import term_len
from ._compat import WIN
from .exceptions import ClickException
from .utils import echo

V = t.TypeVar("V")

if os.name == "nt":
    BEFORE_BAR = "\r"
    AFTER_BAR = "\n"
else:
    BEFORE_BAR = "\r\033[?25l"
    AFTER_BAR = "\033[?25h\n"


class ProgressBar(t.Generic[V]):
    def __init__(
        self,
        iterable: t.Optional[t.Iterable[V]],
        length: t.Optional[int] = None,
        fill_char: str = "#",
        empty_char: str = " ",
        bar_template: str = "%(bar)s",
        info_sep: str = "  ",
        show_eta: bool = True,
        show_percent: t.Optional[bool] = None,
        show_pos: bool = False,
        item_show_func: t.Optional[t.Callable[[t.Optional[V]], t.Optional[str]]] = None,
        label: t.Optional[str] = None,
        file: t.Optional[t.TextIO] = None,
        color: t.Optional[bool] = None,
        update_min_steps: int = 1,
        width: int = 30,
    ) -> None:
        self.fill_char = fill_char
        self.empty_char = empty_char
        self.bar_template = bar_template
        self.info_sep = info_sep
        self.show_eta = show_eta
        self.show_percent = show_percent
        self.show_pos = show_pos
        self.item_show_func = item_show_func
        self.label: str = label or ""

        if file is None:
            file = _default_text_stdout()

            # There are no standard streams attached to write to. For example,
            # pythonw on Windows.
            if file is None:
                file = StringIO()

        self.file = file
        self.color = color
        self.update_min_steps = update_min_steps
        self._completed_intervals = 0
        self.width: int = width
        self.autowidth: bool = width == 0

        if length is None:
            from operator import length_hint

            length = length_hint(iterable, -1)

            if length == -1:
                length = None
        if iterable is None:
            if length is None:
                raise TypeError("iterable or length is required")
            iterable = t.cast(t.Iterable[V], range(length))
        self.iter: t.Iterable[V] = iter(iterable)
        self.length = length
        self.pos = 0
        self.avg: t.List[float] = []
        self.last_eta: float
        self.start: float
        self.start = self.last_eta = time.time()
        self.eta_known: bool = False
        self.finished: bool = False
        self.max_width: t.Optional[int] = None
        self.entered: bool = False
        self.current_item: t.Optional[V] = None
        self.is_hidden: bool = not isatty(self.file)
        self._last_line: t.Optional[str] = None

    def __enter__(self) -> "ProgressBar[V]":
        self.entered = True
        self.render_progress()
        return self

    def __exit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_value: t.Optional[BaseException],
        tb: t.Optional[TracebackType],
    ) -> None:
        self.render_finish()

    def __iter__(self) -> t.Iterator[V]:
        if not self.entered:
            raise RuntimeError("You need to use progress bars in a with block.")
        self.render_progress()
        return self.generator()

    def __next__(self) -> V:
        # Iteration is defined in terms of a generator function,
        # returned by iter(self); use that to define next(). This works
        # because `self.iter` is an iterable consumed by that generator,
        # so it is re-entry safe. Calling `next(self.generator())`
        # twice works and does "what you want".
        return next(iter(self))

    def render_finish(self) -> None:
        if self.is_hidden:
            return
        self.file.write(AFTER_BAR)
        self.file.flush()

    @property
    def pct(self) -> float:
        if self.finished:
            return 1.0
        return min(self.pos / (float(self.length or 1) or 1), 1.0)

    @property
    def time_per_iteration(self) -> float:
        if not self.avg:
            return 0.0
        return sum(self.avg) / float(len(self.avg))

    @property
    def eta(self) -> float:
        if self.length is not None and not self.finished:
            return self.time_per_iteration * (self.length - self.pos)
        return 0.0

    def format_eta(self) -> str:
        if self.eta_known:
            t = int(self.eta)
            seconds = t % 60
            t //= 60
            minutes = t % 60
            t //= 60
            hours = t % 24
            t //= 24
            if t > 0:
                return f"{t}d {hours:02}:{minutes:02}:{seconds:02}"
            else:
                return f"{hours:02}:{minutes:02}:{seconds:02}"
        return ""

    def format_pos(self) -> str:
        pos = str(self.pos)
        if self.length is not None:
            pos += f"/{self.length}"
        return pos

    def format_pct(self) -> str:
        return f"{int(self.pct * 100): 4}%"[1:]

    def format_bar(self) -> str:
        if self.length is not None:
            bar_length = int(self.pct * self.width)
            bar = self.fill_char * bar_length
            bar += self.empty_char * (self.width - bar_length)
        elif self.finished:
            bar = self.fill_char * self.width
        else:
            chars = list(self.empty_char * (self.width or 1))
            if self.time_per_iteration != 0:
                chars[
                    int(
                        (math.cos(self.pos * self.time_per_iteration) / 2.0 + 0.5)
                        * self.width
                    )
                ] = self.fill_char
            bar = "".join(chars)
        return bar

    def format_progress_line(self) -> str:
        show_percent = self.show_percent

        info_bits = []
        if self.length is not None and show_percent is None:
            show_percent = not self.show_pos

        if self.show_pos:
            info_bits.append(self.format_pos())
        if show_percent:
            info_bits.append(self.format_pct())
        if self.show_eta and self.eta_known and not self.finished:
            info_bits.append(self.format_eta())
        if self.item_show_func is not None:
            item_info = self.item_show_func(self.current_item)
            if item_info is not None:
                info_bits.append(item_info)

        return (
            self.bar_template
            % {
                "label": self.label,
                "bar": self.format_bar(),
                "info": self.info_sep.join(info_bits),
            }
        ).rstrip()

    def render_progress(self) -> None:
        import shutil

        if self.is_hidden:
            # Only output the label as it changes if the output is not a
            # TTY. Use file=stderr if you expect to be piping stdout.
            if self._last_line != self.label:
                self._last_line = self.label
                echo(self.label, file=self.file, color=self.color)

            return

        buf = []
        # Update width in case the terminal has been resized
        if self.autowidth:
            old_width = self.width
            self.width = 0
            clutter_length = term_len(self.format_progress_line())
            new_width = max(0, shutil.get_terminal_size().columns - clutter_length)
            if new_width < old_width:
                buf.append(BEFORE_BAR)
                buf.append(" " * self.max_width)  # type: ignore
                self.max_width = new_width
            self.width = new_width

        clear_width = self.width
        if self.max_width is not None:
            clear_width = self.max_width

        buf.append(BEFORE_BAR)
        line = self.format_progress_line()
        line_len = term_len(line)
        if self.max_width is None or self.max_width < line_len:
            self.max_width = line_len

        buf.append(line)
        buf.append(" " * (clear_width - line_len))
        line = "".join(buf)
        # Render the line only if it changed.

        if line != self._last_line:
            self._last_line = line
            echo(line, file=self.file, color=self.color, nl=False)
            self.file.flush()

    def make_step(self, n_steps: int) -> None:
        self.pos += n_steps
        if self.length is not None and self.pos >= self.length:
            self.finished = True

        if (time.time() - self.last_eta) < 1.0:
            return

        self.last_eta = time.time()

        # self.avg is a rolling list of length <= 7 of steps where steps are
        # defined as time elapsed divided by the total progress through
        # self.length.
        if self.pos:
            step = (time.time() - self.start) / self.pos
        else:
            step = time.time() - self.start

        self.avg = self.avg[-6:] + [step]

        self.eta_known = self.length is not None

    def update(self, n_steps: int, current_item: t.Optional[V] = None) -> None:
        """Update the progress bar by advancing a specified number of
        steps, and optionally set the ``current_item`` for this new
        position.

        :param n_steps: Number of steps to advance.
        :param current_item: Optional item to set as ``current_item``
            for the updated position.

        .. versionchanged:: 8.0
            Added the ``current_item`` optional parameter.

        .. versionchanged:: 8.0
            Only render when the number of steps meets the
            ``update_min_steps`` threshold.
        """
        if current_item is not None:
            self.current_item = current_item

        self._completed_intervals += n_steps

        if self._completed_intervals >= self.update_min_steps:
            self.make_step(self._completed_intervals)
            self.render_progress()
            self._completed_intervals = 0

    def finish(self) -> None:
        self.eta_known = False
        self.current_item = None
        self.finished = True

    def generator(self) -> t.Iterator[V]:
        """Return a generator which yields the items added to the bar
        during construction, and updates the progress bar *after* the
        yielded block returns.
        """
        # WARNING: the iterator interface for `ProgressBar` relies on
        # this and only works because this is a simple generator which
        # doesn't create or manage additional state. If this function
        # changes, the impact should be evaluated both against
        # `iter(bar)` and `next(bar)`. `next()` in particular may call
        # `self.generator()` repeatedly, and this must remain safe in
        # order for that interface to work.
        if not self.entered:
            raise RuntimeError("You need to use progress bars in a with block.")

        if self.is_hidden:
            yield from self.iter
        else:
            for rv in self.iter:
                self.current_item = rv

                # This allows show_item_func to be updated before the
                # item is processed. Only trigger at the beginning of
                # the update interval.
                if self._completed_intervals == 0:
                    self.render_progress()

                yield rv
                self.update(1)

            self.finish()
            self.render_progress()


def pager(generator: t.Iterable[str], color: t.Optional[bool] = None) -> None:
    """Decide what method to use for paging through text."""
    stdout = _default_text_stdout()

    # There are no standard streams attached to write to. For example,
    # pythonw on Windows.
    if stdout is None:
        stdout = StringIO()

    if not isatty(sys.stdin) or not isatty(stdout):
        return _nullpager(stdout, generator, color)
    pager_cmd = (os.environ.get("PAGER", None) or "").strip()
    if pager_cmd:
        if WIN:
            if _tempfilepager(generator, pager_cmd, color):
                return
        elif _pipepager(generator, pager_cmd, color):
            return
    if os.environ.get("TERM") in ("dumb", "emacs"):
        return _nullpager(stdout, generator, color)
    if (WIN or sys.platform.startswith("os2")) and _tempfilepager(
        generator, "more", color
    ):
        return
    if _pipepager(generator, "less", color):
        return

    import tempfile

    fd, filename = tempfile.mkstemp()
    os.close(fd)
    try:
        if _pipepager(generator, "more", color):
            return
        return _nullpager(stdout, generator, color)
    finally:
        os.unlink(filename)


def _pipepager(generator: t.Iterable[str], cmd: str, color: t.Optional[bool]) -> bool:
    """Page through text by feeding it to another program.  Invoking a
    pager through this might support colors.

    Returns True if the command was found, False otherwise and thus another
    pager should be attempted.
    """
    cmd_absolute = which(cmd)
    if cmd_absolute is None:
        return False

    import subprocess

    env = dict(os.environ)

    # If we're piping to less we might support colors under the
    # condition that
    cmd_detail = cmd.rsplit("/", 1)[-1].split()
    if color is None and cmd_detail[0] == "less":
        less_flags = f"{os.environ.get('LESS', '')}{' '.join(cmd_detail[1:])}"
        if not less_flags:
            env["LESS"] = "-R"
            color = True
        elif "r" in less_flags or "R" in less_flags:
            color = True

    c = subprocess.Popen(
        [cmd_absolute],
        shell=True,
        stdin=subprocess.PIPE,
        env=env,
        errors="replace",
        text=True,
    )
    assert c.stdin is not None
    try:
        for text in generator:
            if not color:
                text = strip_ansi(text)

            c.stdin.write(text)
    except (OSError, KeyboardInterrupt):
        pass
    else:
        c.stdin.close()

    # Less doesn't respect ^C, but catches it for its own UI purposes (aborting
    # search or other commands inside less).
    #
    # That means when the user hits ^C, the parent process (click) terminates,
    # but less is still alive, paging the output and messing up the terminal.
    #
    # If the user wants to make the pager exit on ^C, they should set
    # `LESS='-K'`. It's not our decision to make.
    while True:
        try:
            c.wait()
        except KeyboardInterrupt:
            pass
        else:
            break

    return True


def _tempfilepager(
    generator: t.Iterable[str],
    cmd: str,
    color: t.Optional[bool],
) -> bool:
    """Page through text by invoking a program on a temporary file.

    Returns True if the command was found, False otherwise and thus another
    pager should be attempted.
    """
    # Which is necessary for Windows, it is also recommended in the Popen docs.
    cmd_absolute = which(cmd)
    if cmd_absolute is None:
        return False

    import subprocess
    import tempfile

    fd, filename = tempfile.mkstemp()
    # TODO: This never terminates if the passed generator never terminates.
    text = "".join(generator)
    if not color:
        text = strip_ansi(text)
    encoding = get_best_encoding(sys.stdout)
    with open_stream(filename, "wb")[0] as f:
        f.write(text.encode(encoding))
    try:
        subprocess.call([cmd_absolute, filename])
    except OSError:
        # Command not found
        pass
    finally:
        os.close(fd)
        os.unlink(filename)

    return True


def _nullpager(
    stream: t.TextIO, generator: t.Iterable[str], color: t.Optional[bool]
) -> None:
    """Simply print unformatted text.  This is the ultimate fallback."""
    for text in generator:
        if not color:
            text = strip_ansi(text)
        stream.write(text)


class Editor:
    def __init__(
        self,
        editor: t.Optional[str] = None,
        env: t.Optional[t.Mapping[str, str]] = None,
        require_save: bool = True,
        extension: str = ".txt",
    ) -> None:
        self.editor = editor
        self.env = env
        self.require_save = require_save
        self.extension = extension

    def get_editor(self) -> str:
        if self.editor is not None:
            return self.editor
        for key in "VISUAL", "EDITOR":
            rv = os.environ.get(key)
            if rv:
                return rv
        if WIN:
            return "notepad"
        for editor in "sensible-editor", "vim", "nano":
            if which(editor) is not None:
                return editor
        return "vi"

    def edit_file(self, filename: str) -> None:
        import subprocess

        editor = self.get_editor()
        environ: t.Optional[t.Dict[str, str]] = None

        if self.env:
            environ = os.environ.copy()
            environ.update(self.env)

        try:
            c = subprocess.Popen(f'{editor} "{filename}"', env=environ, shell=True)
            exit_code = c.wait()
            if exit_code != 0:
                raise ClickException(
                    _("{editor}: Editing failed").format(editor=editor)
                )
        except OSError as e:
            raise ClickException(
                _("{editor}: Editing failed: {e}").format(editor=editor, e=e)
            ) from e

    def edit(self, text: t.Optional[t.AnyStr]) -> t.Optional[t.AnyStr]:
        import tempfile

        if not text:
            data = b""
        elif isinstance(text, (bytes, bytearray)):
            data = text
        else:
            if text and not text.endswith("\n"):
                text += "\n"

            if WIN:
                data = text.replace("\n", "\r\n").encode("utf-8-sig")
            else:
                data = text.encode("utf-8")

        fd, name = tempfile.mkstemp(prefix="editor-", suffix=self.extension)
        f: t.BinaryIO

        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)

            # If the filesystem resolution is 1 second, like Mac OS
            # 10.12 Extended, or 2 seconds, like FAT32, and the editor
            # closes very fast, require_save can fail. Set the modified
            # time to be 2 seconds in the past to work around this.
            os.utime(name, (os.path.getatime(name), os.path.getmtime(name) - 2))
            # Depending on the resolution, the exact value might not be
            # recorded, so get the new recorded value.
            timestamp = os.path.getmtime(name)

            self.edit_file(name)

            if self.require_save and os.path.getmtime(name) == timestamp:
                return None

            with open(name, "rb") as f:
                rv = f.read()

            if isinstance(text, (bytes, bytearray)):
                return rv

            return rv.decode("utf-8-sig").replace("\r\n", "\n")  # type: ignore
        finally:
            os.unlink(name)


def open_url(url: str, wait: bool = False, locate: bool = False) -> int:
    import subprocess

    def _unquote_file(url: str) -> str:
        from urllib.parse import unquote

        if url.startswith("file://"):
            url = unquote(url[7:])

        return url

    if sys.platform == "darwin":
        args = ["open"]
        if wait:
            args.append("-W")
        if locate:
            args.append("-R")
        args.append(_unquote_file(url))
        null = open("/dev/null", "w")
        try:
            return subprocess.Popen(args, stderr=null).wait()
        finally:
            null.close()
    elif WIN:
        if locate:
            url = _unquote_file(url)
            args = ["explorer", f"/select,{url}"]
        else:
            args = ["start"]
            if wait:
                args.append("/WAIT")
            args.append("")
            args.append(url)
        try:
            return subprocess.call(args)
        except OSError:
            # Command not found
            return 127
    elif CYGWIN:
        if locate:
            url = _unquote_file(url)
            args = ["cygstart", os.path.dirname(url)]
        else:
            args = ["cygstart"]
            if wait:
                args.append("-w")
            args.append(url)
        try:
            return subprocess.call(args)
        except OSError:
            # Command not found
            return 127

    try:
        if locate:
            url = os.path.dirname(_unquote_file(url)) or "."
        else:
            url = _unquote_file(url)
        c = subprocess.Popen(["xdg-open", url])
        if wait:
            return c.wait()
        return 0
    except OSError:
        if url.startswith(("http://", "https://")) and not locate and not wait:
            import webbrowser

            webbrowser.open(url)
            return 0
        return 1


def _translate_ch_to_exc(ch: str) -> t.Optional[BaseException]:
    if ch == "\x03":
        raise KeyboardInterrupt()

    if ch == "\x04" and not WIN:  # Unix-like, Ctrl+D
        raise EOFError()

    if ch == "\x1a" and WIN:  # Windows, Ctrl+Z
        raise EOFError()

    return None


if WIN:
    import msvcrt

    @contextlib.contextmanager
    def raw_terminal() -> t.Iterator[int]:
        yield -1

    def getchar(echo: bool) -> str:
        # The function `getch` will return a bytes object corresponding to
        # the pressed character. Since Windows 10 build 1803, it will also
        # return \x00 when called a second time after pressing a regular key.
        #
        # `getwch` does not share this probably-bugged behavior. Moreover, it
        # returns a Unicode object by default, which is what we want.
        #
        # Either of these functions will return \x00 or \xe0 to indicate
        # a special key, and you need to call the same function again to get
        # the "rest" of the code. The fun part is that \u00e0 is
        # "latin small letter a with grave", so if you type that on a French
        # keyboard, you _also_ get a \xe0.
        # E.g., consider the Up arrow. This returns \xe0 and then \x48. The
        # resulting Unicode string reads as "a with grave" + "capital H".
        # This is indistinguishable from when the user actually types
        # "a with grave" and then "capital H".
        #
        # When \xe0 is returned, we assume it's part of a special-key sequence
        # and call `getwch` again, but that means that when the user types
        # the \u00e0 character, `getchar` doesn't return until a second
        # character is typed.
        # The alternative is returning immediately, but that would mess up
        # cross-platform handling of arrow keys and others that start with
        # \xe0. Another option is using `getch`, but then we can't reliably
        # read non-ASCII characters, because return values of `getch` are
        # limited to the current 8-bit codepage.
        #
        # Anyway, Click doesn't claim to do this Right(tm), and using `getwch`
        # is doing the right thing in more situations than with `getch`.
        func: t.Callable[[], str]

        if echo:
            func = msvcrt.getwche  # type: ignore
        else:
            func = msvcrt.getwch  # type: ignore

        rv = func()

        if rv in ("\x00", "\xe0"):
            # \x00 and \xe0 are control characters that indicate special key,
            # see above.
            rv += func()

        _translate_ch_to_exc(rv)
        return rv

else:
    import termios
    import tty

    @contextlib.contextmanager
    def raw_terminal() -> t.Iterator[int]:
        f: t.Optional[t.TextIO]
        fd: int

        if not isatty(sys.stdin):
            f = open("/dev/tty")
            fd = f.fileno()
        else:
            fd = sys.stdin.fileno()
            f = None

        try:
            old_settings = termios.tcgetattr(fd)

            try:
                tty.setraw(fd)
                yield fd
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                sys.stdout.flush()

                if f is not None:
                    f.close()
        except termios.error:
            pass

    def getchar(echo: bool) -> str:
        with raw_terminal() as fd:
            ch = os.read(fd, 32).decode(get_best_encoding(sys.stdin), "replace")

            if echo and isatty(sys.stdout):
                sys.stdout.write(ch)

            _translate_ch_to_exc(ch)
            return ch

from __future__ import annotations

import functools
import sys
from collections.abc import Generator, Iterable, Iterator
from typing import Callable, Literal, TypeVar

from pip._vendor.rich.progress import (
    BarColumn,
    DownloadColumn,
    FileSizeColumn,
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from pip._internal.cli.spinners import RateLimiter
from pip._internal.req.req_install import InstallRequirement
from pip._internal.utils.logging import get_console, get_indentation

T = TypeVar("T")
ProgressRenderer = Callable[[Iterable[T]], Iterator[T]]
BarType = Literal["on", "off", "raw"]


def _rich_download_progress_bar(
    iterable: Iterable[bytes],
    *,
    bar_type: BarType,
    size: int | None,
    initial_progress: int | None = None,
) -> Generator[bytes, None, None]:
    assert bar_type == "on", "This should only be used in the default mode."

    if not size:
        total = float("inf")
        columns: tuple[ProgressColumn, ...] = (
            TextColumn("[progress.description]{task.description}"),
            SpinnerColumn("line", speed=1.5),
            FileSizeColumn(),
            TransferSpeedColumn(),
            TimeElapsedColumn(),
        )
    else:
        total = size
        columns = (
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TextColumn("{task.fields[time_description]}"),
            TimeRemainingColumn(elapsed_when_finished=True),
        )

    progress = Progress(*columns, refresh_per_second=5)
    task_id = progress.add_task(
        " " * (get_indentation() + 2), total=total, time_description="eta"
    )
    if initial_progress is not None:
        progress.update(task_id, advance=initial_progress)
    with progress:
        for chunk in iterable:
            yield chunk
            progress.update(task_id, advance=len(chunk))
        progress.update(task_id, time_description="")


def _rich_install_progress_bar(
    iterable: Iterable[InstallRequirement], *, total: int
) -> Iterator[InstallRequirement]:
    columns = (
        TextColumn("{task.fields[indent]}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("{task.description}"),
    )
    console = get_console()

    bar = Progress(*columns, refresh_per_second=6, console=console, transient=True)
    # Hiding the progress bar at initialization forces a refresh cycle to occur
    # until the bar appears, avoiding very short flashes.
    task = bar.add_task("", total=total, indent=" " * get_indentation(), visible=False)
    with bar:
        for req in iterable:
            bar.update(task, description=rf"\[{req.name}]", visible=True)
            yield req
            bar.advance(task)


def _raw_progress_bar(
    iterable: Iterable[bytes],
    *,
    size: int | None,
    initial_progress: int | None = None,
) -> Generator[bytes, None, None]:
    def write_progress(current: int, total: int) -> None:
        sys.stdout.write(f"Progress {current} of {total}\n")
        sys.stdout.flush()

    current = initial_progress or 0
    total = size or 0
    rate_limiter = RateLimiter(0.25)

    write_progress(current, total)
    for chunk in iterable:
        current += len(chunk)
        if rate_limiter.ready() or current == total:
            write_progress(current, total)
            rate_limiter.reset()
        yield chunk


def get_download_progress_renderer(
    *, bar_type: BarType, size: int | None = None, initial_progress: int | None = None
) -> ProgressRenderer[bytes]:
    """Get an object that can be used to render the download progress.

    Returns a callable, that takes an iterable to "wrap".
    """
    if bar_type == "on":
        return functools.partial(
            _rich_download_progress_bar,
            bar_type=bar_type,
            size=size,
            initial_progress=initial_progress,
        )
    elif bar_type == "raw":
        return functools.partial(
            _raw_progress_bar,
            size=size,
            initial_progress=initial_progress,
        )
    else:
        return iter  # no-op, when passed an iterator


def get_install_progress_renderer(
    *, bar_type: BarType, total: int
) -> ProgressRenderer[InstallRequirement]:
    """Get an object that can be used to render the install progress.
    Returns a callable, that takes an iterable to "wrap".
    """
    if bar_type == "on":
        return functools.partial(_rich_install_progress_bar, total=total)
    else:
        return iter

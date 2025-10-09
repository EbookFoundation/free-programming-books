from types import TracebackType
from typing import Optional, Type

from .console import Console, RenderableType
from .jupyter import JupyterMixin
from .live import Live
from .spinner import Spinner
from .style import StyleType


class Status(JupyterMixin):
    """Displays a status indicator with a 'spinner' animation.

    Args:
        status (RenderableType): A status renderable (str or Text typically).
        console (Console, optional): Console instance to use, or None for global console. Defaults to None.
        spinner (str, optional): Name of spinner animation (see python -m rich.spinner). Defaults to "dots".
        spinner_style (StyleType, optional): Style of spinner. Defaults to "status.spinner".
        speed (float, optional): Speed factor for spinner animation. Defaults to 1.0.
        refresh_per_second (float, optional): Number of refreshes per second. Defaults to 12.5.
    """

    def __init__(
        self,
        status: RenderableType,
        *,
        console: Optional[Console] = None,
        spinner: str = "dots",
        spinner_style: StyleType = "status.spinner",
        speed: float = 1.0,
        refresh_per_second: float = 12.5,
    ):
        self.status = status
        self.spinner_style = spinner_style
        self.speed = speed
        self._spinner = Spinner(spinner, text=status, style=spinner_style, speed=speed)
        self._live = Live(
            self.renderable,
            console=console,
            refresh_per_second=refresh_per_second,
            transient=True,
        )

    @property
    def renderable(self) -> Spinner:
        return self._spinner

    @property
    def console(self) -> "Console":
        """Get the Console used by the Status objects."""
        return self._live.console

    def update(
        self,
        status: Optional[RenderableType] = None,
        *,
        spinner: Optional[str] = None,
        spinner_style: Optional[StyleType] = None,
        speed: Optional[float] = None,
    ) -> None:
        """Update status.

        Args:
            status (Optional[RenderableType], optional): New status renderable or None for no change. Defaults to None.
            spinner (Optional[str], optional): New spinner or None for no change. Defaults to None.
            spinner_style (Optional[StyleType], optional): New spinner style or None for no change. Defaults to None.
            speed (Optional[float], optional): Speed factor for spinner animation or None for no change. Defaults to None.
        """
        if status is not None:
            self.status = status
        if spinner_style is not None:
            self.spinner_style = spinner_style
        if speed is not None:
            self.speed = speed
        if spinner is not None:
            self._spinner = Spinner(
                spinner, text=self.status, style=self.spinner_style, speed=self.speed
            )
            self._live.update(self.renderable, refresh=True)
        else:
            self._spinner.update(
                text=self.status, style=self.spinner_style, speed=self.speed
            )

    def start(self) -> None:
        """Start the status animation."""
        self._live.start()

    def stop(self) -> None:
        """Stop the spinner animation."""
        self._live.stop()

    def __rich__(self) -> RenderableType:
        return self.renderable

    def __enter__(self) -> "Status":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.stop()


if __name__ == "__main__":  # pragma: no cover
    from time import sleep

    from .console import Console

    console = Console()
    with console.status("[magenta]Covid detector booting up") as status:
        sleep(3)
        console.log("Importing advanced AI")
        sleep(3)
        console.log("Advanced Covid AI Ready")
        sleep(3)
        status.update(status="[bold blue] Scanning for Covid", spinner="earth")
        sleep(3)
        console.log("Found 10,000,000,000 copies of Covid32.exe")
        sleep(3)
        status.update(
            status="[bold red]Moving Covid32.exe to Trash",
            spinner="bouncingBall",
            spinner_style="yellow",
        )
        sleep(5)
    console.print("[bold green]Covid deleted successfully")

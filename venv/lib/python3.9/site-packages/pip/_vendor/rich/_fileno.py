from __future__ import annotations

from typing import IO, Callable


def get_fileno(file_like: IO[str]) -> int | None:
    """Get fileno() from a file, accounting for poorly implemented file-like objects.

    Args:
        file_like (IO): A file-like object.

    Returns:
        int | None: The result of fileno if available, or None if operation failed.
    """
    fileno: Callable[[], int] | None = getattr(file_like, "fileno", None)
    if fileno is not None:
        try:
            return fileno()
        except Exception:
            # `fileno` is documented as potentially raising a OSError
            # Alas, from the issues, there are so many poorly implemented file-like objects,
            # that `fileno()` can raise just about anything.
            return None
    return None

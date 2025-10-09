from __future__ import annotations

import functools
from time import perf_counter, sleep
from typing import TYPE_CHECKING, Callable, TypeVar

if TYPE_CHECKING:
    from typing_extensions import ParamSpec

    T = TypeVar("T")
    P = ParamSpec("P")


def retry(
    wait: float, stop_after_delay: float
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to automatically retry a function on error.

    If the function raises, the function is recalled with the same arguments
    until it returns or the time limit is reached. When the time limit is
    surpassed, the last exception raised is reraised.

    :param wait: The time to wait after an error before retrying, in seconds.
    :param stop_after_delay: The time limit after which retries will cease,
        in seconds.
    """

    def wrapper(func: Callable[P, T]) -> Callable[P, T]:

        @functools.wraps(func)
        def retry_wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            # The performance counter is monotonic on all platforms we care
            # about and has much better resolution than time.monotonic().
            start_time = perf_counter()
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if perf_counter() - start_time > stop_after_delay:
                        raise
                    sleep(wait)

        return retry_wrapped

    return wrapper

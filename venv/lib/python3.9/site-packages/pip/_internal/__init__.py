from __future__ import annotations

from pip._internal.utils import _log

# init_logging() must be called before any call to logging.getLogger()
# which happens at import of most modules.
_log.init_logging()


def main(args: list[str] | None = None) -> int:
    """This is preserved for old console scripts that may still be referencing
    it.

    For additional details, see https://github.com/pypa/pip/issues/7498.
    """
    from pip._internal.utils.entrypoints import _wrapper

    return _wrapper(args)

"""Customize logging

Defines custom logger class for the `logger.verbose(...)` method.

init_logging() must be called before any other modules that call logging.getLogger.
"""

import logging
from typing import Any, cast

# custom log level for `--verbose` output
# between DEBUG and INFO
VERBOSE = 15


class VerboseLogger(logging.Logger):
    """Custom Logger, defining a verbose log-level

    VERBOSE is between INFO and DEBUG.
    """

    def verbose(self, msg: str, *args: Any, **kwargs: Any) -> None:
        return self.log(VERBOSE, msg, *args, **kwargs)


def getLogger(name: str) -> VerboseLogger:
    """logging.getLogger, but ensures our VerboseLogger class is returned"""
    return cast(VerboseLogger, logging.getLogger(name))


def init_logging() -> None:
    """Register our VerboseLogger and VERBOSE log level.

    Should be called before any calls to getLogger(),
    i.e. in pip._internal.__init__
    """
    logging.setLoggerClass(VerboseLogger)
    logging.addLevelName(VERBOSE, "VERBOSE")

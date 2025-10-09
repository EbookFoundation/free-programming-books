"""setuptools.errors

Provides exceptions used by setuptools modules.
"""

from distutils.errors import DistutilsError


class RemovedCommandError(DistutilsError, RuntimeError):
    """Error used for commands that have been removed in setuptools.

    Since ``setuptools`` is built on ``distutils``, simply removing a command
    from ``setuptools`` will make the behavior fall back to ``distutils``; this
    error is raised if a command exists in ``distutils`` but has been actively
    removed in ``setuptools``.
    """

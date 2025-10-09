from distutils import log
from distutils.command import upload as orig

from setuptools.errors import RemovedCommandError


class upload(orig.upload):
    """Formerly used to upload packages to PyPI."""

    def run(self):
        msg = (
            "The upload command has been removed, use twine to upload "
            + "instead (https://pypi.org/p/twine)"
        )

        self.announce("ERROR: " + msg, log.ERROR)
        raise RemovedCommandError(msg)

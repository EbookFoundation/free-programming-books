from distutils.util import convert_path
from distutils import log
from distutils.errors import DistutilsOptionError
import os
import shutil

from setuptools import Command


class rotate(Command):
    """Delete older distributions"""

    description = "delete older distributions, keeping N newest files"
    user_options = [
        ('match=', 'm', "patterns to match (required)"),
        ('dist-dir=', 'd', "directory where the distributions are"),
        ('keep=', 'k', "number of matching distributions to keep"),
    ]

    boolean_options = []

    def initialize_options(self):
        self.match = None
        self.dist_dir = None
        self.keep = None

    def finalize_options(self):
        if self.match is None:
            raise DistutilsOptionError(
                "Must specify one or more (comma-separated) match patterns "
                "(e.g. '.zip' or '.egg')"
            )
        if self.keep is None:
            raise DistutilsOptionError("Must specify number of files to keep")
        try:
            self.keep = int(self.keep)
        except ValueError as e:
            raise DistutilsOptionError("--keep must be an integer") from e
        if isinstance(self.match, str):
            self.match = [
                convert_path(p.strip()) for p in self.match.split(',')
            ]
        self.set_undefined_options('bdist', ('dist_dir', 'dist_dir'))

    def run(self):
        self.run_command("egg_info")
        from glob import glob

        for pattern in self.match:
            pattern = self.distribution.get_name() + '*' + pattern
            files = glob(os.path.join(self.dist_dir, pattern))
            files = [(os.path.getmtime(f), f) for f in files]
            files.sort()
            files.reverse()

            log.info("%d file(s) matching %s", len(files), pattern)
            files = files[self.keep:]
            for (t, f) in files:
                log.info("Deleting %s", f)
                if not self.dry_run:
                    if os.path.isdir(f):
                        shutil.rmtree(f)
                    else:
                        os.unlink(f)

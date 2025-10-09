"""
Create a dist_info directory
As defined in the wheel specification
"""

import os

from distutils.core import Command
from distutils import log


class dist_info(Command):

    description = 'create a .dist-info directory'

    user_options = [
        ('egg-base=', 'e', "directory containing .egg-info directories"
                           " (default: top of the source tree)"),
    ]

    def initialize_options(self):
        self.egg_base = None

    def finalize_options(self):
        pass

    def run(self):
        egg_info = self.get_finalized_command('egg_info')
        egg_info.egg_base = self.egg_base
        egg_info.finalize_options()
        egg_info.run()
        dist_info_dir = egg_info.egg_info[:-len('.egg-info')] + '.dist-info'
        log.info("creating '{}'".format(os.path.abspath(dist_info_dir)))

        bdist_wheel = self.get_finalized_command('bdist_wheel')
        bdist_wheel.egg2dist(egg_info.egg_info, dist_info_dir)

from distutils import log, dir_util
import os

from setuptools import Command
from setuptools import namespaces
from setuptools.archive_util import unpack_archive
import pkg_resources


class install_egg_info(namespaces.Installer, Command):
    """Install an .egg-info directory for the package"""

    description = "Install an .egg-info directory for the package"

    user_options = [
        ('install-dir=', 'd', "directory to install to"),
    ]

    def initialize_options(self):
        self.install_dir = None

    def finalize_options(self):
        self.set_undefined_options('install_lib',
                                   ('install_dir', 'install_dir'))
        ei_cmd = self.get_finalized_command("egg_info")
        basename = pkg_resources.Distribution(
            None, None, ei_cmd.egg_name, ei_cmd.egg_version
        ).egg_name() + '.egg-info'
        self.source = ei_cmd.egg_info
        self.target = os.path.join(self.install_dir, basename)
        self.outputs = []

    def run(self):
        self.run_command('egg_info')
        if os.path.isdir(self.target) and not os.path.islink(self.target):
            dir_util.remove_tree(self.target, dry_run=self.dry_run)
        elif os.path.exists(self.target):
            self.execute(os.unlink, (self.target,), "Removing " + self.target)
        if not self.dry_run:
            pkg_resources.ensure_directory(self.target)
        self.execute(
            self.copytree, (), "Copying %s to %s" % (self.source, self.target)
        )
        self.install_namespaces()

    def get_outputs(self):
        return self.outputs

    def copytree(self):
        # Copy the .egg-info tree to site-packages
        def skimmer(src, dst):
            # filter out source-control directories; note that 'src' is always
            # a '/'-separated path, regardless of platform.  'dst' is a
            # platform-specific path.
            for skip in '.svn/', 'CVS/':
                if src.startswith(skip) or '/' + skip in src:
                    return None
            self.outputs.append(dst)
            log.debug("Copying %s to %s", src, dst)
            return dst

        unpack_archive(self.source, self.target, skimmer)

"""distutils.command.bdist_dumb

Implements the Distutils 'bdist_dumb' command (create a "dumb" built
distribution -- i.e., just an archive to be unpacked under $prefix or
$exec_prefix)."""

import os
from distutils.core import Command
from distutils.util import get_platform
from distutils.dir_util import remove_tree, ensure_relative
from distutils.errors import *
from distutils.sysconfig import get_python_version
from distutils import log

class bdist_dumb(Command):

    description = "create a \"dumb\" built distribution"

    user_options = [('bdist-dir=', 'd',
                     "temporary directory for creating the distribution"),
                    ('plat-name=', 'p',
                     "platform name to embed in generated filenames "
                     "(default: %s)" % get_platform()),
                    ('format=', 'f',
                     "archive format to create (tar, gztar, bztar, xztar, "
                     "ztar, zip)"),
                    ('keep-temp', 'k',
                     "keep the pseudo-installation tree around after " +
                     "creating the distribution archive"),
                    ('dist-dir=', 'd',
                     "directory to put final built distributions in"),
                    ('skip-build', None,
                     "skip rebuilding everything (for testing/debugging)"),
                    ('relative', None,
                     "build the archive using relative paths "
                     "(default: false)"),
                    ('owner=', 'u',
                     "Owner name used when creating a tar file"
                     " [default: current user]"),
                    ('group=', 'g',
                     "Group name used when creating a tar file"
                     " [default: current group]"),
                   ]

    boolean_options = ['keep-temp', 'skip-build', 'relative']

    default_format = { 'posix': 'gztar',
                       'nt': 'zip' }

    def initialize_options(self):
        self.bdist_dir = None
        self.plat_name = None
        self.format = None
        self.keep_temp = 0
        self.dist_dir = None
        self.skip_build = None
        self.relative = 0
        self.owner = None
        self.group = None

    def finalize_options(self):
        if self.bdist_dir is None:
            bdist_base = self.get_finalized_command('bdist').bdist_base
            self.bdist_dir = os.path.join(bdist_base, 'dumb')

        if self.format is None:
            try:
                self.format = self.default_format[os.name]
            except KeyError:
                raise DistutilsPlatformError(
                       "don't know how to create dumb built distributions "
                       "on platform %s" % os.name)

        self.set_undefined_options('bdist',
                                   ('dist_dir', 'dist_dir'),
                                   ('plat_name', 'plat_name'),
                                   ('skip_build', 'skip_build'))

    def run(self):
        if not self.skip_build:
            self.run_command('build')

        install = self.reinitialize_command('install', reinit_subcommands=1)
        install.root = self.bdist_dir
        install.skip_build = self.skip_build
        install.warn_dir = 0

        log.info("installing to %s", self.bdist_dir)
        self.run_command('install')

        # And make an archive relative to the root of the
        # pseudo-installation tree.
        archive_basename = "%s.%s" % (self.distribution.get_fullname(),
                                      self.plat_name)

        pseudoinstall_root = os.path.join(self.dist_dir, archive_basename)
        if not self.relative:
            archive_root = self.bdist_dir
        else:
            if (self.distribution.has_ext_modules() and
                (install.install_base != install.install_platbase)):
                raise DistutilsPlatformError(
                       "can't make a dumb built distribution where "
                       "base and platbase are different (%s, %s)"
                       % (repr(install.install_base),
                          repr(install.install_platbase)))
            else:
                archive_root = os.path.join(self.bdist_dir,
                                   ensure_relative(install.install_base))

        # Make the archive
        filename = self.make_archive(pseudoinstall_root,
                                     self.format, root_dir=archive_root,
                                     owner=self.owner, group=self.group)
        if self.distribution.has_ext_modules():
            pyversion = get_python_version()
        else:
            pyversion = 'any'
        self.distribution.dist_files.append(('bdist_dumb', pyversion,
                                             filename))

        if not self.keep_temp:
            remove_tree(self.bdist_dir, dry_run=self.dry_run)

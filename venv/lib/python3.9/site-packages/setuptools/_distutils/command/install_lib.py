"""distutils.command.install_lib

Implements the Distutils 'install_lib' command
(install all Python modules)."""

import os
import importlib.util
import sys

from distutils.core import Command
from distutils.errors import DistutilsOptionError


# Extension for Python source files.
PYTHON_SOURCE_EXTENSION = ".py"

class install_lib(Command):

    description = "install all Python modules (extensions and pure Python)"

    # The byte-compilation options are a tad confusing.  Here are the
    # possible scenarios:
    #   1) no compilation at all (--no-compile --no-optimize)
    #   2) compile .pyc only (--compile --no-optimize; default)
    #   3) compile .pyc and "opt-1" .pyc (--compile --optimize)
    #   4) compile "opt-1" .pyc only (--no-compile --optimize)
    #   5) compile .pyc and "opt-2" .pyc (--compile --optimize-more)
    #   6) compile "opt-2" .pyc only (--no-compile --optimize-more)
    #
    # The UI for this is two options, 'compile' and 'optimize'.
    # 'compile' is strictly boolean, and only decides whether to
    # generate .pyc files.  'optimize' is three-way (0, 1, or 2), and
    # decides both whether to generate .pyc files and what level of
    # optimization to use.

    user_options = [
        ('install-dir=', 'd', "directory to install to"),
        ('build-dir=','b', "build directory (where to install from)"),
        ('force', 'f', "force installation (overwrite existing files)"),
        ('compile', 'c', "compile .py to .pyc [default]"),
        ('no-compile', None, "don't compile .py files"),
        ('optimize=', 'O',
         "also compile with optimization: -O1 for \"python -O\", "
         "-O2 for \"python -OO\", and -O0 to disable [default: -O0]"),
        ('skip-build', None, "skip the build steps"),
        ]

    boolean_options = ['force', 'compile', 'skip-build']
    negative_opt = {'no-compile' : 'compile'}

    def initialize_options(self):
        # let the 'install' command dictate our installation directory
        self.install_dir = None
        self.build_dir = None
        self.force = 0
        self.compile = None
        self.optimize = None
        self.skip_build = None

    def finalize_options(self):
        # Get all the information we need to install pure Python modules
        # from the umbrella 'install' command -- build (source) directory,
        # install (target) directory, and whether to compile .py files.
        self.set_undefined_options('install',
                                   ('build_lib', 'build_dir'),
                                   ('install_lib', 'install_dir'),
                                   ('force', 'force'),
                                   ('compile', 'compile'),
                                   ('optimize', 'optimize'),
                                   ('skip_build', 'skip_build'),
                                  )

        if self.compile is None:
            self.compile = True
        if self.optimize is None:
            self.optimize = False

        if not isinstance(self.optimize, int):
            try:
                self.optimize = int(self.optimize)
                if self.optimize not in (0, 1, 2):
                    raise AssertionError
            except (ValueError, AssertionError):
                raise DistutilsOptionError("optimize must be 0, 1, or 2")

    def run(self):
        # Make sure we have built everything we need first
        self.build()

        # Install everything: simply dump the entire contents of the build
        # directory to the installation directory (that's the beauty of
        # having a build directory!)
        outfiles = self.install()

        # (Optionally) compile .py to .pyc
        if outfiles is not None and self.distribution.has_pure_modules():
            self.byte_compile(outfiles)

    # -- Top-level worker functions ------------------------------------
    # (called from 'run()')

    def build(self):
        if not self.skip_build:
            if self.distribution.has_pure_modules():
                self.run_command('build_py')
            if self.distribution.has_ext_modules():
                self.run_command('build_ext')

    def install(self):
        if os.path.isdir(self.build_dir):
            outfiles = self.copy_tree(self.build_dir, self.install_dir)
        else:
            self.warn("'%s' does not exist -- no Python modules to install" %
                      self.build_dir)
            return
        return outfiles

    def byte_compile(self, files):
        if sys.dont_write_bytecode:
            self.warn('byte-compiling is disabled, skipping.')
            return

        from distutils.util import byte_compile

        # Get the "--root" directory supplied to the "install" command,
        # and use it as a prefix to strip off the purported filename
        # encoded in bytecode files.  This is far from complete, but it
        # should at least generate usable bytecode in RPM distributions.
        install_root = self.get_finalized_command('install').root

        if self.compile:
            byte_compile(files, optimize=0,
                         force=self.force, prefix=install_root,
                         dry_run=self.dry_run)
        if self.optimize > 0:
            byte_compile(files, optimize=self.optimize,
                         force=self.force, prefix=install_root,
                         verbose=self.verbose, dry_run=self.dry_run)


    # -- Utility methods -----------------------------------------------

    def _mutate_outputs(self, has_any, build_cmd, cmd_option, output_dir):
        if not has_any:
            return []

        build_cmd = self.get_finalized_command(build_cmd)
        build_files = build_cmd.get_outputs()
        build_dir = getattr(build_cmd, cmd_option)

        prefix_len = len(build_dir) + len(os.sep)
        outputs = []
        for file in build_files:
            outputs.append(os.path.join(output_dir, file[prefix_len:]))

        return outputs

    def _bytecode_filenames(self, py_filenames):
        bytecode_files = []
        for py_file in py_filenames:
            # Since build_py handles package data installation, the
            # list of outputs can contain more than just .py files.
            # Make sure we only report bytecode for the .py files.
            ext = os.path.splitext(os.path.normcase(py_file))[1]
            if ext != PYTHON_SOURCE_EXTENSION:
                continue
            if self.compile:
                bytecode_files.append(importlib.util.cache_from_source(
                    py_file, optimization=''))
            if self.optimize > 0:
                bytecode_files.append(importlib.util.cache_from_source(
                    py_file, optimization=self.optimize))

        return bytecode_files


    # -- External interface --------------------------------------------
    # (called by outsiders)

    def get_outputs(self):
        """Return the list of files that would be installed if this command
        were actually run.  Not affected by the "dry-run" flag or whether
        modules have actually been built yet.
        """
        pure_outputs = \
            self._mutate_outputs(self.distribution.has_pure_modules(),
                                 'build_py', 'build_lib',
                                 self.install_dir)
        if self.compile:
            bytecode_outputs = self._bytecode_filenames(pure_outputs)
        else:
            bytecode_outputs = []

        ext_outputs = \
            self._mutate_outputs(self.distribution.has_ext_modules(),
                                 'build_ext', 'build_lib',
                                 self.install_dir)

        return pure_outputs + bytecode_outputs + ext_outputs

    def get_inputs(self):
        """Get the list of files that are input to this command, ie. the
        files that get installed as they are named in the build tree.
        The files in this list correspond one-to-one to the output
        filenames returned by 'get_outputs()'.
        """
        inputs = []

        if self.distribution.has_pure_modules():
            build_py = self.get_finalized_command('build_py')
            inputs.extend(build_py.get_outputs())

        if self.distribution.has_ext_modules():
            build_ext = self.get_finalized_command('build_ext')
            inputs.extend(build_ext.get_outputs())

        return inputs

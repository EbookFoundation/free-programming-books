"""distutils.command.build_py

Implements the Distutils 'build_py' command."""

import os
import importlib.util
import sys
import glob

from distutils.core import Command
from distutils.errors import *
from distutils.util import convert_path
from distutils import log

class build_py (Command):

    description = "\"build\" pure Python modules (copy to build directory)"

    user_options = [
        ('build-lib=', 'd', "directory to \"build\" (copy) to"),
        ('compile', 'c', "compile .py to .pyc"),
        ('no-compile', None, "don't compile .py files [default]"),
        ('optimize=', 'O',
         "also compile with optimization: -O1 for \"python -O\", "
         "-O2 for \"python -OO\", and -O0 to disable [default: -O0]"),
        ('force', 'f', "forcibly build everything (ignore file timestamps)"),
        ]

    boolean_options = ['compile', 'force']
    negative_opt = {'no-compile' : 'compile'}

    def initialize_options(self):
        self.build_lib = None
        self.py_modules = None
        self.package = None
        self.package_data = None
        self.package_dir = None
        self.compile = 0
        self.optimize = 0
        self.force = None

    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_lib', 'build_lib'),
                                   ('force', 'force'))

        # Get the distribution options that are aliases for build_py
        # options -- list of packages and list of modules.
        self.packages = self.distribution.packages
        self.py_modules = self.distribution.py_modules
        self.package_data = self.distribution.package_data
        self.package_dir = {}
        if self.distribution.package_dir:
            for name, path in self.distribution.package_dir.items():
                self.package_dir[name] = convert_path(path)
        self.data_files = self.get_data_files()

        # Ick, copied straight from install_lib.py (fancy_getopt needs a
        # type system!  Hell, *everything* needs a type system!!!)
        if not isinstance(self.optimize, int):
            try:
                self.optimize = int(self.optimize)
                assert 0 <= self.optimize <= 2
            except (ValueError, AssertionError):
                raise DistutilsOptionError("optimize must be 0, 1, or 2")

    def run(self):
        # XXX copy_file by default preserves atime and mtime.  IMHO this is
        # the right thing to do, but perhaps it should be an option -- in
        # particular, a site administrator might want installed files to
        # reflect the time of installation rather than the last
        # modification time before the installed release.

        # XXX copy_file by default preserves mode, which appears to be the
        # wrong thing to do: if a file is read-only in the working
        # directory, we want it to be installed read/write so that the next
        # installation of the same module distribution can overwrite it
        # without problems.  (This might be a Unix-specific issue.)  Thus
        # we turn off 'preserve_mode' when copying to the build directory,
        # since the build directory is supposed to be exactly what the
        # installation will look like (ie. we preserve mode when
        # installing).

        # Two options control which modules will be installed: 'packages'
        # and 'py_modules'.  The former lets us work with whole packages, not
        # specifying individual modules at all; the latter is for
        # specifying modules one-at-a-time.

        if self.py_modules:
            self.build_modules()
        if self.packages:
            self.build_packages()
            self.build_package_data()

        self.byte_compile(self.get_outputs(include_bytecode=0))

    def get_data_files(self):
        """Generate list of '(package,src_dir,build_dir,filenames)' tuples"""
        data = []
        if not self.packages:
            return data
        for package in self.packages:
            # Locate package source directory
            src_dir = self.get_package_dir(package)

            # Compute package build directory
            build_dir = os.path.join(*([self.build_lib] + package.split('.')))

            # Length of path to strip from found files
            plen = 0
            if src_dir:
                plen = len(src_dir)+1

            # Strip directory from globbed filenames
            filenames = [
                file[plen:] for file in self.find_data_files(package, src_dir)
                ]
            data.append((package, src_dir, build_dir, filenames))
        return data

    def find_data_files(self, package, src_dir):
        """Return filenames for package's data files in 'src_dir'"""
        globs = (self.package_data.get('', [])
                 + self.package_data.get(package, []))
        files = []
        for pattern in globs:
            # Each pattern has to be converted to a platform-specific path
            filelist = glob.glob(os.path.join(glob.escape(src_dir), convert_path(pattern)))
            # Files that match more than one pattern are only added once
            files.extend([fn for fn in filelist if fn not in files
                and os.path.isfile(fn)])
        return files

    def build_package_data(self):
        """Copy data files into build directory"""
        lastdir = None
        for package, src_dir, build_dir, filenames in self.data_files:
            for filename in filenames:
                target = os.path.join(build_dir, filename)
                self.mkpath(os.path.dirname(target))
                self.copy_file(os.path.join(src_dir, filename), target,
                               preserve_mode=False)

    def get_package_dir(self, package):
        """Return the directory, relative to the top of the source
           distribution, where package 'package' should be found
           (at least according to the 'package_dir' option, if any)."""
        path = package.split('.')

        if not self.package_dir:
            if path:
                return os.path.join(*path)
            else:
                return ''
        else:
            tail = []
            while path:
                try:
                    pdir = self.package_dir['.'.join(path)]
                except KeyError:
                    tail.insert(0, path[-1])
                    del path[-1]
                else:
                    tail.insert(0, pdir)
                    return os.path.join(*tail)
            else:
                # Oops, got all the way through 'path' without finding a
                # match in package_dir.  If package_dir defines a directory
                # for the root (nameless) package, then fallback on it;
                # otherwise, we might as well have not consulted
                # package_dir at all, as we just use the directory implied
                # by 'tail' (which should be the same as the original value
                # of 'path' at this point).
                pdir = self.package_dir.get('')
                if pdir is not None:
                    tail.insert(0, pdir)

                if tail:
                    return os.path.join(*tail)
                else:
                    return ''

    def check_package(self, package, package_dir):
        # Empty dir name means current directory, which we can probably
        # assume exists.  Also, os.path.exists and isdir don't know about
        # my "empty string means current dir" convention, so we have to
        # circumvent them.
        if package_dir != "":
            if not os.path.exists(package_dir):
                raise DistutilsFileError(
                      "package directory '%s' does not exist" % package_dir)
            if not os.path.isdir(package_dir):
                raise DistutilsFileError(
                       "supposed package directory '%s' exists, "
                       "but is not a directory" % package_dir)

        # Require __init__.py for all but the "root package"
        if package:
            init_py = os.path.join(package_dir, "__init__.py")
            if os.path.isfile(init_py):
                return init_py
            else:
                log.warn(("package init file '%s' not found " +
                          "(or not a regular file)"), init_py)

        # Either not in a package at all (__init__.py not expected), or
        # __init__.py doesn't exist -- so don't return the filename.
        return None

    def check_module(self, module, module_file):
        if not os.path.isfile(module_file):
            log.warn("file %s (for module %s) not found", module_file, module)
            return False
        else:
            return True

    def find_package_modules(self, package, package_dir):
        self.check_package(package, package_dir)
        module_files = glob.glob(os.path.join(glob.escape(package_dir), "*.py"))
        modules = []
        setup_script = os.path.abspath(self.distribution.script_name)

        for f in module_files:
            abs_f = os.path.abspath(f)
            if abs_f != setup_script:
                module = os.path.splitext(os.path.basename(f))[0]
                modules.append((package, module, f))
            else:
                self.debug_print("excluding %s" % setup_script)
        return modules

    def find_modules(self):
        """Finds individually-specified Python modules, ie. those listed by
        module name in 'self.py_modules'.  Returns a list of tuples (package,
        module_base, filename): 'package' is a tuple of the path through
        package-space to the module; 'module_base' is the bare (no
        packages, no dots) module name, and 'filename' is the path to the
        ".py" file (relative to the distribution root) that implements the
        module.
        """
        # Map package names to tuples of useful info about the package:
        #    (package_dir, checked)
        # package_dir - the directory where we'll find source files for
        #   this package
        # checked - true if we have checked that the package directory
        #   is valid (exists, contains __init__.py, ... ?)
        packages = {}

        # List of (package, module, filename) tuples to return
        modules = []

        # We treat modules-in-packages almost the same as toplevel modules,
        # just the "package" for a toplevel is empty (either an empty
        # string or empty list, depending on context).  Differences:
        #   - don't check for __init__.py in directory for empty package
        for module in self.py_modules:
            path = module.split('.')
            package = '.'.join(path[0:-1])
            module_base = path[-1]

            try:
                (package_dir, checked) = packages[package]
            except KeyError:
                package_dir = self.get_package_dir(package)
                checked = 0

            if not checked:
                init_py = self.check_package(package, package_dir)
                packages[package] = (package_dir, 1)
                if init_py:
                    modules.append((package, "__init__", init_py))

            # XXX perhaps we should also check for just .pyc files
            # (so greedy closed-source bastards can distribute Python
            # modules too)
            module_file = os.path.join(package_dir, module_base + ".py")
            if not self.check_module(module, module_file):
                continue

            modules.append((package, module_base, module_file))

        return modules

    def find_all_modules(self):
        """Compute the list of all modules that will be built, whether
        they are specified one-module-at-a-time ('self.py_modules') or
        by whole packages ('self.packages').  Return a list of tuples
        (package, module, module_file), just like 'find_modules()' and
        'find_package_modules()' do."""
        modules = []
        if self.py_modules:
            modules.extend(self.find_modules())
        if self.packages:
            for package in self.packages:
                package_dir = self.get_package_dir(package)
                m = self.find_package_modules(package, package_dir)
                modules.extend(m)
        return modules

    def get_source_files(self):
        return [module[-1] for module in self.find_all_modules()]

    def get_module_outfile(self, build_dir, package, module):
        outfile_path = [build_dir] + list(package) + [module + ".py"]
        return os.path.join(*outfile_path)

    def get_outputs(self, include_bytecode=1):
        modules = self.find_all_modules()
        outputs = []
        for (package, module, module_file) in modules:
            package = package.split('.')
            filename = self.get_module_outfile(self.build_lib, package, module)
            outputs.append(filename)
            if include_bytecode:
                if self.compile:
                    outputs.append(importlib.util.cache_from_source(
                        filename, optimization=''))
                if self.optimize > 0:
                    outputs.append(importlib.util.cache_from_source(
                        filename, optimization=self.optimize))

        outputs += [
            os.path.join(build_dir, filename)
            for package, src_dir, build_dir, filenames in self.data_files
            for filename in filenames
            ]

        return outputs

    def build_module(self, module, module_file, package):
        if isinstance(package, str):
            package = package.split('.')
        elif not isinstance(package, (list, tuple)):
            raise TypeError(
                  "'package' must be a string (dot-separated), list, or tuple")

        # Now put the module source file into the "build" area -- this is
        # easy, we just copy it somewhere under self.build_lib (the build
        # directory for Python source).
        outfile = self.get_module_outfile(self.build_lib, package, module)
        dir = os.path.dirname(outfile)
        self.mkpath(dir)
        return self.copy_file(module_file, outfile, preserve_mode=0)

    def build_modules(self):
        modules = self.find_modules()
        for (package, module, module_file) in modules:
            # Now "build" the module -- ie. copy the source file to
            # self.build_lib (the build directory for Python source).
            # (Actually, it gets copied to the directory for this package
            # under self.build_lib.)
            self.build_module(module, module_file, package)

    def build_packages(self):
        for package in self.packages:
            # Get list of (package, module, module_file) tuples based on
            # scanning the package directory.  'package' is only included
            # in the tuple so that 'find_modules()' and
            # 'find_package_tuples()' have a consistent interface; it's
            # ignored here (apart from a sanity check).  Also, 'module' is
            # the *unqualified* module name (ie. no dots, no package -- we
            # already know its package!), and 'module_file' is the path to
            # the .py file, relative to the current directory
            # (ie. including 'package_dir').
            package_dir = self.get_package_dir(package)
            modules = self.find_package_modules(package, package_dir)

            # Now loop over the modules we found, "building" each one (just
            # copy it to self.build_lib).
            for (package_, module, module_file) in modules:
                assert package == package_
                self.build_module(module, module_file, package)

    def byte_compile(self, files):
        if sys.dont_write_bytecode:
            self.warn('byte-compiling is disabled, skipping.')
            return

        from distutils.util import byte_compile
        prefix = self.build_lib
        if prefix[-1] != os.sep:
            prefix = prefix + os.sep

        # XXX this code is essentially the same as the 'byte_compile()
        # method of the "install_lib" command, except for the determination
        # of the 'prefix' string.  Hmmm.
        if self.compile:
            byte_compile(files, optimize=0,
                         force=self.force, prefix=prefix, dry_run=self.dry_run)
        if self.optimize > 0:
            byte_compile(files, optimize=self.optimize,
                         force=self.force, prefix=prefix, dry_run=self.dry_run)

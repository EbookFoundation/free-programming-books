import os
from glob import glob
from distutils.util import convert_path
from distutils.command import sdist


class sdist_add_defaults:
    """
    Mix-in providing forward-compatibility for functionality as found in
    distutils on Python 3.7.

    Do not edit the code in this class except to update functionality
    as implemented in distutils. Instead, override in the subclass.
    """

    def add_defaults(self):
        """Add all the default files to self.filelist:
          - README or README.txt
          - setup.py
          - test/test*.py
          - all pure Python modules mentioned in setup script
          - all files pointed by package_data (build_py)
          - all files defined in data_files.
          - all files defined as scripts.
          - all C sources listed as part of extensions or C libraries
            in the setup script (doesn't catch C headers!)
        Warns if (README or README.txt) or setup.py are missing; everything
        else is optional.
        """
        self._add_defaults_standards()
        self._add_defaults_optional()
        self._add_defaults_python()
        self._add_defaults_data_files()
        self._add_defaults_ext()
        self._add_defaults_c_libs()
        self._add_defaults_scripts()

    @staticmethod
    def _cs_path_exists(fspath):
        """
        Case-sensitive path existence check

        >>> sdist_add_defaults._cs_path_exists(__file__)
        True
        >>> sdist_add_defaults._cs_path_exists(__file__.upper())
        False
        """
        if not os.path.exists(fspath):
            return False
        # make absolute so we always have a directory
        abspath = os.path.abspath(fspath)
        directory, filename = os.path.split(abspath)
        return filename in os.listdir(directory)

    def _add_defaults_standards(self):
        standards = [self.READMES, self.distribution.script_name]
        for fn in standards:
            if isinstance(fn, tuple):
                alts = fn
                got_it = False
                for fn in alts:
                    if self._cs_path_exists(fn):
                        got_it = True
                        self.filelist.append(fn)
                        break

                if not got_it:
                    self.warn("standard file not found: should have one of " +
                              ', '.join(alts))
            else:
                if self._cs_path_exists(fn):
                    self.filelist.append(fn)
                else:
                    self.warn("standard file '%s' not found" % fn)

    def _add_defaults_optional(self):
        optional = ['test/test*.py', 'setup.cfg']
        for pattern in optional:
            files = filter(os.path.isfile, glob(pattern))
            self.filelist.extend(files)

    def _add_defaults_python(self):
        # build_py is used to get:
        #  - python modules
        #  - files defined in package_data
        build_py = self.get_finalized_command('build_py')

        # getting python files
        if self.distribution.has_pure_modules():
            self.filelist.extend(build_py.get_source_files())

        # getting package_data files
        # (computed in build_py.data_files by build_py.finalize_options)
        for pkg, src_dir, build_dir, filenames in build_py.data_files:
            for filename in filenames:
                self.filelist.append(os.path.join(src_dir, filename))

    def _add_defaults_data_files(self):
        # getting distribution.data_files
        if self.distribution.has_data_files():
            for item in self.distribution.data_files:
                if isinstance(item, str):
                    # plain file
                    item = convert_path(item)
                    if os.path.isfile(item):
                        self.filelist.append(item)
                else:
                    # a (dirname, filenames) tuple
                    dirname, filenames = item
                    for f in filenames:
                        f = convert_path(f)
                        if os.path.isfile(f):
                            self.filelist.append(f)

    def _add_defaults_ext(self):
        if self.distribution.has_ext_modules():
            build_ext = self.get_finalized_command('build_ext')
            self.filelist.extend(build_ext.get_source_files())

    def _add_defaults_c_libs(self):
        if self.distribution.has_c_libraries():
            build_clib = self.get_finalized_command('build_clib')
            self.filelist.extend(build_clib.get_source_files())

    def _add_defaults_scripts(self):
        if self.distribution.has_scripts():
            build_scripts = self.get_finalized_command('build_scripts')
            self.filelist.extend(build_scripts.get_source_files())


if hasattr(sdist.sdist, '_add_defaults_standards'):
    # disable the functionality already available upstream
    class sdist_add_defaults:  # noqa
        pass

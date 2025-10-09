"""distutils.command.build_ext

Implements the Distutils 'build_ext' command, for building extension
modules (currently limited to C extensions, should accommodate C++
extensions ASAP)."""

import contextlib
import os
import re
import sys
from distutils.core import Command
from distutils.errors import *
from distutils.sysconfig import customize_compiler, get_python_version
from distutils.sysconfig import get_config_h_filename
from distutils.dep_util import newer_group
from distutils.extension import Extension
from distutils.util import get_platform
from distutils import log
from . import py37compat

from site import USER_BASE

# An extension name is just a dot-separated list of Python NAMEs (ie.
# the same as a fully-qualified module name).
extension_name_re = re.compile \
    (r'^[a-zA-Z_][a-zA-Z_0-9]*(\.[a-zA-Z_][a-zA-Z_0-9]*)*$')


def show_compilers ():
    from distutils.ccompiler import show_compilers
    show_compilers()


class build_ext(Command):

    description = "build C/C++ extensions (compile/link to build directory)"

    # XXX thoughts on how to deal with complex command-line options like
    # these, i.e. how to make it so fancy_getopt can suck them off the
    # command line and make it look like setup.py defined the appropriate
    # lists of tuples of what-have-you.
    #   - each command needs a callback to process its command-line options
    #   - Command.__init__() needs access to its share of the whole
    #     command line (must ultimately come from
    #     Distribution.parse_command_line())
    #   - it then calls the current command class' option-parsing
    #     callback to deal with weird options like -D, which have to
    #     parse the option text and churn out some custom data
    #     structure
    #   - that data structure (in this case, a list of 2-tuples)
    #     will then be present in the command object by the time
    #     we get to finalize_options() (i.e. the constructor
    #     takes care of both command-line and client options
    #     in between initialize_options() and finalize_options())

    sep_by = " (separated by '%s')" % os.pathsep
    user_options = [
        ('build-lib=', 'b',
         "directory for compiled extension modules"),
        ('build-temp=', 't',
         "directory for temporary files (build by-products)"),
        ('plat-name=', 'p',
         "platform name to cross-compile for, if supported "
         "(default: %s)" % get_platform()),
        ('inplace', 'i',
         "ignore build-lib and put compiled extensions into the source " +
         "directory alongside your pure Python modules"),
        ('include-dirs=', 'I',
         "list of directories to search for header files" + sep_by),
        ('define=', 'D',
         "C preprocessor macros to define"),
        ('undef=', 'U',
         "C preprocessor macros to undefine"),
        ('libraries=', 'l',
         "external C libraries to link with"),
        ('library-dirs=', 'L',
         "directories to search for external C libraries" + sep_by),
        ('rpath=', 'R',
         "directories to search for shared C libraries at runtime"),
        ('link-objects=', 'O',
         "extra explicit link objects to include in the link"),
        ('debug', 'g',
         "compile/link with debugging information"),
        ('force', 'f',
         "forcibly build everything (ignore file timestamps)"),
        ('compiler=', 'c',
         "specify the compiler type"),
        ('parallel=', 'j',
         "number of parallel build jobs"),
        ('swig-cpp', None,
         "make SWIG create C++ files (default is C)"),
        ('swig-opts=', None,
         "list of SWIG command line options"),
        ('swig=', None,
         "path to the SWIG executable"),
        ('user', None,
         "add user include, library and rpath")
        ]

    boolean_options = ['inplace', 'debug', 'force', 'swig-cpp', 'user']

    help_options = [
        ('help-compiler', None,
         "list available compilers", show_compilers),
        ]

    def initialize_options(self):
        self.extensions = None
        self.build_lib = None
        self.plat_name = None
        self.build_temp = None
        self.inplace = 0
        self.package = None

        self.include_dirs = None
        self.define = None
        self.undef = None
        self.libraries = None
        self.library_dirs = None
        self.rpath = None
        self.link_objects = None
        self.debug = None
        self.force = None
        self.compiler = None
        self.swig = None
        self.swig_cpp = None
        self.swig_opts = None
        self.user = None
        self.parallel = None

    def finalize_options(self):
        from distutils import sysconfig

        self.set_undefined_options('build',
                                   ('build_lib', 'build_lib'),
                                   ('build_temp', 'build_temp'),
                                   ('compiler', 'compiler'),
                                   ('debug', 'debug'),
                                   ('force', 'force'),
                                   ('parallel', 'parallel'),
                                   ('plat_name', 'plat_name'),
                                   )

        if self.package is None:
            self.package = self.distribution.ext_package

        self.extensions = self.distribution.ext_modules

        # Make sure Python's include directories (for Python.h, pyconfig.h,
        # etc.) are in the include search path.
        py_include = sysconfig.get_python_inc()
        plat_py_include = sysconfig.get_python_inc(plat_specific=1)
        if self.include_dirs is None:
            self.include_dirs = self.distribution.include_dirs or []
        if isinstance(self.include_dirs, str):
            self.include_dirs = self.include_dirs.split(os.pathsep)

        # If in a virtualenv, add its include directory
        # Issue 16116
        if sys.exec_prefix != sys.base_exec_prefix:
            self.include_dirs.append(os.path.join(sys.exec_prefix, 'include'))

        # Put the Python "system" include dir at the end, so that
        # any local include dirs take precedence.
        self.include_dirs.extend(py_include.split(os.path.pathsep))
        if plat_py_include != py_include:
            self.include_dirs.extend(
                plat_py_include.split(os.path.pathsep))

        self.ensure_string_list('libraries')
        self.ensure_string_list('link_objects')

        # Life is easier if we're not forever checking for None, so
        # simplify these options to empty lists if unset
        if self.libraries is None:
            self.libraries = []
        if self.library_dirs is None:
            self.library_dirs = []
        elif isinstance(self.library_dirs, str):
            self.library_dirs = self.library_dirs.split(os.pathsep)

        if self.rpath is None:
            self.rpath = []
        elif isinstance(self.rpath, str):
            self.rpath = self.rpath.split(os.pathsep)

        # for extensions under windows use different directories
        # for Release and Debug builds.
        # also Python's library directory must be appended to library_dirs
        if os.name == 'nt':
            # the 'libs' directory is for binary installs - we assume that
            # must be the *native* platform.  But we don't really support
            # cross-compiling via a binary install anyway, so we let it go.
            self.library_dirs.append(os.path.join(sys.exec_prefix, 'libs'))
            if sys.base_exec_prefix != sys.prefix:  # Issue 16116
                self.library_dirs.append(os.path.join(sys.base_exec_prefix, 'libs'))
            if self.debug:
                self.build_temp = os.path.join(self.build_temp, "Debug")
            else:
                self.build_temp = os.path.join(self.build_temp, "Release")

            # Append the source distribution include and library directories,
            # this allows distutils on windows to work in the source tree
            self.include_dirs.append(os.path.dirname(get_config_h_filename()))
            _sys_home = getattr(sys, '_home', None)
            if _sys_home:
                self.library_dirs.append(_sys_home)

            # Use the .lib files for the correct architecture
            if self.plat_name == 'win32':
                suffix = 'win32'
            else:
                # win-amd64
                suffix = self.plat_name[4:]
            new_lib = os.path.join(sys.exec_prefix, 'PCbuild')
            if suffix:
                new_lib = os.path.join(new_lib, suffix)
            self.library_dirs.append(new_lib)

        # For extensions under Cygwin, Python's library directory must be
        # appended to library_dirs
        if sys.platform[:6] == 'cygwin':
            if sys.executable.startswith(os.path.join(sys.exec_prefix, "bin")):
                # building third party extensions
                self.library_dirs.append(os.path.join(sys.prefix, "lib",
                                                      "python" + get_python_version(),
                                                      "config"))
            else:
                # building python standard extensions
                self.library_dirs.append('.')

        # For building extensions with a shared Python library,
        # Python's library directory must be appended to library_dirs
        # See Issues: #1600860, #4366
        if (sysconfig.get_config_var('Py_ENABLE_SHARED')):
            if not sysconfig.python_build:
                # building third party extensions
                self.library_dirs.append(sysconfig.get_config_var('LIBDIR'))
            else:
                # building python standard extensions
                self.library_dirs.append('.')

        # The argument parsing will result in self.define being a string, but
        # it has to be a list of 2-tuples.  All the preprocessor symbols
        # specified by the 'define' option will be set to '1'.  Multiple
        # symbols can be separated with commas.

        if self.define:
            defines = self.define.split(',')
            self.define = [(symbol, '1') for symbol in defines]

        # The option for macros to undefine is also a string from the
        # option parsing, but has to be a list.  Multiple symbols can also
        # be separated with commas here.
        if self.undef:
            self.undef = self.undef.split(',')

        if self.swig_opts is None:
            self.swig_opts = []
        else:
            self.swig_opts = self.swig_opts.split(' ')

        # Finally add the user include and library directories if requested
        if self.user:
            user_include = os.path.join(USER_BASE, "include")
            user_lib = os.path.join(USER_BASE, "lib")
            if os.path.isdir(user_include):
                self.include_dirs.append(user_include)
            if os.path.isdir(user_lib):
                self.library_dirs.append(user_lib)
                self.rpath.append(user_lib)

        if isinstance(self.parallel, str):
            try:
                self.parallel = int(self.parallel)
            except ValueError:
                raise DistutilsOptionError("parallel should be an integer")

    def run(self):
        from distutils.ccompiler import new_compiler

        # 'self.extensions', as supplied by setup.py, is a list of
        # Extension instances.  See the documentation for Extension (in
        # distutils.extension) for details.
        #
        # For backwards compatibility with Distutils 0.8.2 and earlier, we
        # also allow the 'extensions' list to be a list of tuples:
        #    (ext_name, build_info)
        # where build_info is a dictionary containing everything that
        # Extension instances do except the name, with a few things being
        # differently named.  We convert these 2-tuples to Extension
        # instances as needed.

        if not self.extensions:
            return

        # If we were asked to build any C/C++ libraries, make sure that the
        # directory where we put them is in the library search path for
        # linking extensions.
        if self.distribution.has_c_libraries():
            build_clib = self.get_finalized_command('build_clib')
            self.libraries.extend(build_clib.get_library_names() or [])
            self.library_dirs.append(build_clib.build_clib)

        # Setup the CCompiler object that we'll use to do all the
        # compiling and linking
        self.compiler = new_compiler(compiler=self.compiler,
                                     verbose=self.verbose,
                                     dry_run=self.dry_run,
                                     force=self.force)
        customize_compiler(self.compiler)
        # If we are cross-compiling, init the compiler now (if we are not
        # cross-compiling, init would not hurt, but people may rely on
        # late initialization of compiler even if they shouldn't...)
        if os.name == 'nt' and self.plat_name != get_platform():
            self.compiler.initialize(self.plat_name)

        # And make sure that any compile/link-related options (which might
        # come from the command-line or from the setup script) are set in
        # that CCompiler object -- that way, they automatically apply to
        # all compiling and linking done here.
        if self.include_dirs is not None:
            self.compiler.set_include_dirs(self.include_dirs)
        if self.define is not None:
            # 'define' option is a list of (name,value) tuples
            for (name, value) in self.define:
                self.compiler.define_macro(name, value)
        if self.undef is not None:
            for macro in self.undef:
                self.compiler.undefine_macro(macro)
        if self.libraries is not None:
            self.compiler.set_libraries(self.libraries)
        if self.library_dirs is not None:
            self.compiler.set_library_dirs(self.library_dirs)
        if self.rpath is not None:
            self.compiler.set_runtime_library_dirs(self.rpath)
        if self.link_objects is not None:
            self.compiler.set_link_objects(self.link_objects)

        # Now actually compile and link everything.
        self.build_extensions()

    def check_extensions_list(self, extensions):
        """Ensure that the list of extensions (presumably provided as a
        command option 'extensions') is valid, i.e. it is a list of
        Extension objects.  We also support the old-style list of 2-tuples,
        where the tuples are (ext_name, build_info), which are converted to
        Extension instances here.

        Raise DistutilsSetupError if the structure is invalid anywhere;
        just returns otherwise.
        """
        if not isinstance(extensions, list):
            raise DistutilsSetupError(
                  "'ext_modules' option must be a list of Extension instances")

        for i, ext in enumerate(extensions):
            if isinstance(ext, Extension):
                continue                # OK! (assume type-checking done
                                        # by Extension constructor)

            if not isinstance(ext, tuple) or len(ext) != 2:
                raise DistutilsSetupError(
                       "each element of 'ext_modules' option must be an "
                       "Extension instance or 2-tuple")

            ext_name, build_info = ext

            log.warn("old-style (ext_name, build_info) tuple found in "
                     "ext_modules for extension '%s' "
                     "-- please convert to Extension instance", ext_name)

            if not (isinstance(ext_name, str) and
                    extension_name_re.match(ext_name)):
                raise DistutilsSetupError(
                       "first element of each tuple in 'ext_modules' "
                       "must be the extension name (a string)")

            if not isinstance(build_info, dict):
                raise DistutilsSetupError(
                       "second element of each tuple in 'ext_modules' "
                       "must be a dictionary (build info)")

            # OK, the (ext_name, build_info) dict is type-safe: convert it
            # to an Extension instance.
            ext = Extension(ext_name, build_info['sources'])

            # Easy stuff: one-to-one mapping from dict elements to
            # instance attributes.
            for key in ('include_dirs', 'library_dirs', 'libraries',
                        'extra_objects', 'extra_compile_args',
                        'extra_link_args'):
                val = build_info.get(key)
                if val is not None:
                    setattr(ext, key, val)

            # Medium-easy stuff: same syntax/semantics, different names.
            ext.runtime_library_dirs = build_info.get('rpath')
            if 'def_file' in build_info:
                log.warn("'def_file' element of build info dict "
                         "no longer supported")

            # Non-trivial stuff: 'macros' split into 'define_macros'
            # and 'undef_macros'.
            macros = build_info.get('macros')
            if macros:
                ext.define_macros = []
                ext.undef_macros = []
                for macro in macros:
                    if not (isinstance(macro, tuple) and len(macro) in (1, 2)):
                        raise DistutilsSetupError(
                              "'macros' element of build info dict "
                              "must be 1- or 2-tuple")
                    if len(macro) == 1:
                        ext.undef_macros.append(macro[0])
                    elif len(macro) == 2:
                        ext.define_macros.append(macro)

            extensions[i] = ext

    def get_source_files(self):
        self.check_extensions_list(self.extensions)
        filenames = []

        # Wouldn't it be neat if we knew the names of header files too...
        for ext in self.extensions:
            filenames.extend(ext.sources)
        return filenames

    def get_outputs(self):
        # Sanity check the 'extensions' list -- can't assume this is being
        # done in the same run as a 'build_extensions()' call (in fact, we
        # can probably assume that it *isn't*!).
        self.check_extensions_list(self.extensions)

        # And build the list of output (built) filenames.  Note that this
        # ignores the 'inplace' flag, and assumes everything goes in the
        # "build" tree.
        outputs = []
        for ext in self.extensions:
            outputs.append(self.get_ext_fullpath(ext.name))
        return outputs

    def build_extensions(self):
        # First, sanity-check the 'extensions' list
        self.check_extensions_list(self.extensions)
        if self.parallel:
            self._build_extensions_parallel()
        else:
            self._build_extensions_serial()

    def _build_extensions_parallel(self):
        workers = self.parallel
        if self.parallel is True:
            workers = os.cpu_count()  # may return None
        try:
            from concurrent.futures import ThreadPoolExecutor
        except ImportError:
            workers = None

        if workers is None:
            self._build_extensions_serial()
            return

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(self.build_extension, ext)
                       for ext in self.extensions]
            for ext, fut in zip(self.extensions, futures):
                with self._filter_build_errors(ext):
                    fut.result()

    def _build_extensions_serial(self):
        for ext in self.extensions:
            with self._filter_build_errors(ext):
                self.build_extension(ext)

    @contextlib.contextmanager
    def _filter_build_errors(self, ext):
        try:
            yield
        except (CCompilerError, DistutilsError, CompileError) as e:
            if not ext.optional:
                raise
            self.warn('building extension "%s" failed: %s' %
                      (ext.name, e))

    def build_extension(self, ext):
        sources = ext.sources
        if sources is None or not isinstance(sources, (list, tuple)):
            raise DistutilsSetupError(
                  "in 'ext_modules' option (extension '%s'), "
                  "'sources' must be present and must be "
                  "a list of source filenames" % ext.name)
        # sort to make the resulting .so file build reproducible
        sources = sorted(sources)

        ext_path = self.get_ext_fullpath(ext.name)
        depends = sources + ext.depends
        if not (self.force or newer_group(depends, ext_path, 'newer')):
            log.debug("skipping '%s' extension (up-to-date)", ext.name)
            return
        else:
            log.info("building '%s' extension", ext.name)

        # First, scan the sources for SWIG definition files (.i), run
        # SWIG on 'em to create .c files, and modify the sources list
        # accordingly.
        sources = self.swig_sources(sources, ext)

        # Next, compile the source code to object files.

        # XXX not honouring 'define_macros' or 'undef_macros' -- the
        # CCompiler API needs to change to accommodate this, and I
        # want to do one thing at a time!

        # Two possible sources for extra compiler arguments:
        #   - 'extra_compile_args' in Extension object
        #   - CFLAGS environment variable (not particularly
        #     elegant, but people seem to expect it and I
        #     guess it's useful)
        # The environment variable should take precedence, and
        # any sensible compiler will give precedence to later
        # command line args.  Hence we combine them in order:
        extra_args = ext.extra_compile_args or []

        macros = ext.define_macros[:]
        for undef in ext.undef_macros:
            macros.append((undef,))

        objects = self.compiler.compile(sources,
                                         output_dir=self.build_temp,
                                         macros=macros,
                                         include_dirs=ext.include_dirs,
                                         debug=self.debug,
                                         extra_postargs=extra_args,
                                         depends=ext.depends)

        # XXX outdated variable, kept here in case third-part code
        # needs it.
        self._built_objects = objects[:]

        # Now link the object files together into a "shared object" --
        # of course, first we have to figure out all the other things
        # that go into the mix.
        if ext.extra_objects:
            objects.extend(ext.extra_objects)
        extra_args = ext.extra_link_args or []

        # Detect target language, if not provided
        language = ext.language or self.compiler.detect_language(sources)

        self.compiler.link_shared_object(
            objects, ext_path,
            libraries=self.get_libraries(ext),
            library_dirs=ext.library_dirs,
            runtime_library_dirs=ext.runtime_library_dirs,
            extra_postargs=extra_args,
            export_symbols=self.get_export_symbols(ext),
            debug=self.debug,
            build_temp=self.build_temp,
            target_lang=language)

    def swig_sources(self, sources, extension):
        """Walk the list of source files in 'sources', looking for SWIG
        interface (.i) files.  Run SWIG on all that are found, and
        return a modified 'sources' list with SWIG source files replaced
        by the generated C (or C++) files.
        """
        new_sources = []
        swig_sources = []
        swig_targets = {}

        # XXX this drops generated C/C++ files into the source tree, which
        # is fine for developers who want to distribute the generated
        # source -- but there should be an option to put SWIG output in
        # the temp dir.

        if self.swig_cpp:
            log.warn("--swig-cpp is deprecated - use --swig-opts=-c++")

        if self.swig_cpp or ('-c++' in self.swig_opts) or \
           ('-c++' in extension.swig_opts):
            target_ext = '.cpp'
        else:
            target_ext = '.c'

        for source in sources:
            (base, ext) = os.path.splitext(source)
            if ext == ".i":             # SWIG interface file
                new_sources.append(base + '_wrap' + target_ext)
                swig_sources.append(source)
                swig_targets[source] = new_sources[-1]
            else:
                new_sources.append(source)

        if not swig_sources:
            return new_sources

        swig = self.swig or self.find_swig()
        swig_cmd = [swig, "-python"]
        swig_cmd.extend(self.swig_opts)
        if self.swig_cpp:
            swig_cmd.append("-c++")

        # Do not override commandline arguments
        if not self.swig_opts:
            for o in extension.swig_opts:
                swig_cmd.append(o)

        for source in swig_sources:
            target = swig_targets[source]
            log.info("swigging %s to %s", source, target)
            self.spawn(swig_cmd + ["-o", target, source])

        return new_sources

    def find_swig(self):
        """Return the name of the SWIG executable.  On Unix, this is
        just "swig" -- it should be in the PATH.  Tries a bit harder on
        Windows.
        """
        if os.name == "posix":
            return "swig"
        elif os.name == "nt":
            # Look for SWIG in its standard installation directory on
            # Windows (or so I presume!).  If we find it there, great;
            # if not, act like Unix and assume it's in the PATH.
            for vers in ("1.3", "1.2", "1.1"):
                fn = os.path.join("c:\\swig%s" % vers, "swig.exe")
                if os.path.isfile(fn):
                    return fn
            else:
                return "swig.exe"
        else:
            raise DistutilsPlatformError(
                  "I don't know how to find (much less run) SWIG "
                  "on platform '%s'" % os.name)

    # -- Name generators -----------------------------------------------
    # (extension names, filenames, whatever)
    def get_ext_fullpath(self, ext_name):
        """Returns the path of the filename for a given extension.

        The file is located in `build_lib` or directly in the package
        (inplace option).
        """
        fullname = self.get_ext_fullname(ext_name)
        modpath = fullname.split('.')
        filename = self.get_ext_filename(modpath[-1])

        if not self.inplace:
            # no further work needed
            # returning :
            #   build_dir/package/path/filename
            filename = os.path.join(*modpath[:-1]+[filename])
            return os.path.join(self.build_lib, filename)

        # the inplace option requires to find the package directory
        # using the build_py command for that
        package = '.'.join(modpath[0:-1])
        build_py = self.get_finalized_command('build_py')
        package_dir = os.path.abspath(build_py.get_package_dir(package))

        # returning
        #   package_dir/filename
        return os.path.join(package_dir, filename)

    def get_ext_fullname(self, ext_name):
        """Returns the fullname of a given extension name.

        Adds the `package.` prefix"""
        if self.package is None:
            return ext_name
        else:
            return self.package + '.' + ext_name

    def get_ext_filename(self, ext_name):
        r"""Convert the name of an extension (eg. "foo.bar") into the name
        of the file from which it will be loaded (eg. "foo/bar.so", or
        "foo\bar.pyd").
        """
        from distutils.sysconfig import get_config_var
        ext_path = ext_name.split('.')
        ext_suffix = get_config_var('EXT_SUFFIX')
        return os.path.join(*ext_path) + ext_suffix

    def get_export_symbols(self, ext):
        """Return the list of symbols that a shared extension has to
        export.  This either uses 'ext.export_symbols' or, if it's not
        provided, "PyInit_" + module_name.  Only relevant on Windows, where
        the .pyd file (DLL) must export the module "PyInit_" function.
        """
        name = ext.name.split('.')[-1]
        try:
            # Unicode module name support as defined in PEP-489
            # https://www.python.org/dev/peps/pep-0489/#export-hook-name
            name.encode('ascii')
        except UnicodeEncodeError:
            suffix = 'U_' + name.encode('punycode').replace(b'-', b'_').decode('ascii')
        else:
            suffix = "_" + name

        initfunc_name = "PyInit" + suffix
        if initfunc_name not in ext.export_symbols:
            ext.export_symbols.append(initfunc_name)
        return ext.export_symbols

    def get_libraries(self, ext):
        """Return the list of libraries to link against when building a
        shared extension.  On most platforms, this is just 'ext.libraries';
        on Windows, we add the Python library (eg. python20.dll).
        """
        # The python library is always needed on Windows.  For MSVC, this
        # is redundant, since the library is mentioned in a pragma in
        # pyconfig.h that MSVC groks.  The other Windows compilers all seem
        # to need it mentioned explicitly, though, so that's what we do.
        # Append '_d' to the python import library on debug builds.
        if sys.platform == "win32":
            from distutils._msvccompiler import MSVCCompiler
            if not isinstance(self.compiler, MSVCCompiler):
                template = "python%d%d"
                if self.debug:
                    template = template + '_d'
                pythonlib = (template %
                       (sys.hexversion >> 24, (sys.hexversion >> 16) & 0xff))
                # don't extend ext.libraries, it may be shared with other
                # extensions, it is a reference to the original list
                return ext.libraries + [pythonlib]
        else:
            # On Android only the main executable and LD_PRELOADs are considered
            # to be RTLD_GLOBAL, all the dependencies of the main executable
            # remain RTLD_LOCAL and so the shared libraries must be linked with
            # libpython when python is built with a shared python library (issue
            # bpo-21536).
            # On Cygwin (and if required, other POSIX-like platforms based on
            # Windows like MinGW) it is simply necessary that all symbols in
            # shared libraries are resolved at link time.
            from distutils.sysconfig import get_config_var
            link_libpython = False
            if get_config_var('Py_ENABLE_SHARED'):
                # A native build on an Android device or on Cygwin
                if hasattr(sys, 'getandroidapilevel'):
                    link_libpython = True
                elif sys.platform == 'cygwin':
                    link_libpython = True
                elif '_PYTHON_HOST_PLATFORM' in os.environ:
                    # We are cross-compiling for one of the relevant platforms
                    if get_config_var('ANDROID_API_LEVEL') != 0:
                        link_libpython = True
                    elif get_config_var('MACHDEP') == 'cygwin':
                        link_libpython = True

            if link_libpython:
                ldversion = get_config_var('LDVERSION')
                return ext.libraries + ['python' + ldversion]

        return ext.libraries + py37compat.pythonlib()

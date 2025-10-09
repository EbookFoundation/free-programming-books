import os
import sys
import itertools
from importlib.machinery import EXTENSION_SUFFIXES
from distutils.command.build_ext import build_ext as _du_build_ext
from distutils.file_util import copy_file
from distutils.ccompiler import new_compiler
from distutils.sysconfig import customize_compiler, get_config_var
from distutils.errors import DistutilsError
from distutils import log

from setuptools.extension import Library

try:
    # Attempt to use Cython for building extensions, if available
    from Cython.Distutils.build_ext import build_ext as _build_ext
    # Additionally, assert that the compiler module will load
    # also. Ref #1229.
    __import__('Cython.Compiler.Main')
except ImportError:
    _build_ext = _du_build_ext

# make sure _config_vars is initialized
get_config_var("LDSHARED")
from distutils.sysconfig import _config_vars as _CONFIG_VARS  # noqa


def _customize_compiler_for_shlib(compiler):
    if sys.platform == "darwin":
        # building .dylib requires additional compiler flags on OSX; here we
        # temporarily substitute the pyconfig.h variables so that distutils'
        # 'customize_compiler' uses them before we build the shared libraries.
        tmp = _CONFIG_VARS.copy()
        try:
            # XXX Help!  I don't have any idea whether these are right...
            _CONFIG_VARS['LDSHARED'] = (
                "gcc -Wl,-x -dynamiclib -undefined dynamic_lookup")
            _CONFIG_VARS['CCSHARED'] = " -dynamiclib"
            _CONFIG_VARS['SO'] = ".dylib"
            customize_compiler(compiler)
        finally:
            _CONFIG_VARS.clear()
            _CONFIG_VARS.update(tmp)
    else:
        customize_compiler(compiler)


have_rtld = False
use_stubs = False
libtype = 'shared'

if sys.platform == "darwin":
    use_stubs = True
elif os.name != 'nt':
    try:
        import dl
        use_stubs = have_rtld = hasattr(dl, 'RTLD_NOW')
    except ImportError:
        pass


def if_dl(s):
    return s if have_rtld else ''


def get_abi3_suffix():
    """Return the file extension for an abi3-compliant Extension()"""
    for suffix in EXTENSION_SUFFIXES:
        if '.abi3' in suffix:  # Unix
            return suffix
        elif suffix == '.pyd':  # Windows
            return suffix


class build_ext(_build_ext):
    def run(self):
        """Build extensions in build directory, then copy if --inplace"""
        old_inplace, self.inplace = self.inplace, 0
        _build_ext.run(self)
        self.inplace = old_inplace
        if old_inplace:
            self.copy_extensions_to_source()

    def copy_extensions_to_source(self):
        build_py = self.get_finalized_command('build_py')
        for ext in self.extensions:
            fullname = self.get_ext_fullname(ext.name)
            filename = self.get_ext_filename(fullname)
            modpath = fullname.split('.')
            package = '.'.join(modpath[:-1])
            package_dir = build_py.get_package_dir(package)
            dest_filename = os.path.join(package_dir,
                                         os.path.basename(filename))
            src_filename = os.path.join(self.build_lib, filename)

            # Always copy, even if source is older than destination, to ensure
            # that the right extensions for the current Python/platform are
            # used.
            copy_file(
                src_filename, dest_filename, verbose=self.verbose,
                dry_run=self.dry_run
            )
            if ext._needs_stub:
                self.write_stub(package_dir or os.curdir, ext, True)

    def get_ext_filename(self, fullname):
        so_ext = os.getenv('SETUPTOOLS_EXT_SUFFIX')
        if so_ext:
            filename = os.path.join(*fullname.split('.')) + so_ext
        else:
            filename = _build_ext.get_ext_filename(self, fullname)
            so_ext = get_config_var('EXT_SUFFIX')

        if fullname in self.ext_map:
            ext = self.ext_map[fullname]
            use_abi3 = getattr(ext, 'py_limited_api') and get_abi3_suffix()
            if use_abi3:
                filename = filename[:-len(so_ext)]
                so_ext = get_abi3_suffix()
                filename = filename + so_ext
            if isinstance(ext, Library):
                fn, ext = os.path.splitext(filename)
                return self.shlib_compiler.library_filename(fn, libtype)
            elif use_stubs and ext._links_to_dynamic:
                d, fn = os.path.split(filename)
                return os.path.join(d, 'dl-' + fn)
        return filename

    def initialize_options(self):
        _build_ext.initialize_options(self)
        self.shlib_compiler = None
        self.shlibs = []
        self.ext_map = {}

    def finalize_options(self):
        _build_ext.finalize_options(self)
        self.extensions = self.extensions or []
        self.check_extensions_list(self.extensions)
        self.shlibs = [ext for ext in self.extensions
                       if isinstance(ext, Library)]
        if self.shlibs:
            self.setup_shlib_compiler()
        for ext in self.extensions:
            ext._full_name = self.get_ext_fullname(ext.name)
        for ext in self.extensions:
            fullname = ext._full_name
            self.ext_map[fullname] = ext

            # distutils 3.1 will also ask for module names
            # XXX what to do with conflicts?
            self.ext_map[fullname.split('.')[-1]] = ext

            ltd = self.shlibs and self.links_to_dynamic(ext) or False
            ns = ltd and use_stubs and not isinstance(ext, Library)
            ext._links_to_dynamic = ltd
            ext._needs_stub = ns
            filename = ext._file_name = self.get_ext_filename(fullname)
            libdir = os.path.dirname(os.path.join(self.build_lib, filename))
            if ltd and libdir not in ext.library_dirs:
                ext.library_dirs.append(libdir)
            if ltd and use_stubs and os.curdir not in ext.runtime_library_dirs:
                ext.runtime_library_dirs.append(os.curdir)

    def setup_shlib_compiler(self):
        compiler = self.shlib_compiler = new_compiler(
            compiler=self.compiler, dry_run=self.dry_run, force=self.force
        )
        _customize_compiler_for_shlib(compiler)

        if self.include_dirs is not None:
            compiler.set_include_dirs(self.include_dirs)
        if self.define is not None:
            # 'define' option is a list of (name,value) tuples
            for (name, value) in self.define:
                compiler.define_macro(name, value)
        if self.undef is not None:
            for macro in self.undef:
                compiler.undefine_macro(macro)
        if self.libraries is not None:
            compiler.set_libraries(self.libraries)
        if self.library_dirs is not None:
            compiler.set_library_dirs(self.library_dirs)
        if self.rpath is not None:
            compiler.set_runtime_library_dirs(self.rpath)
        if self.link_objects is not None:
            compiler.set_link_objects(self.link_objects)

        # hack so distutils' build_extension() builds a library instead
        compiler.link_shared_object = link_shared_object.__get__(compiler)

    def get_export_symbols(self, ext):
        if isinstance(ext, Library):
            return ext.export_symbols
        return _build_ext.get_export_symbols(self, ext)

    def build_extension(self, ext):
        ext._convert_pyx_sources_to_lang()
        _compiler = self.compiler
        try:
            if isinstance(ext, Library):
                self.compiler = self.shlib_compiler
            _build_ext.build_extension(self, ext)
            if ext._needs_stub:
                cmd = self.get_finalized_command('build_py').build_lib
                self.write_stub(cmd, ext)
        finally:
            self.compiler = _compiler

    def links_to_dynamic(self, ext):
        """Return true if 'ext' links to a dynamic lib in the same package"""
        # XXX this should check to ensure the lib is actually being built
        # XXX as dynamic, and not just using a locally-found version or a
        # XXX static-compiled version
        libnames = dict.fromkeys([lib._full_name for lib in self.shlibs])
        pkg = '.'.join(ext._full_name.split('.')[:-1] + [''])
        return any(pkg + libname in libnames for libname in ext.libraries)

    def get_outputs(self):
        return _build_ext.get_outputs(self) + self.__get_stubs_outputs()

    def __get_stubs_outputs(self):
        # assemble the base name for each extension that needs a stub
        ns_ext_bases = (
            os.path.join(self.build_lib, *ext._full_name.split('.'))
            for ext in self.extensions
            if ext._needs_stub
        )
        # pair each base with the extension
        pairs = itertools.product(ns_ext_bases, self.__get_output_extensions())
        return list(base + fnext for base, fnext in pairs)

    def __get_output_extensions(self):
        yield '.py'
        yield '.pyc'
        if self.get_finalized_command('build_py').optimize:
            yield '.pyo'

    def write_stub(self, output_dir, ext, compile=False):
        log.info("writing stub loader for %s to %s", ext._full_name,
                 output_dir)
        stub_file = (os.path.join(output_dir, *ext._full_name.split('.')) +
                     '.py')
        if compile and os.path.exists(stub_file):
            raise DistutilsError(stub_file + " already exists! Please delete.")
        if not self.dry_run:
            f = open(stub_file, 'w')
            f.write(
                '\n'.join([
                    "def __bootstrap__():",
                    "   global __bootstrap__, __file__, __loader__",
                    "   import sys, os, pkg_resources, importlib.util" +
                    if_dl(", dl"),
                    "   __file__ = pkg_resources.resource_filename"
                    "(__name__,%r)"
                    % os.path.basename(ext._file_name),
                    "   del __bootstrap__",
                    "   if '__loader__' in globals():",
                    "       del __loader__",
                    if_dl("   old_flags = sys.getdlopenflags()"),
                    "   old_dir = os.getcwd()",
                    "   try:",
                    "     os.chdir(os.path.dirname(__file__))",
                    if_dl("     sys.setdlopenflags(dl.RTLD_NOW)"),
                    "     spec = importlib.util.spec_from_file_location(",
                    "                __name__, __file__)",
                    "     mod = importlib.util.module_from_spec(spec)",
                    "     spec.loader.exec_module(mod)",
                    "   finally:",
                    if_dl("     sys.setdlopenflags(old_flags)"),
                    "     os.chdir(old_dir)",
                    "__bootstrap__()",
                    ""  # terminal \n
                ])
            )
            f.close()
        if compile:
            from distutils.util import byte_compile

            byte_compile([stub_file], optimize=0,
                         force=True, dry_run=self.dry_run)
            optimize = self.get_finalized_command('install_lib').optimize
            if optimize > 0:
                byte_compile([stub_file], optimize=optimize,
                             force=True, dry_run=self.dry_run)
            if os.path.exists(stub_file) and not self.dry_run:
                os.unlink(stub_file)


if use_stubs or os.name == 'nt':
    # Build shared libraries
    #
    def link_shared_object(
            self, objects, output_libname, output_dir=None, libraries=None,
            library_dirs=None, runtime_library_dirs=None, export_symbols=None,
            debug=0, extra_preargs=None, extra_postargs=None, build_temp=None,
            target_lang=None):
        self.link(
            self.SHARED_LIBRARY, objects, output_libname,
            output_dir, libraries, library_dirs, runtime_library_dirs,
            export_symbols, debug, extra_preargs, extra_postargs,
            build_temp, target_lang
        )
else:
    # Build static libraries everywhere else
    libtype = 'static'

    def link_shared_object(
            self, objects, output_libname, output_dir=None, libraries=None,
            library_dirs=None, runtime_library_dirs=None, export_symbols=None,
            debug=0, extra_preargs=None, extra_postargs=None, build_temp=None,
            target_lang=None):
        # XXX we need to either disallow these attrs on Library instances,
        # or warn/abort here if set, or something...
        # libraries=None, library_dirs=None, runtime_library_dirs=None,
        # export_symbols=None, extra_preargs=None, extra_postargs=None,
        # build_temp=None

        assert output_dir is None  # distutils build_ext doesn't pass this
        output_dir, filename = os.path.split(output_libname)
        basename, ext = os.path.splitext(filename)
        if self.library_filename("x").startswith('lib'):
            # strip 'lib' prefix; this is kludgy if some platform uses
            # a different prefix
            basename = basename[3:]

        self.create_static_lib(
            objects, basename, output_dir, debug, target_lang
        )

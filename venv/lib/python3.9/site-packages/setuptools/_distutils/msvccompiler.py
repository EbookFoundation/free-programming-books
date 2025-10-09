"""distutils.msvccompiler

Contains MSVCCompiler, an implementation of the abstract CCompiler class
for the Microsoft Visual Studio.
"""

# Written by Perry Stoll
# hacked by Robin Becker and Thomas Heller to do a better job of
#   finding DevStudio (through the registry)

import sys, os
from distutils.errors import \
     DistutilsExecError, DistutilsPlatformError, \
     CompileError, LibError, LinkError
from distutils.ccompiler import \
     CCompiler, gen_lib_options
from distutils import log

_can_read_reg = False
try:
    import winreg

    _can_read_reg = True
    hkey_mod = winreg

    RegOpenKeyEx = winreg.OpenKeyEx
    RegEnumKey = winreg.EnumKey
    RegEnumValue = winreg.EnumValue
    RegError = winreg.error

except ImportError:
    try:
        import win32api
        import win32con
        _can_read_reg = True
        hkey_mod = win32con

        RegOpenKeyEx = win32api.RegOpenKeyEx
        RegEnumKey = win32api.RegEnumKey
        RegEnumValue = win32api.RegEnumValue
        RegError = win32api.error
    except ImportError:
        log.info("Warning: Can't read registry to find the "
                 "necessary compiler setting\n"
                 "Make sure that Python modules winreg, "
                 "win32api or win32con are installed.")
        pass

if _can_read_reg:
    HKEYS = (hkey_mod.HKEY_USERS,
             hkey_mod.HKEY_CURRENT_USER,
             hkey_mod.HKEY_LOCAL_MACHINE,
             hkey_mod.HKEY_CLASSES_ROOT)

def read_keys(base, key):
    """Return list of registry keys."""
    try:
        handle = RegOpenKeyEx(base, key)
    except RegError:
        return None
    L = []
    i = 0
    while True:
        try:
            k = RegEnumKey(handle, i)
        except RegError:
            break
        L.append(k)
        i += 1
    return L

def read_values(base, key):
    """Return dict of registry keys and values.

    All names are converted to lowercase.
    """
    try:
        handle = RegOpenKeyEx(base, key)
    except RegError:
        return None
    d = {}
    i = 0
    while True:
        try:
            name, value, type = RegEnumValue(handle, i)
        except RegError:
            break
        name = name.lower()
        d[convert_mbcs(name)] = convert_mbcs(value)
        i += 1
    return d

def convert_mbcs(s):
    dec = getattr(s, "decode", None)
    if dec is not None:
        try:
            s = dec("mbcs")
        except UnicodeError:
            pass
    return s

class MacroExpander:
    def __init__(self, version):
        self.macros = {}
        self.load_macros(version)

    def set_macro(self, macro, path, key):
        for base in HKEYS:
            d = read_values(base, path)
            if d:
                self.macros["$(%s)" % macro] = d[key]
                break

    def load_macros(self, version):
        vsbase = r"Software\Microsoft\VisualStudio\%0.1f" % version
        self.set_macro("VCInstallDir", vsbase + r"\Setup\VC", "productdir")
        self.set_macro("VSInstallDir", vsbase + r"\Setup\VS", "productdir")
        net = r"Software\Microsoft\.NETFramework"
        self.set_macro("FrameworkDir", net, "installroot")
        try:
            if version > 7.0:
                self.set_macro("FrameworkSDKDir", net, "sdkinstallrootv1.1")
            else:
                self.set_macro("FrameworkSDKDir", net, "sdkinstallroot")
        except KeyError as exc: #
            raise DistutilsPlatformError(
            """Python was built with Visual Studio 2003;
extensions must be built with a compiler than can generate compatible binaries.
Visual Studio 2003 was not found on this system. If you have Cygwin installed,
you can try compiling with MingW32, by passing "-c mingw32" to setup.py.""")

        p = r"Software\Microsoft\NET Framework Setup\Product"
        for base in HKEYS:
            try:
                h = RegOpenKeyEx(base, p)
            except RegError:
                continue
            key = RegEnumKey(h, 0)
            d = read_values(base, r"%s\%s" % (p, key))
            self.macros["$(FrameworkVersion)"] = d["version"]

    def sub(self, s):
        for k, v in self.macros.items():
            s = s.replace(k, v)
        return s

def get_build_version():
    """Return the version of MSVC that was used to build Python.

    For Python 2.3 and up, the version number is included in
    sys.version.  For earlier versions, assume the compiler is MSVC 6.
    """
    prefix = "MSC v."
    i = sys.version.find(prefix)
    if i == -1:
        return 6
    i = i + len(prefix)
    s, rest = sys.version[i:].split(" ", 1)
    majorVersion = int(s[:-2]) - 6
    if majorVersion >= 13:
        # v13 was skipped and should be v14
        majorVersion += 1
    minorVersion = int(s[2:3]) / 10.0
    # I don't think paths are affected by minor version in version 6
    if majorVersion == 6:
        minorVersion = 0
    if majorVersion >= 6:
        return majorVersion + minorVersion
    # else we don't know what version of the compiler this is
    return None

def get_build_architecture():
    """Return the processor architecture.

    Possible results are "Intel" or "AMD64".
    """

    prefix = " bit ("
    i = sys.version.find(prefix)
    if i == -1:
        return "Intel"
    j = sys.version.find(")", i)
    return sys.version[i+len(prefix):j]

def normalize_and_reduce_paths(paths):
    """Return a list of normalized paths with duplicates removed.

    The current order of paths is maintained.
    """
    # Paths are normalized so things like:  /a and /a/ aren't both preserved.
    reduced_paths = []
    for p in paths:
        np = os.path.normpath(p)
        # XXX(nnorwitz): O(n**2), if reduced_paths gets long perhaps use a set.
        if np not in reduced_paths:
            reduced_paths.append(np)
    return reduced_paths


class MSVCCompiler(CCompiler) :
    """Concrete class that implements an interface to Microsoft Visual C++,
       as defined by the CCompiler abstract class."""

    compiler_type = 'msvc'

    # Just set this so CCompiler's constructor doesn't barf.  We currently
    # don't use the 'set_executables()' bureaucracy provided by CCompiler,
    # as it really isn't necessary for this sort of single-compiler class.
    # Would be nice to have a consistent interface with UnixCCompiler,
    # though, so it's worth thinking about.
    executables = {}

    # Private class data (need to distinguish C from C++ source for compiler)
    _c_extensions = ['.c']
    _cpp_extensions = ['.cc', '.cpp', '.cxx']
    _rc_extensions = ['.rc']
    _mc_extensions = ['.mc']

    # Needed for the filename generation methods provided by the
    # base class, CCompiler.
    src_extensions = (_c_extensions + _cpp_extensions +
                      _rc_extensions + _mc_extensions)
    res_extension = '.res'
    obj_extension = '.obj'
    static_lib_extension = '.lib'
    shared_lib_extension = '.dll'
    static_lib_format = shared_lib_format = '%s%s'
    exe_extension = '.exe'

    def __init__(self, verbose=0, dry_run=0, force=0):
        CCompiler.__init__ (self, verbose, dry_run, force)
        self.__version = get_build_version()
        self.__arch = get_build_architecture()
        if self.__arch == "Intel":
            # x86
            if self.__version >= 7:
                self.__root = r"Software\Microsoft\VisualStudio"
                self.__macros = MacroExpander(self.__version)
            else:
                self.__root = r"Software\Microsoft\Devstudio"
            self.__product = "Visual Studio version %s" % self.__version
        else:
            # Win64. Assume this was built with the platform SDK
            self.__product = "Microsoft SDK compiler %s" % (self.__version + 6)

        self.initialized = False

    def initialize(self):
        self.__paths = []
        if "DISTUTILS_USE_SDK" in os.environ and "MSSdk" in os.environ and self.find_exe("cl.exe"):
            # Assume that the SDK set up everything alright; don't try to be
            # smarter
            self.cc = "cl.exe"
            self.linker = "link.exe"
            self.lib = "lib.exe"
            self.rc = "rc.exe"
            self.mc = "mc.exe"
        else:
            self.__paths = self.get_msvc_paths("path")

            if len(self.__paths) == 0:
                raise DistutilsPlatformError("Python was built with %s, "
                       "and extensions need to be built with the same "
                       "version of the compiler, but it isn't installed."
                       % self.__product)

            self.cc = self.find_exe("cl.exe")
            self.linker = self.find_exe("link.exe")
            self.lib = self.find_exe("lib.exe")
            self.rc = self.find_exe("rc.exe")   # resource compiler
            self.mc = self.find_exe("mc.exe")   # message compiler
            self.set_path_env_var('lib')
            self.set_path_env_var('include')

        # extend the MSVC path with the current path
        try:
            for p in os.environ['path'].split(';'):
                self.__paths.append(p)
        except KeyError:
            pass
        self.__paths = normalize_and_reduce_paths(self.__paths)
        os.environ['path'] = ";".join(self.__paths)

        self.preprocess_options = None
        if self.__arch == "Intel":
            self.compile_options = [ '/nologo', '/O2', '/MD', '/W3', '/GX' ,
                                     '/DNDEBUG']
            self.compile_options_debug = ['/nologo', '/Od', '/MDd', '/W3', '/GX',
                                          '/Z7', '/D_DEBUG']
        else:
            # Win64
            self.compile_options = [ '/nologo', '/O2', '/MD', '/W3', '/GS-' ,
                                     '/DNDEBUG']
            self.compile_options_debug = ['/nologo', '/Od', '/MDd', '/W3', '/GS-',
                                          '/Z7', '/D_DEBUG']

        self.ldflags_shared = ['/DLL', '/nologo', '/INCREMENTAL:NO']
        if self.__version >= 7:
            self.ldflags_shared_debug = [
                '/DLL', '/nologo', '/INCREMENTAL:no', '/DEBUG'
                ]
        else:
            self.ldflags_shared_debug = [
                '/DLL', '/nologo', '/INCREMENTAL:no', '/pdb:None', '/DEBUG'
                ]
        self.ldflags_static = [ '/nologo']

        self.initialized = True

    # -- Worker methods ------------------------------------------------

    def object_filenames(self,
                         source_filenames,
                         strip_dir=0,
                         output_dir=''):
        # Copied from ccompiler.py, extended to return .res as 'object'-file
        # for .rc input file
        if output_dir is None: output_dir = ''
        obj_names = []
        for src_name in source_filenames:
            (base, ext) = os.path.splitext (src_name)
            base = os.path.splitdrive(base)[1] # Chop off the drive
            base = base[os.path.isabs(base):]  # If abs, chop off leading /
            if ext not in self.src_extensions:
                # Better to raise an exception instead of silently continuing
                # and later complain about sources and targets having
                # different lengths
                raise CompileError ("Don't know how to compile %s" % src_name)
            if strip_dir:
                base = os.path.basename (base)
            if ext in self._rc_extensions:
                obj_names.append (os.path.join (output_dir,
                                                base + self.res_extension))
            elif ext in self._mc_extensions:
                obj_names.append (os.path.join (output_dir,
                                                base + self.res_extension))
            else:
                obj_names.append (os.path.join (output_dir,
                                                base + self.obj_extension))
        return obj_names


    def compile(self, sources,
                output_dir=None, macros=None, include_dirs=None, debug=0,
                extra_preargs=None, extra_postargs=None, depends=None):

        if not self.initialized:
            self.initialize()
        compile_info = self._setup_compile(output_dir, macros, include_dirs,
                                           sources, depends, extra_postargs)
        macros, objects, extra_postargs, pp_opts, build = compile_info

        compile_opts = extra_preargs or []
        compile_opts.append ('/c')
        if debug:
            compile_opts.extend(self.compile_options_debug)
        else:
            compile_opts.extend(self.compile_options)

        for obj in objects:
            try:
                src, ext = build[obj]
            except KeyError:
                continue
            if debug:
                # pass the full pathname to MSVC in debug mode,
                # this allows the debugger to find the source file
                # without asking the user to browse for it
                src = os.path.abspath(src)

            if ext in self._c_extensions:
                input_opt = "/Tc" + src
            elif ext in self._cpp_extensions:
                input_opt = "/Tp" + src
            elif ext in self._rc_extensions:
                # compile .RC to .RES file
                input_opt = src
                output_opt = "/fo" + obj
                try:
                    self.spawn([self.rc] + pp_opts +
                               [output_opt] + [input_opt])
                except DistutilsExecError as msg:
                    raise CompileError(msg)
                continue
            elif ext in self._mc_extensions:
                # Compile .MC to .RC file to .RES file.
                #   * '-h dir' specifies the directory for the
                #     generated include file
                #   * '-r dir' specifies the target directory of the
                #     generated RC file and the binary message resource
                #     it includes
                #
                # For now (since there are no options to change this),
                # we use the source-directory for the include file and
                # the build directory for the RC file and message
                # resources. This works at least for win32all.
                h_dir = os.path.dirname(src)
                rc_dir = os.path.dirname(obj)
                try:
                    # first compile .MC to .RC and .H file
                    self.spawn([self.mc] +
                               ['-h', h_dir, '-r', rc_dir] + [src])
                    base, _ = os.path.splitext (os.path.basename (src))
                    rc_file = os.path.join (rc_dir, base + '.rc')
                    # then compile .RC to .RES file
                    self.spawn([self.rc] +
                               ["/fo" + obj] + [rc_file])

                except DistutilsExecError as msg:
                    raise CompileError(msg)
                continue
            else:
                # how to handle this file?
                raise CompileError("Don't know how to compile %s to %s"
                                   % (src, obj))

            output_opt = "/Fo" + obj
            try:
                self.spawn([self.cc] + compile_opts + pp_opts +
                           [input_opt, output_opt] +
                           extra_postargs)
            except DistutilsExecError as msg:
                raise CompileError(msg)

        return objects


    def create_static_lib(self,
                          objects,
                          output_libname,
                          output_dir=None,
                          debug=0,
                          target_lang=None):

        if not self.initialized:
            self.initialize()
        (objects, output_dir) = self._fix_object_args(objects, output_dir)
        output_filename = self.library_filename(output_libname,
                                                output_dir=output_dir)

        if self._need_link(objects, output_filename):
            lib_args = objects + ['/OUT:' + output_filename]
            if debug:
                pass # XXX what goes here?
            try:
                self.spawn([self.lib] + lib_args)
            except DistutilsExecError as msg:
                raise LibError(msg)
        else:
            log.debug("skipping %s (up-to-date)", output_filename)


    def link(self,
             target_desc,
             objects,
             output_filename,
             output_dir=None,
             libraries=None,
             library_dirs=None,
             runtime_library_dirs=None,
             export_symbols=None,
             debug=0,
             extra_preargs=None,
             extra_postargs=None,
             build_temp=None,
             target_lang=None):

        if not self.initialized:
            self.initialize()
        (objects, output_dir) = self._fix_object_args(objects, output_dir)
        fixed_args = self._fix_lib_args(libraries, library_dirs,
                                        runtime_library_dirs)
        (libraries, library_dirs, runtime_library_dirs) = fixed_args

        if runtime_library_dirs:
            self.warn ("I don't know what to do with 'runtime_library_dirs': "
                       + str (runtime_library_dirs))

        lib_opts = gen_lib_options(self,
                                   library_dirs, runtime_library_dirs,
                                   libraries)
        if output_dir is not None:
            output_filename = os.path.join(output_dir, output_filename)

        if self._need_link(objects, output_filename):
            if target_desc == CCompiler.EXECUTABLE:
                if debug:
                    ldflags = self.ldflags_shared_debug[1:]
                else:
                    ldflags = self.ldflags_shared[1:]
            else:
                if debug:
                    ldflags = self.ldflags_shared_debug
                else:
                    ldflags = self.ldflags_shared

            export_opts = []
            for sym in (export_symbols or []):
                export_opts.append("/EXPORT:" + sym)

            ld_args = (ldflags + lib_opts + export_opts +
                       objects + ['/OUT:' + output_filename])

            # The MSVC linker generates .lib and .exp files, which cannot be
            # suppressed by any linker switches. The .lib files may even be
            # needed! Make sure they are generated in the temporary build
            # directory. Since they have different names for debug and release
            # builds, they can go into the same directory.
            if export_symbols is not None:
                (dll_name, dll_ext) = os.path.splitext(
                    os.path.basename(output_filename))
                implib_file = os.path.join(
                    os.path.dirname(objects[0]),
                    self.library_filename(dll_name))
                ld_args.append ('/IMPLIB:' + implib_file)

            if extra_preargs:
                ld_args[:0] = extra_preargs
            if extra_postargs:
                ld_args.extend(extra_postargs)

            self.mkpath(os.path.dirname(output_filename))
            try:
                self.spawn([self.linker] + ld_args)
            except DistutilsExecError as msg:
                raise LinkError(msg)

        else:
            log.debug("skipping %s (up-to-date)", output_filename)


    # -- Miscellaneous methods -----------------------------------------
    # These are all used by the 'gen_lib_options() function, in
    # ccompiler.py.

    def library_dir_option(self, dir):
        return "/LIBPATH:" + dir

    def runtime_library_dir_option(self, dir):
        raise DistutilsPlatformError(
              "don't know how to set runtime library search path for MSVC++")

    def library_option(self, lib):
        return self.library_filename(lib)


    def find_library_file(self, dirs, lib, debug=0):
        # Prefer a debugging library if found (and requested), but deal
        # with it if we don't have one.
        if debug:
            try_names = [lib + "_d", lib]
        else:
            try_names = [lib]
        for dir in dirs:
            for name in try_names:
                libfile = os.path.join(dir, self.library_filename (name))
                if os.path.exists(libfile):
                    return libfile
        else:
            # Oops, didn't find it in *any* of 'dirs'
            return None

    # Helper methods for using the MSVC registry settings

    def find_exe(self, exe):
        """Return path to an MSVC executable program.

        Tries to find the program in several places: first, one of the
        MSVC program search paths from the registry; next, the directories
        in the PATH environment variable.  If any of those work, return an
        absolute path that is known to exist.  If none of them work, just
        return the original program name, 'exe'.
        """
        for p in self.__paths:
            fn = os.path.join(os.path.abspath(p), exe)
            if os.path.isfile(fn):
                return fn

        # didn't find it; try existing path
        for p in os.environ['Path'].split(';'):
            fn = os.path.join(os.path.abspath(p),exe)
            if os.path.isfile(fn):
                return fn

        return exe

    def get_msvc_paths(self, path, platform='x86'):
        """Get a list of devstudio directories (include, lib or path).

        Return a list of strings.  The list will be empty if unable to
        access the registry or appropriate registry keys not found.
        """
        if not _can_read_reg:
            return []

        path = path + " dirs"
        if self.__version >= 7:
            key = (r"%s\%0.1f\VC\VC_OBJECTS_PLATFORM_INFO\Win32\Directories"
                   % (self.__root, self.__version))
        else:
            key = (r"%s\6.0\Build System\Components\Platforms"
                   r"\Win32 (%s)\Directories" % (self.__root, platform))

        for base in HKEYS:
            d = read_values(base, key)
            if d:
                if self.__version >= 7:
                    return self.__macros.sub(d[path]).split(";")
                else:
                    return d[path].split(";")
        # MSVC 6 seems to create the registry entries we need only when
        # the GUI is run.
        if self.__version == 6:
            for base in HKEYS:
                if read_values(base, r"%s\6.0" % self.__root) is not None:
                    self.warn("It seems you have Visual Studio 6 installed, "
                        "but the expected registry settings are not present.\n"
                        "You must at least run the Visual Studio GUI once "
                        "so that these entries are created.")
                    break
        return []

    def set_path_env_var(self, name):
        """Set environment variable 'name' to an MSVC path type value.

        This is equivalent to a SET command prior to execution of spawned
        commands.
        """

        if name == "lib":
            p = self.get_msvc_paths("library")
        else:
            p = self.get_msvc_paths(name)
        if p:
            os.environ[name] = ';'.join(p)


if get_build_version() >= 8.0:
    log.debug("Importing new compiler from distutils.msvc9compiler")
    OldMSVCCompiler = MSVCCompiler
    from distutils.msvc9compiler import MSVCCompiler
    # get_build_architecture not really relevant now we support cross-compile
    from distutils.msvc9compiler import MacroExpander

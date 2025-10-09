"""distutils.unixccompiler

Contains the UnixCCompiler class, a subclass of CCompiler that handles
the "typical" Unix-style command-line C compiler:
  * macros defined with -Dname[=value]
  * macros undefined with -Uname
  * include search directories specified with -Idir
  * libraries specified with -lllib
  * library search directories specified with -Ldir
  * compile handled by 'cc' (or similar) executable with -c option:
    compiles .c to .o
  * link static library handled by 'ar' command (possibly with 'ranlib')
  * link shared library handled by 'cc -shared'
"""

import os, sys, re

from distutils import sysconfig
from distutils.dep_util import newer
from distutils.ccompiler import \
     CCompiler, gen_preprocess_options, gen_lib_options
from distutils.errors import \
     DistutilsExecError, CompileError, LibError, LinkError
from distutils import log

if sys.platform == 'darwin':
    import _osx_support

# XXX Things not currently handled:
#   * optimization/debug/warning flags; we just use whatever's in Python's
#     Makefile and live with it.  Is this adequate?  If not, we might
#     have to have a bunch of subclasses GNUCCompiler, SGICCompiler,
#     SunCCompiler, and I suspect down that road lies madness.
#   * even if we don't know a warning flag from an optimization flag,
#     we need some way for outsiders to feed preprocessor/compiler/linker
#     flags in to us -- eg. a sysadmin might want to mandate certain flags
#     via a site config file, or a user might want to set something for
#     compiling this module distribution only via the setup.py command
#     line, whatever.  As long as these options come from something on the
#     current system, they can be as system-dependent as they like, and we
#     should just happily stuff them into the preprocessor/compiler/linker
#     options and carry on.


class UnixCCompiler(CCompiler):

    compiler_type = 'unix'

    # These are used by CCompiler in two places: the constructor sets
    # instance attributes 'preprocessor', 'compiler', etc. from them, and
    # 'set_executable()' allows any of these to be set.  The defaults here
    # are pretty generic; they will probably have to be set by an outsider
    # (eg. using information discovered by the sysconfig about building
    # Python extensions).
    executables = {'preprocessor' : None,
                   'compiler'     : ["cc"],
                   'compiler_so'  : ["cc"],
                   'compiler_cxx' : ["cc"],
                   'linker_so'    : ["cc", "-shared"],
                   'linker_exe'   : ["cc"],
                   'archiver'     : ["ar", "-cr"],
                   'ranlib'       : None,
                  }

    if sys.platform[:6] == "darwin":
        executables['ranlib'] = ["ranlib"]

    # Needed for the filename generation methods provided by the base
    # class, CCompiler.  NB. whoever instantiates/uses a particular
    # UnixCCompiler instance should set 'shared_lib_ext' -- we set a
    # reasonable common default here, but it's not necessarily used on all
    # Unices!

    src_extensions = [".c",".C",".cc",".cxx",".cpp",".m"]
    obj_extension = ".o"
    static_lib_extension = ".a"
    shared_lib_extension = ".so"
    dylib_lib_extension = ".dylib"
    xcode_stub_lib_extension = ".tbd"
    static_lib_format = shared_lib_format = dylib_lib_format = "lib%s%s"
    xcode_stub_lib_format = dylib_lib_format
    if sys.platform == "cygwin":
        exe_extension = ".exe"

    def preprocess(self, source, output_file=None, macros=None,
                   include_dirs=None, extra_preargs=None, extra_postargs=None):
        fixed_args = self._fix_compile_args(None, macros, include_dirs)
        ignore, macros, include_dirs = fixed_args
        pp_opts = gen_preprocess_options(macros, include_dirs)
        pp_args = self.preprocessor + pp_opts
        if output_file:
            pp_args.extend(['-o', output_file])
        if extra_preargs:
            pp_args[:0] = extra_preargs
        if extra_postargs:
            pp_args.extend(extra_postargs)
        pp_args.append(source)

        # We need to preprocess: either we're being forced to, or we're
        # generating output to stdout, or there's a target output file and
        # the source file is newer than the target (or the target doesn't
        # exist).
        if self.force or output_file is None or newer(source, output_file):
            if output_file:
                self.mkpath(os.path.dirname(output_file))
            try:
                self.spawn(pp_args)
            except DistutilsExecError as msg:
                raise CompileError(msg)

    def _compile(self, obj, src, ext, cc_args, extra_postargs, pp_opts):
        compiler_so = self.compiler_so
        if sys.platform == 'darwin':
            compiler_so = _osx_support.compiler_fixup(compiler_so,
                                                    cc_args + extra_postargs)
        try:
            self.spawn(compiler_so + cc_args + [src, '-o', obj] +
                       extra_postargs)
        except DistutilsExecError as msg:
            raise CompileError(msg)

    def create_static_lib(self, objects, output_libname,
                          output_dir=None, debug=0, target_lang=None):
        objects, output_dir = self._fix_object_args(objects, output_dir)

        output_filename = \
            self.library_filename(output_libname, output_dir=output_dir)

        if self._need_link(objects, output_filename):
            self.mkpath(os.path.dirname(output_filename))
            self.spawn(self.archiver +
                       [output_filename] +
                       objects + self.objects)

            # Not many Unices required ranlib anymore -- SunOS 4.x is, I
            # think the only major Unix that does.  Maybe we need some
            # platform intelligence here to skip ranlib if it's not
            # needed -- or maybe Python's configure script took care of
            # it for us, hence the check for leading colon.
            if self.ranlib:
                try:
                    self.spawn(self.ranlib + [output_filename])
                except DistutilsExecError as msg:
                    raise LibError(msg)
        else:
            log.debug("skipping %s (up-to-date)", output_filename)

    def link(self, target_desc, objects,
             output_filename, output_dir=None, libraries=None,
             library_dirs=None, runtime_library_dirs=None,
             export_symbols=None, debug=0, extra_preargs=None,
             extra_postargs=None, build_temp=None, target_lang=None):
        objects, output_dir = self._fix_object_args(objects, output_dir)
        fixed_args = self._fix_lib_args(libraries, library_dirs,
                                        runtime_library_dirs)
        libraries, library_dirs, runtime_library_dirs = fixed_args

        lib_opts = gen_lib_options(self, library_dirs, runtime_library_dirs,
                                   libraries)
        if not isinstance(output_dir, (str, type(None))):
            raise TypeError("'output_dir' must be a string or None")
        if output_dir is not None:
            output_filename = os.path.join(output_dir, output_filename)

        if self._need_link(objects, output_filename):
            ld_args = (objects + self.objects +
                       lib_opts + ['-o', output_filename])
            if debug:
                ld_args[:0] = ['-g']
            if extra_preargs:
                ld_args[:0] = extra_preargs
            if extra_postargs:
                ld_args.extend(extra_postargs)
            self.mkpath(os.path.dirname(output_filename))
            try:
                if target_desc == CCompiler.EXECUTABLE:
                    linker = self.linker_exe[:]
                else:
                    linker = self.linker_so[:]
                if target_lang == "c++" and self.compiler_cxx:
                    # skip over environment variable settings if /usr/bin/env
                    # is used to set up the linker's environment.
                    # This is needed on OSX. Note: this assumes that the
                    # normal and C++ compiler have the same environment
                    # settings.
                    i = 0
                    if os.path.basename(linker[0]) == "env":
                        i = 1
                        while '=' in linker[i]:
                            i += 1

                    if os.path.basename(linker[i]) == 'ld_so_aix':
                        # AIX platforms prefix the compiler with the ld_so_aix
                        # script, so we need to adjust our linker index
                        offset = 1
                    else:
                        offset = 0

                    linker[i+offset] = self.compiler_cxx[i]

                if sys.platform == 'darwin':
                    linker = _osx_support.compiler_fixup(linker, ld_args)

                self.spawn(linker + ld_args)
            except DistutilsExecError as msg:
                raise LinkError(msg)
        else:
            log.debug("skipping %s (up-to-date)", output_filename)

    # -- Miscellaneous methods -----------------------------------------
    # These are all used by the 'gen_lib_options() function, in
    # ccompiler.py.

    def library_dir_option(self, dir):
        return "-L" + dir

    def _is_gcc(self, compiler_name):
        return "gcc" in compiler_name or "g++" in compiler_name

    def runtime_library_dir_option(self, dir):
        # XXX Hackish, at the very least.  See Python bug #445902:
        # http://sourceforge.net/tracker/index.php
        #   ?func=detail&aid=445902&group_id=5470&atid=105470
        # Linkers on different platforms need different options to
        # specify that directories need to be added to the list of
        # directories searched for dependencies when a dynamic library
        # is sought.  GCC on GNU systems (Linux, FreeBSD, ...) has to
        # be told to pass the -R option through to the linker, whereas
        # other compilers and gcc on other systems just know this.
        # Other compilers may need something slightly different.  At
        # this time, there's no way to determine this information from
        # the configuration data stored in the Python installation, so
        # we use this hack.
        compiler = os.path.basename(sysconfig.get_config_var("CC"))
        if sys.platform[:6] == "darwin":
            from distutils.util import get_macosx_target_ver, split_version
            macosx_target_ver = get_macosx_target_ver()
            if macosx_target_ver and split_version(macosx_target_ver) >= [10, 5]:
                return "-Wl,-rpath," + dir
            else: # no support for -rpath on earlier macOS versions
                return "-L" + dir
        elif sys.platform[:7] == "freebsd":
            return "-Wl,-rpath=" + dir
        elif sys.platform[:5] == "hp-ux":
            if self._is_gcc(compiler):
                return ["-Wl,+s", "-L" + dir]
            return ["+s", "-L" + dir]
        else:
            if self._is_gcc(compiler):
                # gcc on non-GNU systems does not need -Wl, but can
                # use it anyway.  Since distutils has always passed in
                # -Wl whenever gcc was used in the past it is probably
                # safest to keep doing so.
                if sysconfig.get_config_var("GNULD") == "yes":
                    # GNU ld needs an extra option to get a RUNPATH
                    # instead of just an RPATH.
                    return "-Wl,--enable-new-dtags,-R" + dir
                else:
                    return "-Wl,-R" + dir
            else:
                # No idea how --enable-new-dtags would be passed on to
                # ld if this system was using GNU ld.  Don't know if a
                # system like this even exists.
                return "-R" + dir

    def library_option(self, lib):
        return "-l" + lib

    def find_library_file(self, dirs, lib, debug=0):
        shared_f = self.library_filename(lib, lib_type='shared')
        dylib_f = self.library_filename(lib, lib_type='dylib')
        xcode_stub_f = self.library_filename(lib, lib_type='xcode_stub')
        static_f = self.library_filename(lib, lib_type='static')

        if sys.platform == 'darwin':
            # On OSX users can specify an alternate SDK using
            # '-isysroot', calculate the SDK root if it is specified
            # (and use it further on)
            #
            # Note that, as of Xcode 7, Apple SDKs may contain textual stub
            # libraries with .tbd extensions rather than the normal .dylib
            # shared libraries installed in /.  The Apple compiler tool
            # chain handles this transparently but it can cause problems
            # for programs that are being built with an SDK and searching
            # for specific libraries.  Callers of find_library_file need to
            # keep in mind that the base filename of the returned SDK library
            # file might have a different extension from that of the library
            # file installed on the running system, for example:
            #   /Applications/Xcode.app/Contents/Developer/Platforms/
            #       MacOSX.platform/Developer/SDKs/MacOSX10.11.sdk/
            #       usr/lib/libedit.tbd
            # vs
            #   /usr/lib/libedit.dylib
            cflags = sysconfig.get_config_var('CFLAGS')
            m = re.search(r'-isysroot\s*(\S+)', cflags)
            if m is None:
                sysroot = '/'
            else:
                sysroot = m.group(1)



        for dir in dirs:
            shared = os.path.join(dir, shared_f)
            dylib = os.path.join(dir, dylib_f)
            static = os.path.join(dir, static_f)
            xcode_stub = os.path.join(dir, xcode_stub_f)

            if sys.platform == 'darwin' and (
                dir.startswith('/System/') or (
                dir.startswith('/usr/') and not dir.startswith('/usr/local/'))):

                shared = os.path.join(sysroot, dir[1:], shared_f)
                dylib = os.path.join(sysroot, dir[1:], dylib_f)
                static = os.path.join(sysroot, dir[1:], static_f)
                xcode_stub = os.path.join(sysroot, dir[1:], xcode_stub_f)

            # We're second-guessing the linker here, with not much hard
            # data to go on: GCC seems to prefer the shared library, so I'm
            # assuming that *all* Unix C compilers do.  And of course I'm
            # ignoring even GCC's "-static" option.  So sue me.
            if os.path.exists(dylib):
                return dylib
            elif os.path.exists(xcode_stub):
                return xcode_stub
            elif os.path.exists(shared):
                return shared
            elif os.path.exists(static):
                return static

        # Oops, didn't find it in *any* of 'dirs'
        return None

"""distutils.bcppcompiler

Contains BorlandCCompiler, an implementation of the abstract CCompiler class
for the Borland C++ compiler.
"""

# This implementation by Lyle Johnson, based on the original msvccompiler.py
# module and using the directions originally published by Gordon Williams.

# XXX looks like there's a LOT of overlap between these two classes:
# someone should sit down and factor out the common code as
# WindowsCCompiler!  --GPW


import os
from distutils.errors import \
     DistutilsExecError, \
     CompileError, LibError, LinkError, UnknownFileError
from distutils.ccompiler import \
     CCompiler, gen_preprocess_options
from distutils.file_util import write_file
from distutils.dep_util import newer
from distutils import log

class BCPPCompiler(CCompiler) :
    """Concrete class that implements an interface to the Borland C/C++
    compiler, as defined by the CCompiler abstract class.
    """

    compiler_type = 'bcpp'

    # Just set this so CCompiler's constructor doesn't barf.  We currently
    # don't use the 'set_executables()' bureaucracy provided by CCompiler,
    # as it really isn't necessary for this sort of single-compiler class.
    # Would be nice to have a consistent interface with UnixCCompiler,
    # though, so it's worth thinking about.
    executables = {}

    # Private class data (need to distinguish C from C++ source for compiler)
    _c_extensions = ['.c']
    _cpp_extensions = ['.cc', '.cpp', '.cxx']

    # Needed for the filename generation methods provided by the
    # base class, CCompiler.
    src_extensions = _c_extensions + _cpp_extensions
    obj_extension = '.obj'
    static_lib_extension = '.lib'
    shared_lib_extension = '.dll'
    static_lib_format = shared_lib_format = '%s%s'
    exe_extension = '.exe'


    def __init__ (self,
                  verbose=0,
                  dry_run=0,
                  force=0):

        CCompiler.__init__ (self, verbose, dry_run, force)

        # These executables are assumed to all be in the path.
        # Borland doesn't seem to use any special registry settings to
        # indicate their installation locations.

        self.cc = "bcc32.exe"
        self.linker = "ilink32.exe"
        self.lib = "tlib.exe"

        self.preprocess_options = None
        self.compile_options = ['/tWM', '/O2', '/q', '/g0']
        self.compile_options_debug = ['/tWM', '/Od', '/q', '/g0']

        self.ldflags_shared = ['/Tpd', '/Gn', '/q', '/x']
        self.ldflags_shared_debug = ['/Tpd', '/Gn', '/q', '/x']
        self.ldflags_static = []
        self.ldflags_exe = ['/Gn', '/q', '/x']
        self.ldflags_exe_debug = ['/Gn', '/q', '/x','/r']


    # -- Worker methods ------------------------------------------------

    def compile(self, sources,
                output_dir=None, macros=None, include_dirs=None, debug=0,
                extra_preargs=None, extra_postargs=None, depends=None):

        macros, objects, extra_postargs, pp_opts, build = \
                self._setup_compile(output_dir, macros, include_dirs, sources,
                                    depends, extra_postargs)
        compile_opts = extra_preargs or []
        compile_opts.append ('-c')
        if debug:
            compile_opts.extend (self.compile_options_debug)
        else:
            compile_opts.extend (self.compile_options)

        for obj in objects:
            try:
                src, ext = build[obj]
            except KeyError:
                continue
            # XXX why do the normpath here?
            src = os.path.normpath(src)
            obj = os.path.normpath(obj)
            # XXX _setup_compile() did a mkpath() too but before the normpath.
            # Is it possible to skip the normpath?
            self.mkpath(os.path.dirname(obj))

            if ext == '.res':
                # This is already a binary file -- skip it.
                continue # the 'for' loop
            if ext == '.rc':
                # This needs to be compiled to a .res file -- do it now.
                try:
                    self.spawn (["brcc32", "-fo", obj, src])
                except DistutilsExecError as msg:
                    raise CompileError(msg)
                continue # the 'for' loop

            # The next two are both for the real compiler.
            if ext in self._c_extensions:
                input_opt = ""
            elif ext in self._cpp_extensions:
                input_opt = "-P"
            else:
                # Unknown file type -- no extra options.  The compiler
                # will probably fail, but let it just in case this is a
                # file the compiler recognizes even if we don't.
                input_opt = ""

            output_opt = "-o" + obj

            # Compiler command line syntax is: "bcc32 [options] file(s)".
            # Note that the source file names must appear at the end of
            # the command line.
            try:
                self.spawn ([self.cc] + compile_opts + pp_opts +
                            [input_opt, output_opt] +
                            extra_postargs + [src])
            except DistutilsExecError as msg:
                raise CompileError(msg)

        return objects

    # compile ()


    def create_static_lib (self,
                           objects,
                           output_libname,
                           output_dir=None,
                           debug=0,
                           target_lang=None):

        (objects, output_dir) = self._fix_object_args (objects, output_dir)
        output_filename = \
            self.library_filename (output_libname, output_dir=output_dir)

        if self._need_link (objects, output_filename):
            lib_args = [output_filename, '/u'] + objects
            if debug:
                pass                    # XXX what goes here?
            try:
                self.spawn ([self.lib] + lib_args)
            except DistutilsExecError as msg:
                raise LibError(msg)
        else:
            log.debug("skipping %s (up-to-date)", output_filename)

    # create_static_lib ()


    def link (self,
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

        # XXX this ignores 'build_temp'!  should follow the lead of
        # msvccompiler.py

        (objects, output_dir) = self._fix_object_args (objects, output_dir)
        (libraries, library_dirs, runtime_library_dirs) = \
            self._fix_lib_args (libraries, library_dirs, runtime_library_dirs)

        if runtime_library_dirs:
            log.warn("I don't know what to do with 'runtime_library_dirs': %s",
                     str(runtime_library_dirs))

        if output_dir is not None:
            output_filename = os.path.join (output_dir, output_filename)

        if self._need_link (objects, output_filename):

            # Figure out linker args based on type of target.
            if target_desc == CCompiler.EXECUTABLE:
                startup_obj = 'c0w32'
                if debug:
                    ld_args = self.ldflags_exe_debug[:]
                else:
                    ld_args = self.ldflags_exe[:]
            else:
                startup_obj = 'c0d32'
                if debug:
                    ld_args = self.ldflags_shared_debug[:]
                else:
                    ld_args = self.ldflags_shared[:]


            # Create a temporary exports file for use by the linker
            if export_symbols is None:
                def_file = ''
            else:
                head, tail = os.path.split (output_filename)
                modname, ext = os.path.splitext (tail)
                temp_dir = os.path.dirname(objects[0]) # preserve tree structure
                def_file = os.path.join (temp_dir, '%s.def' % modname)
                contents = ['EXPORTS']
                for sym in (export_symbols or []):
                    contents.append('  %s=_%s' % (sym, sym))
                self.execute(write_file, (def_file, contents),
                             "writing %s" % def_file)

            # Borland C++ has problems with '/' in paths
            objects2 = map(os.path.normpath, objects)
            # split objects in .obj and .res files
            # Borland C++ needs them at different positions in the command line
            objects = [startup_obj]
            resources = []
            for file in objects2:
                (base, ext) = os.path.splitext(os.path.normcase(file))
                if ext == '.res':
                    resources.append(file)
                else:
                    objects.append(file)


            for l in library_dirs:
                ld_args.append("/L%s" % os.path.normpath(l))
            ld_args.append("/L.") # we sometimes use relative paths

            # list of object files
            ld_args.extend(objects)

            # XXX the command-line syntax for Borland C++ is a bit wonky;
            # certain filenames are jammed together in one big string, but
            # comma-delimited.  This doesn't mesh too well with the
            # Unix-centric attitude (with a DOS/Windows quoting hack) of
            # 'spawn()', so constructing the argument list is a bit
            # awkward.  Note that doing the obvious thing and jamming all
            # the filenames and commas into one argument would be wrong,
            # because 'spawn()' would quote any filenames with spaces in
            # them.  Arghghh!.  Apparently it works fine as coded...

            # name of dll/exe file
            ld_args.extend([',',output_filename])
            # no map file and start libraries
            ld_args.append(',,')

            for lib in libraries:
                # see if we find it and if there is a bcpp specific lib
                # (xxx_bcpp.lib)
                libfile = self.find_library_file(library_dirs, lib, debug)
                if libfile is None:
                    ld_args.append(lib)
                    # probably a BCPP internal library -- don't warn
                else:
                    # full name which prefers bcpp_xxx.lib over xxx.lib
                    ld_args.append(libfile)

            # some default libraries
            ld_args.append ('import32')
            ld_args.append ('cw32mt')

            # def file for export symbols
            ld_args.extend([',',def_file])
            # add resource files
            ld_args.append(',')
            ld_args.extend(resources)


            if extra_preargs:
                ld_args[:0] = extra_preargs
            if extra_postargs:
                ld_args.extend(extra_postargs)

            self.mkpath (os.path.dirname (output_filename))
            try:
                self.spawn ([self.linker] + ld_args)
            except DistutilsExecError as msg:
                raise LinkError(msg)

        else:
            log.debug("skipping %s (up-to-date)", output_filename)

    # link ()

    # -- Miscellaneous methods -----------------------------------------


    def find_library_file (self, dirs, lib, debug=0):
        # List of effective library names to try, in order of preference:
        # xxx_bcpp.lib is better than xxx.lib
        # and xxx_d.lib is better than xxx.lib if debug is set
        #
        # The "_bcpp" suffix is to handle a Python installation for people
        # with multiple compilers (primarily Distutils hackers, I suspect
        # ;-).  The idea is they'd have one static library for each
        # compiler they care about, since (almost?) every Windows compiler
        # seems to have a different format for static libraries.
        if debug:
            dlib = (lib + "_d")
            try_names = (dlib + "_bcpp", lib + "_bcpp", dlib, lib)
        else:
            try_names = (lib + "_bcpp", lib)

        for dir in dirs:
            for name in try_names:
                libfile = os.path.join(dir, self.library_filename(name))
                if os.path.exists(libfile):
                    return libfile
        else:
            # Oops, didn't find it in *any* of 'dirs'
            return None

    # overwrite the one from CCompiler to support rc and res-files
    def object_filenames (self,
                          source_filenames,
                          strip_dir=0,
                          output_dir=''):
        if output_dir is None: output_dir = ''
        obj_names = []
        for src_name in source_filenames:
            # use normcase to make sure '.rc' is really '.rc' and not '.RC'
            (base, ext) = os.path.splitext (os.path.normcase(src_name))
            if ext not in (self.src_extensions + ['.rc','.res']):
                raise UnknownFileError("unknown file type '%s' (from '%s')" % \
                      (ext, src_name))
            if strip_dir:
                base = os.path.basename (base)
            if ext == '.res':
                # these can go unchanged
                obj_names.append (os.path.join (output_dir, base + ext))
            elif ext == '.rc':
                # these need to be compiled to .res-files
                obj_names.append (os.path.join (output_dir, base + '.res'))
            else:
                obj_names.append (os.path.join (output_dir,
                                            base + self.obj_extension))
        return obj_names

    # object_filenames ()

    def preprocess (self,
                    source,
                    output_file=None,
                    macros=None,
                    include_dirs=None,
                    extra_preargs=None,
                    extra_postargs=None):

        (_, macros, include_dirs) = \
            self._fix_compile_args(None, macros, include_dirs)
        pp_opts = gen_preprocess_options(macros, include_dirs)
        pp_args = ['cpp32.exe'] + pp_opts
        if output_file is not None:
            pp_args.append('-o' + output_file)
        if extra_preargs:
            pp_args[:0] = extra_preargs
        if extra_postargs:
            pp_args.extend(extra_postargs)
        pp_args.append(source)

        # We need to preprocess: either we're being forced to, or the
        # source file is newer than the target (or the target doesn't
        # exist).
        if self.force or output_file is None or newer(source, output_file):
            if output_file:
                self.mkpath(os.path.dirname(output_file))
            try:
                self.spawn(pp_args)
            except DistutilsExecError as msg:
                print(msg)
                raise CompileError(msg)

    # preprocess()

# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2023 Vinay Sajip.
# Licensed to the Python Software Foundation under a contributor agreement.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
from io import BytesIO
import logging
import os
import re
import struct
import sys
import time
from zipfile import ZipInfo

from .compat import sysconfig, detect_encoding, ZipFile
from .resources import finder
from .util import (FileOperator, get_export_entry, convert_path, get_executable, get_platform, in_venv)

logger = logging.getLogger(__name__)

_DEFAULT_MANIFEST = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
 <assemblyIdentity version="1.0.0.0"
 processorArchitecture="X86"
 name="%s"
 type="win32"/>

 <!-- Identify the application security requirements. -->
 <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
 <security>
 <requestedPrivileges>
 <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
 </requestedPrivileges>
 </security>
 </trustInfo>
</assembly>'''.strip()

# check if Python is called on the first line with this expression
FIRST_LINE_RE = re.compile(b'^#!.*pythonw?[0-9.]*([ \t].*)?$')
SCRIPT_TEMPLATE = r'''# -*- coding: utf-8 -*-
import re
import sys
if __name__ == '__main__':
    from %(module)s import %(import_name)s
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(%(func)s())
'''

# Pre-fetch the contents of all executable wrapper stubs.
# This is to address https://github.com/pypa/pip/issues/12666.
# When updating pip, we rename the old pip in place before installing the
# new version. If we try to fetch a wrapper *after* that rename, the finder
# machinery will be confused as the package is no longer available at the
# location where it was imported from. So we load everything into memory in
# advance.

if os.name == 'nt' or (os.name == 'java' and os._name == 'nt'):
    # Issue 31: don't hardcode an absolute package name, but
    # determine it relative to the current package
    DISTLIB_PACKAGE = __name__.rsplit('.', 1)[0]

    WRAPPERS = {
        r.name: r.bytes
        for r in finder(DISTLIB_PACKAGE).iterator("")
        if r.name.endswith(".exe")
    }


def enquote_executable(executable):
    if ' ' in executable:
        # make sure we quote only the executable in case of env
        # for example /usr/bin/env "/dir with spaces/bin/jython"
        # instead of "/usr/bin/env /dir with spaces/bin/jython"
        # otherwise whole
        if executable.startswith('/usr/bin/env '):
            env, _executable = executable.split(' ', 1)
            if ' ' in _executable and not _executable.startswith('"'):
                executable = '%s "%s"' % (env, _executable)
        else:
            if not executable.startswith('"'):
                executable = '"%s"' % executable
    return executable


# Keep the old name around (for now), as there is at least one project using it!
_enquote_executable = enquote_executable


class ScriptMaker(object):
    """
    A class to copy or create scripts from source scripts or callable
    specifications.
    """
    script_template = SCRIPT_TEMPLATE

    executable = None  # for shebangs

    def __init__(self, source_dir, target_dir, add_launchers=True, dry_run=False, fileop=None):
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.add_launchers = add_launchers
        self.force = False
        self.clobber = False
        # It only makes sense to set mode bits on POSIX.
        self.set_mode = (os.name == 'posix') or (os.name == 'java' and os._name == 'posix')
        self.variants = set(('', 'X.Y'))
        self._fileop = fileop or FileOperator(dry_run)

        self._is_nt = os.name == 'nt' or (os.name == 'java' and os._name == 'nt')
        self.version_info = sys.version_info

    def _get_alternate_executable(self, executable, options):
        if options.get('gui', False) and self._is_nt:  # pragma: no cover
            dn, fn = os.path.split(executable)
            fn = fn.replace('python', 'pythonw')
            executable = os.path.join(dn, fn)
        return executable

    if sys.platform.startswith('java'):  # pragma: no cover

        def _is_shell(self, executable):
            """
            Determine if the specified executable is a script
            (contains a #! line)
            """
            try:
                with open(executable) as fp:
                    return fp.read(2) == '#!'
            except (OSError, IOError):
                logger.warning('Failed to open %s', executable)
                return False

        def _fix_jython_executable(self, executable):
            if self._is_shell(executable):
                # Workaround for Jython is not needed on Linux systems.
                import java

                if java.lang.System.getProperty('os.name') == 'Linux':
                    return executable
            elif executable.lower().endswith('jython.exe'):
                # Use wrapper exe for Jython on Windows
                return executable
            return '/usr/bin/env %s' % executable

    def _build_shebang(self, executable, post_interp):
        """
        Build a shebang line. In the simple case (on Windows, or a shebang line
        which is not too long or contains spaces) use a simple formulation for
        the shebang. Otherwise, use /bin/sh as the executable, with a contrived
        shebang which allows the script to run either under Python or sh, using
        suitable quoting. Thanks to Harald Nordgren for his input.

        See also: http://www.in-ulm.de/~mascheck/various/shebang/#length
                  https://hg.mozilla.org/mozilla-central/file/tip/mach
        """
        if os.name != 'posix':
            simple_shebang = True
        elif getattr(sys, "cross_compiling", False):
            # In a cross-compiling environment, the shebang will likely be a
            # script; this *must* be invoked with the "safe" version of the
            # shebang, or else using os.exec() to run the entry script will
            # fail, raising "OSError 8 [Errno 8] Exec format error".
            simple_shebang = False
        else:
            # Add 3 for '#!' prefix and newline suffix.
            shebang_length = len(executable) + len(post_interp) + 3
            if sys.platform == 'darwin':
                max_shebang_length = 512
            else:
                max_shebang_length = 127
            simple_shebang = ((b' ' not in executable) and (shebang_length <= max_shebang_length))

        if simple_shebang:
            result = b'#!' + executable + post_interp + b'\n'
        else:
            result = b'#!/bin/sh\n'
            result += b"'''exec' " + executable + post_interp + b' "$0" "$@"\n'
            result += b"' '''\n"
        return result

    def _get_shebang(self, encoding, post_interp=b'', options=None):
        enquote = True
        if self.executable:
            executable = self.executable
            enquote = False  # assume this will be taken care of
        elif not sysconfig.is_python_build():
            executable = get_executable()
        elif in_venv():  # pragma: no cover
            executable = os.path.join(sysconfig.get_path('scripts'), 'python%s' % sysconfig.get_config_var('EXE'))
        else:  # pragma: no cover
            if os.name == 'nt':
                # for Python builds from source on Windows, no Python executables with
                # a version suffix are created, so we use python.exe
                executable = os.path.join(sysconfig.get_config_var('BINDIR'),
                                          'python%s' % (sysconfig.get_config_var('EXE')))
            else:
                executable = os.path.join(
                    sysconfig.get_config_var('BINDIR'),
                    'python%s%s' % (sysconfig.get_config_var('VERSION'), sysconfig.get_config_var('EXE')))
        if options:
            executable = self._get_alternate_executable(executable, options)

        if sys.platform.startswith('java'):  # pragma: no cover
            executable = self._fix_jython_executable(executable)

        # Normalise case for Windows - COMMENTED OUT
        # executable = os.path.normcase(executable)
        # N.B. The normalising operation above has been commented out: See
        # issue #124. Although paths in Windows are generally case-insensitive,
        # they aren't always. For example, a path containing a ẞ (which is a
        # LATIN CAPITAL LETTER SHARP S - U+1E9E) is normcased to ß (which is a
        # LATIN SMALL LETTER SHARP S' - U+00DF). The two are not considered by
        # Windows as equivalent in path names.

        # If the user didn't specify an executable, it may be necessary to
        # cater for executable paths with spaces (not uncommon on Windows)
        if enquote:
            executable = enquote_executable(executable)
        # Issue #51: don't use fsencode, since we later try to
        # check that the shebang is decodable using utf-8.
        executable = executable.encode('utf-8')
        # in case of IronPython, play safe and enable frames support
        if (sys.platform == 'cli' and '-X:Frames' not in post_interp and
                '-X:FullFrames' not in post_interp):  # pragma: no cover
            post_interp += b' -X:Frames'
        shebang = self._build_shebang(executable, post_interp)
        # Python parser starts to read a script using UTF-8 until
        # it gets a #coding:xxx cookie. The shebang has to be the
        # first line of a file, the #coding:xxx cookie cannot be
        # written before. So the shebang has to be decodable from
        # UTF-8.
        try:
            shebang.decode('utf-8')
        except UnicodeDecodeError:  # pragma: no cover
            raise ValueError('The shebang (%r) is not decodable from utf-8' % shebang)
        # If the script is encoded to a custom encoding (use a
        # #coding:xxx cookie), the shebang has to be decodable from
        # the script encoding too.
        if encoding != 'utf-8':
            try:
                shebang.decode(encoding)
            except UnicodeDecodeError:  # pragma: no cover
                raise ValueError('The shebang (%r) is not decodable '
                                 'from the script encoding (%r)' % (shebang, encoding))
        return shebang

    def _get_script_text(self, entry):
        return self.script_template % dict(
            module=entry.prefix, import_name=entry.suffix.split('.')[0], func=entry.suffix)

    manifest = _DEFAULT_MANIFEST

    def get_manifest(self, exename):
        base = os.path.basename(exename)
        return self.manifest % base

    def _write_script(self, names, shebang, script_bytes, filenames, ext):
        use_launcher = self.add_launchers and self._is_nt
        if not use_launcher:
            script_bytes = shebang + script_bytes
        else:  # pragma: no cover
            if ext == 'py':
                launcher = self._get_launcher('t')
            else:
                launcher = self._get_launcher('w')
            stream = BytesIO()
            with ZipFile(stream, 'w') as zf:
                source_date_epoch = os.environ.get('SOURCE_DATE_EPOCH')
                if source_date_epoch:
                    date_time = time.gmtime(int(source_date_epoch))[:6]
                    zinfo = ZipInfo(filename='__main__.py', date_time=date_time)
                    zf.writestr(zinfo, script_bytes)
                else:
                    zf.writestr('__main__.py', script_bytes)
            zip_data = stream.getvalue()
            script_bytes = launcher + shebang + zip_data
        for name in names:
            outname = os.path.join(self.target_dir, name)
            if use_launcher:  # pragma: no cover
                n, e = os.path.splitext(outname)
                if e.startswith('.py'):
                    outname = n
                outname = '%s.exe' % outname
                try:
                    self._fileop.write_binary_file(outname, script_bytes)
                except Exception:
                    # Failed writing an executable - it might be in use.
                    logger.warning('Failed to write executable - trying to '
                                   'use .deleteme logic')
                    dfname = '%s.deleteme' % outname
                    if os.path.exists(dfname):
                        os.remove(dfname)  # Not allowed to fail here
                    os.rename(outname, dfname)  # nor here
                    self._fileop.write_binary_file(outname, script_bytes)
                    logger.debug('Able to replace executable using '
                                 '.deleteme logic')
                    try:
                        os.remove(dfname)
                    except Exception:
                        pass  # still in use - ignore error
            else:
                if self._is_nt and not outname.endswith('.' + ext):  # pragma: no cover
                    outname = '%s.%s' % (outname, ext)
                if os.path.exists(outname) and not self.clobber:
                    logger.warning('Skipping existing file %s', outname)
                    continue
                self._fileop.write_binary_file(outname, script_bytes)
                if self.set_mode:
                    self._fileop.set_executable_mode([outname])
            filenames.append(outname)

    variant_separator = '-'

    def get_script_filenames(self, name):
        result = set()
        if '' in self.variants:
            result.add(name)
        if 'X' in self.variants:
            result.add('%s%s' % (name, self.version_info[0]))
        if 'X.Y' in self.variants:
            result.add('%s%s%s.%s' % (name, self.variant_separator, self.version_info[0], self.version_info[1]))
        return result

    def _make_script(self, entry, filenames, options=None):
        post_interp = b''
        if options:
            args = options.get('interpreter_args', [])
            if args:
                args = ' %s' % ' '.join(args)
                post_interp = args.encode('utf-8')
        shebang = self._get_shebang('utf-8', post_interp, options=options)
        script = self._get_script_text(entry).encode('utf-8')
        scriptnames = self.get_script_filenames(entry.name)
        if options and options.get('gui', False):
            ext = 'pyw'
        else:
            ext = 'py'
        self._write_script(scriptnames, shebang, script, filenames, ext)

    def _copy_script(self, script, filenames):
        adjust = False
        script = os.path.join(self.source_dir, convert_path(script))
        outname = os.path.join(self.target_dir, os.path.basename(script))
        if not self.force and not self._fileop.newer(script, outname):
            logger.debug('not copying %s (up-to-date)', script)
            return

        # Always open the file, but ignore failures in dry-run mode --
        # that way, we'll get accurate feedback if we can read the
        # script.
        try:
            f = open(script, 'rb')
        except IOError:  # pragma: no cover
            if not self.dry_run:
                raise
            f = None
        else:
            first_line = f.readline()
            if not first_line:  # pragma: no cover
                logger.warning('%s is an empty file (skipping)', script)
                return

            match = FIRST_LINE_RE.match(first_line.replace(b'\r\n', b'\n'))
            if match:
                adjust = True
                post_interp = match.group(1) or b''

        if not adjust:
            if f:
                f.close()
            self._fileop.copy_file(script, outname)
            if self.set_mode:
                self._fileop.set_executable_mode([outname])
            filenames.append(outname)
        else:
            logger.info('copying and adjusting %s -> %s', script, self.target_dir)
            if not self._fileop.dry_run:
                encoding, lines = detect_encoding(f.readline)
                f.seek(0)
                shebang = self._get_shebang(encoding, post_interp)
                if b'pythonw' in first_line:  # pragma: no cover
                    ext = 'pyw'
                else:
                    ext = 'py'
                n = os.path.basename(outname)
                self._write_script([n], shebang, f.read(), filenames, ext)
            if f:
                f.close()

    @property
    def dry_run(self):
        return self._fileop.dry_run

    @dry_run.setter
    def dry_run(self, value):
        self._fileop.dry_run = value

    if os.name == 'nt' or (os.name == 'java' and os._name == 'nt'):  # pragma: no cover
        # Executable launcher support.
        # Launchers are from https://bitbucket.org/vinay.sajip/simple_launcher/

        def _get_launcher(self, kind):
            if struct.calcsize('P') == 8:  # 64-bit
                bits = '64'
            else:
                bits = '32'
            platform_suffix = '-arm' if get_platform() == 'win-arm64' else ''
            name = '%s%s%s.exe' % (kind, bits, platform_suffix)
            if name not in WRAPPERS:
                msg = ('Unable to find resource %s in package %s' %
                       (name, DISTLIB_PACKAGE))
                raise ValueError(msg)
            return WRAPPERS[name]

    # Public API follows

    def make(self, specification, options=None):
        """
        Make a script.

        :param specification: The specification, which is either a valid export
                              entry specification (to make a script from a
                              callable) or a filename (to make a script by
                              copying from a source location).
        :param options: A dictionary of options controlling script generation.
        :return: A list of all absolute pathnames written to.
        """
        filenames = []
        entry = get_export_entry(specification)
        if entry is None:
            self._copy_script(specification, filenames)
        else:
            self._make_script(entry, filenames, options=options)
        return filenames

    def make_multiple(self, specifications, options=None):
        """
        Take a list of specifications and make scripts from them,
        :param specifications: A list of specifications.
        :return: A list of all absolute pathnames written to,
        """
        filenames = []
        for specification in specifications:
            filenames.extend(self.make(specification, options))
        return filenames

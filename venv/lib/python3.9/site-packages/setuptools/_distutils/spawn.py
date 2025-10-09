"""distutils.spawn

Provides the 'spawn()' function, a front-end to various platform-
specific functions for launching another program in a sub-process.
Also provides the 'find_executable()' to search the path for a given
executable name.
"""

import sys
import os
import subprocess

from distutils.errors import DistutilsPlatformError, DistutilsExecError
from distutils.debug import DEBUG
from distutils import log


def spawn(cmd, search_path=1, verbose=0, dry_run=0, env=None):
    """Run another program, specified as a command list 'cmd', in a new process.

    'cmd' is just the argument list for the new process, ie.
    cmd[0] is the program to run and cmd[1:] are the rest of its arguments.
    There is no way to run a program with a name different from that of its
    executable.

    If 'search_path' is true (the default), the system's executable
    search path will be used to find the program; otherwise, cmd[0]
    must be the exact path to the executable.  If 'dry_run' is true,
    the command will not actually be run.

    Raise DistutilsExecError if running the program fails in any way; just
    return on success.
    """
    # cmd is documented as a list, but just in case some code passes a tuple
    # in, protect our %-formatting code against horrible death
    cmd = list(cmd)

    log.info(subprocess.list2cmdline(cmd))
    if dry_run:
        return

    if search_path:
        executable = find_executable(cmd[0])
        if executable is not None:
            cmd[0] = executable

    env = env if env is not None else dict(os.environ)

    if sys.platform == 'darwin':
        from distutils.util import MACOSX_VERSION_VAR, get_macosx_target_ver
        macosx_target_ver = get_macosx_target_ver()
        if macosx_target_ver:
            env[MACOSX_VERSION_VAR] = macosx_target_ver

    try:
        proc = subprocess.Popen(cmd, env=env)
        proc.wait()
        exitcode = proc.returncode
    except OSError as exc:
        if not DEBUG:
            cmd = cmd[0]
        raise DistutilsExecError(
            "command %r failed: %s" % (cmd, exc.args[-1])) from exc

    if exitcode:
        if not DEBUG:
            cmd = cmd[0]
        raise DistutilsExecError(
              "command %r failed with exit code %s" % (cmd, exitcode))


def find_executable(executable, path=None):
    """Tries to find 'executable' in the directories listed in 'path'.

    A string listing directories separated by 'os.pathsep'; defaults to
    os.environ['PATH'].  Returns the complete filename or None if not found.
    """
    _, ext = os.path.splitext(executable)
    if (sys.platform == 'win32') and (ext != '.exe'):
        executable = executable + '.exe'

    if os.path.isfile(executable):
        return executable

    if path is None:
        path = os.environ.get('PATH', None)
        if path is None:
            try:
                path = os.confstr("CS_PATH")
            except (AttributeError, ValueError):
                # os.confstr() or CS_PATH is not available
                path = os.defpath
        # bpo-35755: Don't use os.defpath if the PATH environment variable is
        # set to an empty string

    # PATH='' doesn't match, whereas PATH=':' looks in the current directory
    if not path:
        return None

    paths = path.split(os.pathsep)
    for p in paths:
        f = os.path.join(p, executable)
        if os.path.isfile(f):
            # the file exists, we have a shot at spawn working
            return f
    return None

from distutils.errors import DistutilsArgError
import inspect
import glob
import warnings
import platform
import distutils.command.install as orig

import setuptools

# Prior to numpy 1.9, NumPy relies on the '_install' name, so provide it for
# now. See https://github.com/pypa/setuptools/issues/199/
_install = orig.install


class install(orig.install):
    """Use easy_install to install the package, w/dependencies"""

    user_options = orig.install.user_options + [
        ('old-and-unmanageable', None, "Try not to use this!"),
        ('single-version-externally-managed', None,
         "used by system package builders to create 'flat' eggs"),
    ]
    boolean_options = orig.install.boolean_options + [
        'old-and-unmanageable', 'single-version-externally-managed',
    ]
    new_commands = [
        ('install_egg_info', lambda self: True),
        ('install_scripts', lambda self: True),
    ]
    _nc = dict(new_commands)

    def initialize_options(self):
        orig.install.initialize_options(self)
        self.old_and_unmanageable = None
        self.single_version_externally_managed = None

    def finalize_options(self):
        orig.install.finalize_options(self)
        if self.root:
            self.single_version_externally_managed = True
        elif self.single_version_externally_managed:
            if not self.root and not self.record:
                raise DistutilsArgError(
                    "You must specify --record or --root when building system"
                    " packages"
                )

    def handle_extra_path(self):
        if self.root or self.single_version_externally_managed:
            # explicit backward-compatibility mode, allow extra_path to work
            return orig.install.handle_extra_path(self)

        # Ignore extra_path when installing an egg (or being run by another
        # command without --root or --single-version-externally-managed
        self.path_file = None
        self.extra_dirs = ''

    def run(self):
        # Explicit request for old-style install?  Just do it
        if self.old_and_unmanageable or self.single_version_externally_managed:
            return orig.install.run(self)

        if not self._called_from_setup(inspect.currentframe()):
            # Run in backward-compatibility mode to support bdist_* commands.
            orig.install.run(self)
        else:
            self.do_egg_install()

    @staticmethod
    def _called_from_setup(run_frame):
        """
        Attempt to detect whether run() was called from setup() or by another
        command.  If called by setup(), the parent caller will be the
        'run_command' method in 'distutils.dist', and *its* caller will be
        the 'run_commands' method.  If called any other way, the
        immediate caller *might* be 'run_command', but it won't have been
        called by 'run_commands'. Return True in that case or if a call stack
        is unavailable. Return False otherwise.
        """
        if run_frame is None:
            msg = "Call stack not available. bdist_* commands may fail."
            warnings.warn(msg)
            if platform.python_implementation() == 'IronPython':
                msg = "For best results, pass -X:Frames to enable call stack."
                warnings.warn(msg)
            return True
        res = inspect.getouterframes(run_frame)[2]
        caller, = res[:1]
        info = inspect.getframeinfo(caller)
        caller_module = caller.f_globals.get('__name__', '')
        return (
            caller_module == 'distutils.dist'
            and info.function == 'run_commands'
        )

    def do_egg_install(self):

        easy_install = self.distribution.get_command_class('easy_install')

        cmd = easy_install(
            self.distribution, args="x", root=self.root, record=self.record,
        )
        cmd.ensure_finalized()  # finalize before bdist_egg munges install cmd
        cmd.always_copy_from = '.'  # make sure local-dir eggs get installed

        # pick up setup-dir .egg files only: no .egg-info
        cmd.package_index.scan(glob.glob('*.egg'))

        self.run_command('bdist_egg')
        args = [self.distribution.get_command_obj('bdist_egg').egg_output]

        if setuptools.bootstrap_install_from:
            # Bootstrap self-installation of setuptools
            args.insert(0, setuptools.bootstrap_install_from)

        cmd.args = args
        cmd.run(show_deprecation=False)
        setuptools.bootstrap_install_from = None


# XXX Python 3.1 doesn't see _nc if this is inside the class
install.sub_commands = (
    [cmd for cmd in orig.install.sub_commands if cmd[0] not in install._nc] +
    install.new_commands
)

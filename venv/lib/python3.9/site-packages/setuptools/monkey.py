"""
Monkey patching of distutils.
"""

import sys
import distutils.filelist
import platform
import types
import functools
from importlib import import_module
import inspect

import setuptools

__all__ = []
"""
Everything is private. Contact the project team
if you think you need this functionality.
"""


def _get_mro(cls):
    """
    Returns the bases classes for cls sorted by the MRO.

    Works around an issue on Jython where inspect.getmro will not return all
    base classes if multiple classes share the same name. Instead, this
    function will return a tuple containing the class itself, and the contents
    of cls.__bases__. See https://github.com/pypa/setuptools/issues/1024.
    """
    if platform.python_implementation() == "Jython":
        return (cls,) + cls.__bases__
    return inspect.getmro(cls)


def get_unpatched(item):
    lookup = (
        get_unpatched_class if isinstance(item, type) else
        get_unpatched_function if isinstance(item, types.FunctionType) else
        lambda item: None
    )
    return lookup(item)


def get_unpatched_class(cls):
    """Protect against re-patching the distutils if reloaded

    Also ensures that no other distutils extension monkeypatched the distutils
    first.
    """
    external_bases = (
        cls
        for cls in _get_mro(cls)
        if not cls.__module__.startswith('setuptools')
    )
    base = next(external_bases)
    if not base.__module__.startswith('distutils'):
        msg = "distutils has already been patched by %r" % cls
        raise AssertionError(msg)
    return base


def patch_all():
    # we can't patch distutils.cmd, alas
    distutils.core.Command = setuptools.Command

    has_issue_12885 = sys.version_info <= (3, 5, 3)

    if has_issue_12885:
        # fix findall bug in distutils (http://bugs.python.org/issue12885)
        distutils.filelist.findall = setuptools.findall

    needs_warehouse = (
        sys.version_info < (2, 7, 13)
        or
        (3, 4) < sys.version_info < (3, 4, 6)
        or
        (3, 5) < sys.version_info <= (3, 5, 3)
    )

    if needs_warehouse:
        warehouse = 'https://upload.pypi.org/legacy/'
        distutils.config.PyPIRCCommand.DEFAULT_REPOSITORY = warehouse

    _patch_distribution_metadata()

    # Install Distribution throughout the distutils
    for module in distutils.dist, distutils.core, distutils.cmd:
        module.Distribution = setuptools.dist.Distribution

    # Install the patched Extension
    distutils.core.Extension = setuptools.extension.Extension
    distutils.extension.Extension = setuptools.extension.Extension
    if 'distutils.command.build_ext' in sys.modules:
        sys.modules['distutils.command.build_ext'].Extension = (
            setuptools.extension.Extension
        )

    patch_for_msvc_specialized_compiler()


def _patch_distribution_metadata():
    """Patch write_pkg_file and read_pkg_file for higher metadata standards"""
    for attr in ('write_pkg_file', 'read_pkg_file', 'get_metadata_version'):
        new_val = getattr(setuptools.dist, attr)
        setattr(distutils.dist.DistributionMetadata, attr, new_val)


def patch_func(replacement, target_mod, func_name):
    """
    Patch func_name in target_mod with replacement

    Important - original must be resolved by name to avoid
    patching an already patched function.
    """
    original = getattr(target_mod, func_name)

    # set the 'unpatched' attribute on the replacement to
    # point to the original.
    vars(replacement).setdefault('unpatched', original)

    # replace the function in the original module
    setattr(target_mod, func_name, replacement)


def get_unpatched_function(candidate):
    return getattr(candidate, 'unpatched')


def patch_for_msvc_specialized_compiler():
    """
    Patch functions in distutils to use standalone Microsoft Visual C++
    compilers.
    """
    # import late to avoid circular imports on Python < 3.5
    msvc = import_module('setuptools.msvc')

    if platform.system() != 'Windows':
        # Compilers only available on Microsoft Windows
        return

    def patch_params(mod_name, func_name):
        """
        Prepare the parameters for patch_func to patch indicated function.
        """
        repl_prefix = 'msvc9_' if 'msvc9' in mod_name else 'msvc14_'
        repl_name = repl_prefix + func_name.lstrip('_')
        repl = getattr(msvc, repl_name)
        mod = import_module(mod_name)
        if not hasattr(mod, func_name):
            raise ImportError(func_name)
        return repl, mod, func_name

    # Python 2.7 to 3.4
    msvc9 = functools.partial(patch_params, 'distutils.msvc9compiler')

    # Python 3.5+
    msvc14 = functools.partial(patch_params, 'distutils._msvccompiler')

    try:
        # Patch distutils.msvc9compiler
        patch_func(*msvc9('find_vcvarsall'))
        patch_func(*msvc9('query_vcvarsall'))
    except ImportError:
        pass

    try:
        # Patch distutils._msvccompiler._get_vc_env
        patch_func(*msvc14('_get_vc_env'))
    except ImportError:
        pass

    try:
        # Patch distutils._msvccompiler.gen_lib_options for Numpy
        patch_func(*msvc14('gen_lib_options'))
    except ImportError:
        pass

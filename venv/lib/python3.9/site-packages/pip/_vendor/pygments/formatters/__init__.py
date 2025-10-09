"""
    pygments.formatters
    ~~~~~~~~~~~~~~~~~~~

    Pygments formatters.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import sys
import types
import fnmatch
from os.path import basename

from pip._vendor.pygments.formatters._mapping import FORMATTERS
from pip._vendor.pygments.plugin import find_plugin_formatters
from pip._vendor.pygments.util import ClassNotFound

__all__ = ['get_formatter_by_name', 'get_formatter_for_filename',
           'get_all_formatters', 'load_formatter_from_file'] + list(FORMATTERS)

_formatter_cache = {}  # classes by name
_pattern_cache = {}


def _fn_matches(fn, glob):
    """Return whether the supplied file name fn matches pattern filename."""
    if glob not in _pattern_cache:
        pattern = _pattern_cache[glob] = re.compile(fnmatch.translate(glob))
        return pattern.match(fn)
    return _pattern_cache[glob].match(fn)


def _load_formatters(module_name):
    """Load a formatter (and all others in the module too)."""
    mod = __import__(module_name, None, None, ['__all__'])
    for formatter_name in mod.__all__:
        cls = getattr(mod, formatter_name)
        _formatter_cache[cls.name] = cls


def get_all_formatters():
    """Return a generator for all formatter classes."""
    # NB: this returns formatter classes, not info like get_all_lexers().
    for info in FORMATTERS.values():
        if info[1] not in _formatter_cache:
            _load_formatters(info[0])
        yield _formatter_cache[info[1]]
    for _, formatter in find_plugin_formatters():
        yield formatter


def find_formatter_class(alias):
    """Lookup a formatter by alias.

    Returns None if not found.
    """
    for module_name, name, aliases, _, _ in FORMATTERS.values():
        if alias in aliases:
            if name not in _formatter_cache:
                _load_formatters(module_name)
            return _formatter_cache[name]
    for _, cls in find_plugin_formatters():
        if alias in cls.aliases:
            return cls


def get_formatter_by_name(_alias, **options):
    """
    Return an instance of a :class:`.Formatter` subclass that has `alias` in its
    aliases list. The formatter is given the `options` at its instantiation.

    Will raise :exc:`pygments.util.ClassNotFound` if no formatter with that
    alias is found.
    """
    cls = find_formatter_class(_alias)
    if cls is None:
        raise ClassNotFound(f"no formatter found for name {_alias!r}")
    return cls(**options)


def load_formatter_from_file(filename, formattername="CustomFormatter", **options):
    """
    Return a `Formatter` subclass instance loaded from the provided file, relative
    to the current directory.

    The file is expected to contain a Formatter class named ``formattername``
    (by default, CustomFormatter). Users should be very careful with the input, because
    this method is equivalent to running ``eval()`` on the input file. The formatter is
    given the `options` at its instantiation.

    :exc:`pygments.util.ClassNotFound` is raised if there are any errors loading
    the formatter.

    .. versionadded:: 2.2
    """
    try:
        # This empty dict will contain the namespace for the exec'd file
        custom_namespace = {}
        with open(filename, 'rb') as f:
            exec(f.read(), custom_namespace)
        # Retrieve the class `formattername` from that namespace
        if formattername not in custom_namespace:
            raise ClassNotFound(f'no valid {formattername} class found in {filename}')
        formatter_class = custom_namespace[formattername]
        # And finally instantiate it with the options
        return formatter_class(**options)
    except OSError as err:
        raise ClassNotFound(f'cannot read {filename}: {err}')
    except ClassNotFound:
        raise
    except Exception as err:
        raise ClassNotFound(f'error when loading custom formatter: {err}')


def get_formatter_for_filename(fn, **options):
    """
    Return a :class:`.Formatter` subclass instance that has a filename pattern
    matching `fn`. The formatter is given the `options` at its instantiation.

    Will raise :exc:`pygments.util.ClassNotFound` if no formatter for that filename
    is found.
    """
    fn = basename(fn)
    for modname, name, _, filenames, _ in FORMATTERS.values():
        for filename in filenames:
            if _fn_matches(fn, filename):
                if name not in _formatter_cache:
                    _load_formatters(modname)
                return _formatter_cache[name](**options)
    for _name, cls in find_plugin_formatters():
        for filename in cls.filenames:
            if _fn_matches(fn, filename):
                return cls(**options)
    raise ClassNotFound(f"no formatter found for file name {fn!r}")


class _automodule(types.ModuleType):
    """Automatically import formatters."""

    def __getattr__(self, name):
        info = FORMATTERS.get(name)
        if info:
            _load_formatters(info[0])
            cls = _formatter_cache[info[1]]
            setattr(self, name, cls)
            return cls
        raise AttributeError(name)


oldmod = sys.modules[__name__]
newmod = _automodule(__name__)
newmod.__dict__.update(oldmod.__dict__)
sys.modules[__name__] = newmod
del newmod.newmod, newmod.oldmod, newmod.sys, newmod.types

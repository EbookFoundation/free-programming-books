"""
    pygments.lexers
    ~~~~~~~~~~~~~~~

    Pygments lexers.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import sys
import types
import fnmatch
from os.path import basename

from pip._vendor.pygments.lexers._mapping import LEXERS
from pip._vendor.pygments.modeline import get_filetype_from_buffer
from pip._vendor.pygments.plugin import find_plugin_lexers
from pip._vendor.pygments.util import ClassNotFound, guess_decode

COMPAT = {
    'Python3Lexer': 'PythonLexer',
    'Python3TracebackLexer': 'PythonTracebackLexer',
    'LeanLexer': 'Lean3Lexer',
}

__all__ = ['get_lexer_by_name', 'get_lexer_for_filename', 'find_lexer_class',
           'guess_lexer', 'load_lexer_from_file'] + list(LEXERS) + list(COMPAT)

_lexer_cache = {}
_pattern_cache = {}


def _fn_matches(fn, glob):
    """Return whether the supplied file name fn matches pattern filename."""
    if glob not in _pattern_cache:
        pattern = _pattern_cache[glob] = re.compile(fnmatch.translate(glob))
        return pattern.match(fn)
    return _pattern_cache[glob].match(fn)


def _load_lexers(module_name):
    """Load a lexer (and all others in the module too)."""
    mod = __import__(module_name, None, None, ['__all__'])
    for lexer_name in mod.__all__:
        cls = getattr(mod, lexer_name)
        _lexer_cache[cls.name] = cls


def get_all_lexers(plugins=True):
    """Return a generator of tuples in the form ``(name, aliases,
    filenames, mimetypes)`` of all know lexers.

    If *plugins* is true (the default), plugin lexers supplied by entrypoints
    are also returned.  Otherwise, only builtin ones are considered.
    """
    for item in LEXERS.values():
        yield item[1:]
    if plugins:
        for lexer in find_plugin_lexers():
            yield lexer.name, lexer.aliases, lexer.filenames, lexer.mimetypes


def find_lexer_class(name):
    """
    Return the `Lexer` subclass that with the *name* attribute as given by
    the *name* argument.
    """
    if name in _lexer_cache:
        return _lexer_cache[name]
    # lookup builtin lexers
    for module_name, lname, aliases, _, _ in LEXERS.values():
        if name == lname:
            _load_lexers(module_name)
            return _lexer_cache[name]
    # continue with lexers from setuptools entrypoints
    for cls in find_plugin_lexers():
        if cls.name == name:
            return cls


def find_lexer_class_by_name(_alias):
    """
    Return the `Lexer` subclass that has `alias` in its aliases list, without
    instantiating it.

    Like `get_lexer_by_name`, but does not instantiate the class.

    Will raise :exc:`pygments.util.ClassNotFound` if no lexer with that alias is
    found.

    .. versionadded:: 2.2
    """
    if not _alias:
        raise ClassNotFound(f'no lexer for alias {_alias!r} found')
    # lookup builtin lexers
    for module_name, name, aliases, _, _ in LEXERS.values():
        if _alias.lower() in aliases:
            if name not in _lexer_cache:
                _load_lexers(module_name)
            return _lexer_cache[name]
    # continue with lexers from setuptools entrypoints
    for cls in find_plugin_lexers():
        if _alias.lower() in cls.aliases:
            return cls
    raise ClassNotFound(f'no lexer for alias {_alias!r} found')


def get_lexer_by_name(_alias, **options):
    """
    Return an instance of a `Lexer` subclass that has `alias` in its
    aliases list. The lexer is given the `options` at its
    instantiation.

    Will raise :exc:`pygments.util.ClassNotFound` if no lexer with that alias is
    found.
    """
    if not _alias:
        raise ClassNotFound(f'no lexer for alias {_alias!r} found')

    # lookup builtin lexers
    for module_name, name, aliases, _, _ in LEXERS.values():
        if _alias.lower() in aliases:
            if name not in _lexer_cache:
                _load_lexers(module_name)
            return _lexer_cache[name](**options)
    # continue with lexers from setuptools entrypoints
    for cls in find_plugin_lexers():
        if _alias.lower() in cls.aliases:
            return cls(**options)
    raise ClassNotFound(f'no lexer for alias {_alias!r} found')


def load_lexer_from_file(filename, lexername="CustomLexer", **options):
    """Load a lexer from a file.

    This method expects a file located relative to the current working
    directory, which contains a Lexer class. By default, it expects the
    Lexer to be name CustomLexer; you can specify your own class name
    as the second argument to this function.

    Users should be very careful with the input, because this method
    is equivalent to running eval on the input file.

    Raises ClassNotFound if there are any problems importing the Lexer.

    .. versionadded:: 2.2
    """
    try:
        # This empty dict will contain the namespace for the exec'd file
        custom_namespace = {}
        with open(filename, 'rb') as f:
            exec(f.read(), custom_namespace)
        # Retrieve the class `lexername` from that namespace
        if lexername not in custom_namespace:
            raise ClassNotFound(f'no valid {lexername} class found in {filename}')
        lexer_class = custom_namespace[lexername]
        # And finally instantiate it with the options
        return lexer_class(**options)
    except OSError as err:
        raise ClassNotFound(f'cannot read {filename}: {err}')
    except ClassNotFound:
        raise
    except Exception as err:
        raise ClassNotFound(f'error when loading custom lexer: {err}')


def find_lexer_class_for_filename(_fn, code=None):
    """Get a lexer for a filename.

    If multiple lexers match the filename pattern, use ``analyse_text()`` to
    figure out which one is more appropriate.

    Returns None if not found.
    """
    matches = []
    fn = basename(_fn)
    for modname, name, _, filenames, _ in LEXERS.values():
        for filename in filenames:
            if _fn_matches(fn, filename):
                if name not in _lexer_cache:
                    _load_lexers(modname)
                matches.append((_lexer_cache[name], filename))
    for cls in find_plugin_lexers():
        for filename in cls.filenames:
            if _fn_matches(fn, filename):
                matches.append((cls, filename))

    if isinstance(code, bytes):
        # decode it, since all analyse_text functions expect unicode
        code = guess_decode(code)

    def get_rating(info):
        cls, filename = info
        # explicit patterns get a bonus
        bonus = '*' not in filename and 0.5 or 0
        # The class _always_ defines analyse_text because it's included in
        # the Lexer class.  The default implementation returns None which
        # gets turned into 0.0.  Run scripts/detect_missing_analyse_text.py
        # to find lexers which need it overridden.
        if code:
            return cls.analyse_text(code) + bonus, cls.__name__
        return cls.priority + bonus, cls.__name__

    if matches:
        matches.sort(key=get_rating)
        # print "Possible lexers, after sort:", matches
        return matches[-1][0]


def get_lexer_for_filename(_fn, code=None, **options):
    """Get a lexer for a filename.

    Return a `Lexer` subclass instance that has a filename pattern
    matching `fn`. The lexer is given the `options` at its
    instantiation.

    Raise :exc:`pygments.util.ClassNotFound` if no lexer for that filename
    is found.

    If multiple lexers match the filename pattern, use their ``analyse_text()``
    methods to figure out which one is more appropriate.
    """
    res = find_lexer_class_for_filename(_fn, code)
    if not res:
        raise ClassNotFound(f'no lexer for filename {_fn!r} found')
    return res(**options)


def get_lexer_for_mimetype(_mime, **options):
    """
    Return a `Lexer` subclass instance that has `mime` in its mimetype
    list. The lexer is given the `options` at its instantiation.

    Will raise :exc:`pygments.util.ClassNotFound` if not lexer for that mimetype
    is found.
    """
    for modname, name, _, _, mimetypes in LEXERS.values():
        if _mime in mimetypes:
            if name not in _lexer_cache:
                _load_lexers(modname)
            return _lexer_cache[name](**options)
    for cls in find_plugin_lexers():
        if _mime in cls.mimetypes:
            return cls(**options)
    raise ClassNotFound(f'no lexer for mimetype {_mime!r} found')


def _iter_lexerclasses(plugins=True):
    """Return an iterator over all lexer classes."""
    for key in sorted(LEXERS):
        module_name, name = LEXERS[key][:2]
        if name not in _lexer_cache:
            _load_lexers(module_name)
        yield _lexer_cache[name]
    if plugins:
        yield from find_plugin_lexers()


def guess_lexer_for_filename(_fn, _text, **options):
    """
    As :func:`guess_lexer()`, but only lexers which have a pattern in `filenames`
    or `alias_filenames` that matches `filename` are taken into consideration.

    :exc:`pygments.util.ClassNotFound` is raised if no lexer thinks it can
    handle the content.
    """
    fn = basename(_fn)
    primary = {}
    matching_lexers = set()
    for lexer in _iter_lexerclasses():
        for filename in lexer.filenames:
            if _fn_matches(fn, filename):
                matching_lexers.add(lexer)
                primary[lexer] = True
        for filename in lexer.alias_filenames:
            if _fn_matches(fn, filename):
                matching_lexers.add(lexer)
                primary[lexer] = False
    if not matching_lexers:
        raise ClassNotFound(f'no lexer for filename {fn!r} found')
    if len(matching_lexers) == 1:
        return matching_lexers.pop()(**options)
    result = []
    for lexer in matching_lexers:
        rv = lexer.analyse_text(_text)
        if rv == 1.0:
            return lexer(**options)
        result.append((rv, lexer))

    def type_sort(t):
        # sort by:
        # - analyse score
        # - is primary filename pattern?
        # - priority
        # - last resort: class name
        return (t[0], primary[t[1]], t[1].priority, t[1].__name__)
    result.sort(key=type_sort)

    return result[-1][1](**options)


def guess_lexer(_text, **options):
    """
    Return a `Lexer` subclass instance that's guessed from the text in
    `text`. For that, the :meth:`.analyse_text()` method of every known lexer
    class is called with the text as argument, and the lexer which returned the
    highest value will be instantiated and returned.

    :exc:`pygments.util.ClassNotFound` is raised if no lexer thinks it can
    handle the content.
    """

    if not isinstance(_text, str):
        inencoding = options.get('inencoding', options.get('encoding'))
        if inencoding:
            _text = _text.decode(inencoding or 'utf8')
        else:
            _text, _ = guess_decode(_text)

    # try to get a vim modeline first
    ft = get_filetype_from_buffer(_text)

    if ft is not None:
        try:
            return get_lexer_by_name(ft, **options)
        except ClassNotFound:
            pass

    best_lexer = [0.0, None]
    for lexer in _iter_lexerclasses():
        rv = lexer.analyse_text(_text)
        if rv == 1.0:
            return lexer(**options)
        if rv > best_lexer[0]:
            best_lexer[:] = (rv, lexer)
    if not best_lexer[0] or best_lexer[1] is None:
        raise ClassNotFound('no lexer matching the text found')
    return best_lexer[1](**options)


class _automodule(types.ModuleType):
    """Automatically import lexers."""

    def __getattr__(self, name):
        info = LEXERS.get(name)
        if info:
            _load_lexers(info[0])
            cls = _lexer_cache[info[1]]
            setattr(self, name, cls)
            return cls
        if name in COMPAT:
            return getattr(self, COMPAT[name])
        raise AttributeError(name)


oldmod = sys.modules[__name__]
newmod = _automodule(__name__)
newmod.__dict__.update(oldmod.__dict__)
sys.modules[__name__] = newmod
del newmod.newmod, newmod.oldmod, newmod.sys, newmod.types

"""
Re-implementation of find_module and get_frozen_object
from the deprecated imp module.
"""

import os
import importlib.util
import importlib.machinery

from .py34compat import module_from_spec


PY_SOURCE = 1
PY_COMPILED = 2
C_EXTENSION = 3
C_BUILTIN = 6
PY_FROZEN = 7


def find_spec(module, paths):
    finder = (
        importlib.machinery.PathFinder().find_spec
        if isinstance(paths, list) else
        importlib.util.find_spec
    )
    return finder(module, paths)


def find_module(module, paths=None):
    """Just like 'imp.find_module()', but with package support"""
    spec = find_spec(module, paths)
    if spec is None:
        raise ImportError("Can't find %s" % module)
    if not spec.has_location and hasattr(spec, 'submodule_search_locations'):
        spec = importlib.util.spec_from_loader('__init__.py', spec.loader)

    kind = -1
    file = None
    static = isinstance(spec.loader, type)
    if spec.origin == 'frozen' or static and issubclass(
            spec.loader, importlib.machinery.FrozenImporter):
        kind = PY_FROZEN
        path = None  # imp compabilty
        suffix = mode = ''  # imp compatibility
    elif spec.origin == 'built-in' or static and issubclass(
            spec.loader, importlib.machinery.BuiltinImporter):
        kind = C_BUILTIN
        path = None  # imp compabilty
        suffix = mode = ''  # imp compatibility
    elif spec.has_location:
        path = spec.origin
        suffix = os.path.splitext(path)[1]
        mode = 'r' if suffix in importlib.machinery.SOURCE_SUFFIXES else 'rb'

        if suffix in importlib.machinery.SOURCE_SUFFIXES:
            kind = PY_SOURCE
        elif suffix in importlib.machinery.BYTECODE_SUFFIXES:
            kind = PY_COMPILED
        elif suffix in importlib.machinery.EXTENSION_SUFFIXES:
            kind = C_EXTENSION

        if kind in {PY_SOURCE, PY_COMPILED}:
            file = open(path, mode)
    else:
        path = None
        suffix = mode = ''

    return file, path, (suffix, mode, kind)


def get_frozen_object(module, paths=None):
    spec = find_spec(module, paths)
    if not spec:
        raise ImportError("Can't find %s" % module)
    return spec.loader.get_code(module)


def get_module(module, paths, info):
    spec = find_spec(module, paths)
    if not spec:
        raise ImportError("Can't find %s" % module)
    return module_from_spec(spec)

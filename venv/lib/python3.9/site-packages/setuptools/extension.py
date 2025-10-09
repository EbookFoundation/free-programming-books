import re
import functools
import distutils.core
import distutils.errors
import distutils.extension

from .monkey import get_unpatched


def _have_cython():
    """
    Return True if Cython can be imported.
    """
    cython_impl = 'Cython.Distutils.build_ext'
    try:
        # from (cython_impl) import build_ext
        __import__(cython_impl, fromlist=['build_ext']).build_ext
        return True
    except Exception:
        pass
    return False


# for compatibility
have_pyrex = _have_cython

_Extension = get_unpatched(distutils.core.Extension)


class Extension(_Extension):
    """Extension that uses '.c' files in place of '.pyx' files"""

    def __init__(self, name, sources, *args, **kw):
        # The *args is needed for compatibility as calls may use positional
        # arguments. py_limited_api may be set only via keyword.
        self.py_limited_api = kw.pop("py_limited_api", False)
        _Extension.__init__(self, name, sources, *args, **kw)

    def _convert_pyx_sources_to_lang(self):
        """
        Replace sources with .pyx extensions to sources with the target
        language extension. This mechanism allows language authors to supply
        pre-converted sources but to prefer the .pyx sources.
        """
        if _have_cython():
            # the build has Cython, so allow it to compile the .pyx files
            return
        lang = self.language or ''
        target_ext = '.cpp' if lang.lower() == 'c++' else '.c'
        sub = functools.partial(re.sub, '.pyx$', target_ext)
        self.sources = list(map(sub, self.sources))


class Library(Extension):
    """Just like a regular Extension, but built as a library instead"""

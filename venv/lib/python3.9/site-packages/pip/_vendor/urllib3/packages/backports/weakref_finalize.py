# -*- coding: utf-8 -*-
"""
backports.weakref_finalize
~~~~~~~~~~~~~~~~~~

Backports the Python 3 ``weakref.finalize`` method.
"""
from __future__ import absolute_import

import itertools
import sys
from weakref import ref

__all__ = ["weakref_finalize"]


class weakref_finalize(object):
    """Class for finalization of weakrefable objects
    finalize(obj, func, *args, **kwargs) returns a callable finalizer
    object which will be called when obj is garbage collected. The
    first time the finalizer is called it evaluates func(*arg, **kwargs)
    and returns the result. After this the finalizer is dead, and
    calling it just returns None.
    When the program exits any remaining finalizers for which the
    atexit attribute is true will be run in reverse order of creation.
    By default atexit is true.
    """

    # Finalizer objects don't have any state of their own.  They are
    # just used as keys to lookup _Info objects in the registry.  This
    # ensures that they cannot be part of a ref-cycle.

    __slots__ = ()
    _registry = {}
    _shutdown = False
    _index_iter = itertools.count()
    _dirty = False
    _registered_with_atexit = False

    class _Info(object):
        __slots__ = ("weakref", "func", "args", "kwargs", "atexit", "index")

    def __init__(self, obj, func, *args, **kwargs):
        if not self._registered_with_atexit:
            # We may register the exit function more than once because
            # of a thread race, but that is harmless
            import atexit

            atexit.register(self._exitfunc)
            weakref_finalize._registered_with_atexit = True
        info = self._Info()
        info.weakref = ref(obj, self)
        info.func = func
        info.args = args
        info.kwargs = kwargs or None
        info.atexit = True
        info.index = next(self._index_iter)
        self._registry[self] = info
        weakref_finalize._dirty = True

    def __call__(self, _=None):
        """If alive then mark as dead and return func(*args, **kwargs);
        otherwise return None"""
        info = self._registry.pop(self, None)
        if info and not self._shutdown:
            return info.func(*info.args, **(info.kwargs or {}))

    def detach(self):
        """If alive then mark as dead and return (obj, func, args, kwargs);
        otherwise return None"""
        info = self._registry.get(self)
        obj = info and info.weakref()
        if obj is not None and self._registry.pop(self, None):
            return (obj, info.func, info.args, info.kwargs or {})

    def peek(self):
        """If alive then return (obj, func, args, kwargs);
        otherwise return None"""
        info = self._registry.get(self)
        obj = info and info.weakref()
        if obj is not None:
            return (obj, info.func, info.args, info.kwargs or {})

    @property
    def alive(self):
        """Whether finalizer is alive"""
        return self in self._registry

    @property
    def atexit(self):
        """Whether finalizer should be called at exit"""
        info = self._registry.get(self)
        return bool(info) and info.atexit

    @atexit.setter
    def atexit(self, value):
        info = self._registry.get(self)
        if info:
            info.atexit = bool(value)

    def __repr__(self):
        info = self._registry.get(self)
        obj = info and info.weakref()
        if obj is None:
            return "<%s object at %#x; dead>" % (type(self).__name__, id(self))
        else:
            return "<%s object at %#x; for %r at %#x>" % (
                type(self).__name__,
                id(self),
                type(obj).__name__,
                id(obj),
            )

    @classmethod
    def _select_for_exit(cls):
        # Return live finalizers marked for exit, oldest first
        L = [(f, i) for (f, i) in cls._registry.items() if i.atexit]
        L.sort(key=lambda item: item[1].index)
        return [f for (f, i) in L]

    @classmethod
    def _exitfunc(cls):
        # At shutdown invoke finalizers for which atexit is true.
        # This is called once all other non-daemonic threads have been
        # joined.
        reenable_gc = False
        try:
            if cls._registry:
                import gc

                if gc.isenabled():
                    reenable_gc = True
                    gc.disable()
                pending = None
                while True:
                    if pending is None or weakref_finalize._dirty:
                        pending = cls._select_for_exit()
                        weakref_finalize._dirty = False
                    if not pending:
                        break
                    f = pending.pop()
                    try:
                        # gc is disabled, so (assuming no daemonic
                        # threads) the following is the only line in
                        # this function which might trigger creation
                        # of a new finalizer
                        f()
                    except Exception:
                        sys.excepthook(*sys.exc_info())
                    assert f not in cls._registry
        finally:
            # prevent any more finalizers from executing during shutdown
            weakref_finalize._shutdown = True
            if reenable_gc:
                gc.enable()

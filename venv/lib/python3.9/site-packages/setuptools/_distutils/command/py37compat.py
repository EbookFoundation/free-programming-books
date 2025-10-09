import sys


def _pythonlib_compat():
    """
    On Python 3.7 and earlier, distutils would include the Python
    library. See pypa/distutils#9.
    """
    from distutils import sysconfig
    if not sysconfig.get_config_var('Py_ENABLED_SHARED'):
        return

    yield 'python{}.{}{}'.format(
        sys.hexversion >> 24,
        (sys.hexversion >> 16) & 0xff,
        sysconfig.get_config_var('ABIFLAGS'),
    )


def compose(f1, f2):
    return lambda *args, **kwargs: f1(f2(*args, **kwargs))


pythonlib = (
    compose(list, _pythonlib_compat)
    if sys.version_info < (3, 8)
    and sys.platform != 'darwin'
    and sys.platform[:3] != 'aix'
    else list
)

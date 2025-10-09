import errno
import select
import sys
from functools import partial

try:
    from time import monotonic
except ImportError:
    from time import time as monotonic

__all__ = ["NoWayToWaitForSocketError", "wait_for_read", "wait_for_write"]


class NoWayToWaitForSocketError(Exception):
    pass


# How should we wait on sockets?
#
# There are two types of APIs you can use for waiting on sockets: the fancy
# modern stateful APIs like epoll/kqueue, and the older stateless APIs like
# select/poll. The stateful APIs are more efficient when you have a lots of
# sockets to keep track of, because you can set them up once and then use them
# lots of times. But we only ever want to wait on a single socket at a time
# and don't want to keep track of state, so the stateless APIs are actually
# more efficient. So we want to use select() or poll().
#
# Now, how do we choose between select() and poll()? On traditional Unixes,
# select() has a strange calling convention that makes it slow, or fail
# altogether, for high-numbered file descriptors. The point of poll() is to fix
# that, so on Unixes, we prefer poll().
#
# On Windows, there is no poll() (or at least Python doesn't provide a wrapper
# for it), but that's OK, because on Windows, select() doesn't have this
# strange calling convention; plain select() works fine.
#
# So: on Windows we use select(), and everywhere else we use poll(). We also
# fall back to select() in case poll() is somehow broken or missing.

if sys.version_info >= (3, 5):
    # Modern Python, that retries syscalls by default
    def _retry_on_intr(fn, timeout):
        return fn(timeout)

else:
    # Old and broken Pythons.
    def _retry_on_intr(fn, timeout):
        if timeout is None:
            deadline = float("inf")
        else:
            deadline = monotonic() + timeout

        while True:
            try:
                return fn(timeout)
            # OSError for 3 <= pyver < 3.5, select.error for pyver <= 2.7
            except (OSError, select.error) as e:
                # 'e.args[0]' incantation works for both OSError and select.error
                if e.args[0] != errno.EINTR:
                    raise
                else:
                    timeout = deadline - monotonic()
                    if timeout < 0:
                        timeout = 0
                    if timeout == float("inf"):
                        timeout = None
                    continue


def select_wait_for_socket(sock, read=False, write=False, timeout=None):
    if not read and not write:
        raise RuntimeError("must specify at least one of read=True, write=True")
    rcheck = []
    wcheck = []
    if read:
        rcheck.append(sock)
    if write:
        wcheck.append(sock)
    # When doing a non-blocking connect, most systems signal success by
    # marking the socket writable. Windows, though, signals success by marked
    # it as "exceptional". We paper over the difference by checking the write
    # sockets for both conditions. (The stdlib selectors module does the same
    # thing.)
    fn = partial(select.select, rcheck, wcheck, wcheck)
    rready, wready, xready = _retry_on_intr(fn, timeout)
    return bool(rready or wready or xready)


def poll_wait_for_socket(sock, read=False, write=False, timeout=None):
    if not read and not write:
        raise RuntimeError("must specify at least one of read=True, write=True")
    mask = 0
    if read:
        mask |= select.POLLIN
    if write:
        mask |= select.POLLOUT
    poll_obj = select.poll()
    poll_obj.register(sock, mask)

    # For some reason, poll() takes timeout in milliseconds
    def do_poll(t):
        if t is not None:
            t *= 1000
        return poll_obj.poll(t)

    return bool(_retry_on_intr(do_poll, timeout))


def null_wait_for_socket(*args, **kwargs):
    raise NoWayToWaitForSocketError("no select-equivalent available")


def _have_working_poll():
    # Apparently some systems have a select.poll that fails as soon as you try
    # to use it, either due to strange configuration or broken monkeypatching
    # from libraries like eventlet/greenlet.
    try:
        poll_obj = select.poll()
        _retry_on_intr(poll_obj.poll, 0)
    except (AttributeError, OSError):
        return False
    else:
        return True


def wait_for_socket(*args, **kwargs):
    # We delay choosing which implementation to use until the first time we're
    # called. We could do it at import time, but then we might make the wrong
    # decision if someone goes wild with monkeypatching select.poll after
    # we're imported.
    global wait_for_socket
    if _have_working_poll():
        wait_for_socket = poll_wait_for_socket
    elif hasattr(select, "select"):
        wait_for_socket = select_wait_for_socket
    else:  # Platform-specific: Appengine.
        wait_for_socket = null_wait_for_socket
    return wait_for_socket(*args, **kwargs)


def wait_for_read(sock, timeout=None):
    """Waits for reading to be available on a given socket.
    Returns True if the socket is readable, or False if the timeout expired.
    """
    return wait_for_socket(sock, read=True, timeout=timeout)


def wait_for_write(sock, timeout=None):
    """Waits for writing to be available on a given socket.
    Returns True if the socket is readable, or False if the timeout expired.
    """
    return wait_for_socket(sock, write=True, timeout=timeout)

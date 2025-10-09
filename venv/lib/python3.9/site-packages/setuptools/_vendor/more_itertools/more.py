import warnings

from collections import Counter, defaultdict, deque, abc
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from functools import partial, reduce, wraps
from heapq import merge, heapify, heapreplace, heappop
from itertools import (
    chain,
    compress,
    count,
    cycle,
    dropwhile,
    groupby,
    islice,
    repeat,
    starmap,
    takewhile,
    tee,
    zip_longest,
)
from math import exp, factorial, floor, log
from queue import Empty, Queue
from random import random, randrange, uniform
from operator import itemgetter, mul, sub, gt, lt
from sys import hexversion, maxsize
from time import monotonic

from .recipes import (
    consume,
    flatten,
    pairwise,
    powerset,
    take,
    unique_everseen,
)

__all__ = [
    'AbortThread',
    'adjacent',
    'always_iterable',
    'always_reversible',
    'bucket',
    'callback_iter',
    'chunked',
    'circular_shifts',
    'collapse',
    'collate',
    'consecutive_groups',
    'consumer',
    'countable',
    'count_cycle',
    'mark_ends',
    'difference',
    'distinct_combinations',
    'distinct_permutations',
    'distribute',
    'divide',
    'exactly_n',
    'filter_except',
    'first',
    'groupby_transform',
    'ilen',
    'interleave_longest',
    'interleave',
    'intersperse',
    'islice_extended',
    'iterate',
    'ichunked',
    'is_sorted',
    'last',
    'locate',
    'lstrip',
    'make_decorator',
    'map_except',
    'map_reduce',
    'nth_or_last',
    'nth_permutation',
    'nth_product',
    'numeric_range',
    'one',
    'only',
    'padded',
    'partitions',
    'set_partitions',
    'peekable',
    'repeat_last',
    'replace',
    'rlocate',
    'rstrip',
    'run_length',
    'sample',
    'seekable',
    'SequenceView',
    'side_effect',
    'sliced',
    'sort_together',
    'split_at',
    'split_after',
    'split_before',
    'split_when',
    'split_into',
    'spy',
    'stagger',
    'strip',
    'substrings',
    'substrings_indexes',
    'time_limited',
    'unique_to_each',
    'unzip',
    'windowed',
    'with_iter',
    'UnequalIterablesError',
    'zip_equal',
    'zip_offset',
    'windowed_complete',
    'all_unique',
    'value_chain',
    'product_index',
    'combination_index',
    'permutation_index',
]

_marker = object()


def chunked(iterable, n, strict=False):
    """Break *iterable* into lists of length *n*:

        >>> list(chunked([1, 2, 3, 4, 5, 6], 3))
        [[1, 2, 3], [4, 5, 6]]

    By the default, the last yielded list will have fewer than *n* elements
    if the length of *iterable* is not divisible by *n*:

        >>> list(chunked([1, 2, 3, 4, 5, 6, 7, 8], 3))
        [[1, 2, 3], [4, 5, 6], [7, 8]]

    To use a fill-in value instead, see the :func:`grouper` recipe.

    If the length of *iterable* is not divisible by *n* and *strict* is
    ``True``, then ``ValueError`` will be raised before the last
    list is yielded.

    """
    iterator = iter(partial(take, n, iter(iterable)), [])
    if strict:

        def ret():
            for chunk in iterator:
                if len(chunk) != n:
                    raise ValueError('iterable is not divisible by n.')
                yield chunk

        return iter(ret())
    else:
        return iterator


def first(iterable, default=_marker):
    """Return the first item of *iterable*, or *default* if *iterable* is
    empty.

        >>> first([0, 1, 2, 3])
        0
        >>> first([], 'some default')
        'some default'

    If *default* is not provided and there are no items in the iterable,
    raise ``ValueError``.

    :func:`first` is useful when you have a generator of expensive-to-retrieve
    values and want any arbitrary one. It is marginally shorter than
    ``next(iter(iterable), default)``.

    """
    try:
        return next(iter(iterable))
    except StopIteration as e:
        if default is _marker:
            raise ValueError(
                'first() was called on an empty iterable, and no '
                'default value was provided.'
            ) from e
        return default


def last(iterable, default=_marker):
    """Return the last item of *iterable*, or *default* if *iterable* is
    empty.

        >>> last([0, 1, 2, 3])
        3
        >>> last([], 'some default')
        'some default'

    If *default* is not provided and there are no items in the iterable,
    raise ``ValueError``.
    """
    try:
        if isinstance(iterable, Sequence):
            return iterable[-1]
        # Work around https://bugs.python.org/issue38525
        elif hasattr(iterable, '__reversed__') and (hexversion != 0x030800F0):
            return next(reversed(iterable))
        else:
            return deque(iterable, maxlen=1)[-1]
    except (IndexError, TypeError, StopIteration):
        if default is _marker:
            raise ValueError(
                'last() was called on an empty iterable, and no default was '
                'provided.'
            )
        return default


def nth_or_last(iterable, n, default=_marker):
    """Return the nth or the last item of *iterable*,
    or *default* if *iterable* is empty.

        >>> nth_or_last([0, 1, 2, 3], 2)
        2
        >>> nth_or_last([0, 1], 2)
        1
        >>> nth_or_last([], 0, 'some default')
        'some default'

    If *default* is not provided and there are no items in the iterable,
    raise ``ValueError``.
    """
    return last(islice(iterable, n + 1), default=default)


class peekable:
    """Wrap an iterator to allow lookahead and prepending elements.

    Call :meth:`peek` on the result to get the value that will be returned
    by :func:`next`. This won't advance the iterator:

        >>> p = peekable(['a', 'b'])
        >>> p.peek()
        'a'
        >>> next(p)
        'a'

    Pass :meth:`peek` a default value to return that instead of raising
    ``StopIteration`` when the iterator is exhausted.

        >>> p = peekable([])
        >>> p.peek('hi')
        'hi'

    peekables also offer a :meth:`prepend` method, which "inserts" items
    at the head of the iterable:

        >>> p = peekable([1, 2, 3])
        >>> p.prepend(10, 11, 12)
        >>> next(p)
        10
        >>> p.peek()
        11
        >>> list(p)
        [11, 12, 1, 2, 3]

    peekables can be indexed. Index 0 is the item that will be returned by
    :func:`next`, index 1 is the item after that, and so on:
    The values up to the given index will be cached.

        >>> p = peekable(['a', 'b', 'c', 'd'])
        >>> p[0]
        'a'
        >>> p[1]
        'b'
        >>> next(p)
        'a'

    Negative indexes are supported, but be aware that they will cache the
    remaining items in the source iterator, which may require significant
    storage.

    To check whether a peekable is exhausted, check its truth value:

        >>> p = peekable(['a', 'b'])
        >>> if p:  # peekable has items
        ...     list(p)
        ['a', 'b']
        >>> if not p:  # peekable is exhausted
        ...     list(p)
        []

    """

    def __init__(self, iterable):
        self._it = iter(iterable)
        self._cache = deque()

    def __iter__(self):
        return self

    def __bool__(self):
        try:
            self.peek()
        except StopIteration:
            return False
        return True

    def peek(self, default=_marker):
        """Return the item that will be next returned from ``next()``.

        Return ``default`` if there are no items left. If ``default`` is not
        provided, raise ``StopIteration``.

        """
        if not self._cache:
            try:
                self._cache.append(next(self._it))
            except StopIteration:
                if default is _marker:
                    raise
                return default
        return self._cache[0]

    def prepend(self, *items):
        """Stack up items to be the next ones returned from ``next()`` or
        ``self.peek()``. The items will be returned in
        first in, first out order::

            >>> p = peekable([1, 2, 3])
            >>> p.prepend(10, 11, 12)
            >>> next(p)
            10
            >>> list(p)
            [11, 12, 1, 2, 3]

        It is possible, by prepending items, to "resurrect" a peekable that
        previously raised ``StopIteration``.

            >>> p = peekable([])
            >>> next(p)
            Traceback (most recent call last):
              ...
            StopIteration
            >>> p.prepend(1)
            >>> next(p)
            1
            >>> next(p)
            Traceback (most recent call last):
              ...
            StopIteration

        """
        self._cache.extendleft(reversed(items))

    def __next__(self):
        if self._cache:
            return self._cache.popleft()

        return next(self._it)

    def _get_slice(self, index):
        # Normalize the slice's arguments
        step = 1 if (index.step is None) else index.step
        if step > 0:
            start = 0 if (index.start is None) else index.start
            stop = maxsize if (index.stop is None) else index.stop
        elif step < 0:
            start = -1 if (index.start is None) else index.start
            stop = (-maxsize - 1) if (index.stop is None) else index.stop
        else:
            raise ValueError('slice step cannot be zero')

        # If either the start or stop index is negative, we'll need to cache
        # the rest of the iterable in order to slice from the right side.
        if (start < 0) or (stop < 0):
            self._cache.extend(self._it)
        # Otherwise we'll need to find the rightmost index and cache to that
        # point.
        else:
            n = min(max(start, stop) + 1, maxsize)
            cache_len = len(self._cache)
            if n >= cache_len:
                self._cache.extend(islice(self._it, n - cache_len))

        return list(self._cache)[index]

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self._get_slice(index)

        cache_len = len(self._cache)
        if index < 0:
            self._cache.extend(self._it)
        elif index >= cache_len:
            self._cache.extend(islice(self._it, index + 1 - cache_len))

        return self._cache[index]


def collate(*iterables, **kwargs):
    """Return a sorted merge of the items from each of several already-sorted
    *iterables*.

        >>> list(collate('ACDZ', 'AZ', 'JKL'))
        ['A', 'A', 'C', 'D', 'J', 'K', 'L', 'Z', 'Z']

    Works lazily, keeping only the next value from each iterable in memory. Use
    :func:`collate` to, for example, perform a n-way mergesort of items that
    don't fit in memory.

    If a *key* function is specified, the iterables will be sorted according
    to its result:

        >>> key = lambda s: int(s)  # Sort by numeric value, not by string
        >>> list(collate(['1', '10'], ['2', '11'], key=key))
        ['1', '2', '10', '11']


    If the *iterables* are sorted in descending order, set *reverse* to
    ``True``:

        >>> list(collate([5, 3, 1], [4, 2, 0], reverse=True))
        [5, 4, 3, 2, 1, 0]

    If the elements of the passed-in iterables are out of order, you might get
    unexpected results.

    On Python 3.5+, this function is an alias for :func:`heapq.merge`.

    """
    warnings.warn(
        "collate is no longer part of more_itertools, use heapq.merge",
        DeprecationWarning,
    )
    return merge(*iterables, **kwargs)


def consumer(func):
    """Decorator that automatically advances a PEP-342-style "reverse iterator"
    to its first yield point so you don't have to call ``next()`` on it
    manually.

        >>> @consumer
        ... def tally():
        ...     i = 0
        ...     while True:
        ...         print('Thing number %s is %s.' % (i, (yield)))
        ...         i += 1
        ...
        >>> t = tally()
        >>> t.send('red')
        Thing number 0 is red.
        >>> t.send('fish')
        Thing number 1 is fish.

    Without the decorator, you would have to call ``next(t)`` before
    ``t.send()`` could be used.

    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        gen = func(*args, **kwargs)
        next(gen)
        return gen

    return wrapper


def ilen(iterable):
    """Return the number of items in *iterable*.

        >>> ilen(x for x in range(1000000) if x % 3 == 0)
        333334

    This consumes the iterable, so handle with care.

    """
    # This approach was selected because benchmarks showed it's likely the
    # fastest of the known implementations at the time of writing.
    # See GitHub tracker: #236, #230.
    counter = count()
    deque(zip(iterable, counter), maxlen=0)
    return next(counter)


def iterate(func, start):
    """Return ``start``, ``func(start)``, ``func(func(start))``, ...

    >>> from itertools import islice
    >>> list(islice(iterate(lambda x: 2*x, 1), 10))
    [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

    """
    while True:
        yield start
        start = func(start)


def with_iter(context_manager):
    """Wrap an iterable in a ``with`` statement, so it closes once exhausted.

    For example, this will close the file when the iterator is exhausted::

        upper_lines = (line.upper() for line in with_iter(open('foo')))

    Any context manager which returns an iterable is a candidate for
    ``with_iter``.

    """
    with context_manager as iterable:
        yield from iterable


def one(iterable, too_short=None, too_long=None):
    """Return the first item from *iterable*, which is expected to contain only
    that item. Raise an exception if *iterable* is empty or has more than one
    item.

    :func:`one` is useful for ensuring that an iterable contains only one item.
    For example, it can be used to retrieve the result of a database query
    that is expected to return a single row.

    If *iterable* is empty, ``ValueError`` will be raised. You may specify a
    different exception with the *too_short* keyword:

        >>> it = []
        >>> one(it)  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        ValueError: too many items in iterable (expected 1)'
        >>> too_short = IndexError('too few items')
        >>> one(it, too_short=too_short)  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        IndexError: too few items

    Similarly, if *iterable* contains more than one item, ``ValueError`` will
    be raised. You may specify a different exception with the *too_long*
    keyword:

        >>> it = ['too', 'many']
        >>> one(it)  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        ValueError: Expected exactly one item in iterable, but got 'too',
        'many', and perhaps more.
        >>> too_long = RuntimeError
        >>> one(it, too_long=too_long)  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        RuntimeError

    Note that :func:`one` attempts to advance *iterable* twice to ensure there
    is only one item. See :func:`spy` or :func:`peekable` to check iterable
    contents less destructively.

    """
    it = iter(iterable)

    try:
        first_value = next(it)
    except StopIteration as e:
        raise (
            too_short or ValueError('too few items in iterable (expected 1)')
        ) from e

    try:
        second_value = next(it)
    except StopIteration:
        pass
    else:
        msg = (
            'Expected exactly one item in iterable, but got {!r}, {!r}, '
            'and perhaps more.'.format(first_value, second_value)
        )
        raise too_long or ValueError(msg)

    return first_value


def distinct_permutations(iterable, r=None):
    """Yield successive distinct permutations of the elements in *iterable*.

        >>> sorted(distinct_permutations([1, 0, 1]))
        [(0, 1, 1), (1, 0, 1), (1, 1, 0)]

    Equivalent to ``set(permutations(iterable))``, except duplicates are not
    generated and thrown away. For larger input sequences this is much more
    efficient.

    Duplicate permutations arise when there are duplicated elements in the
    input iterable. The number of items returned is
    `n! / (x_1! * x_2! * ... * x_n!)`, where `n` is the total number of
    items input, and each `x_i` is the count of a distinct item in the input
    sequence.

    If *r* is given, only the *r*-length permutations are yielded.

        >>> sorted(distinct_permutations([1, 0, 1], r=2))
        [(0, 1), (1, 0), (1, 1)]
        >>> sorted(distinct_permutations(range(3), r=2))
        [(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)]

    """
    # Algorithm: https://w.wiki/Qai
    def _full(A):
        while True:
            # Yield the permutation we have
            yield tuple(A)

            # Find the largest index i such that A[i] < A[i + 1]
            for i in range(size - 2, -1, -1):
                if A[i] < A[i + 1]:
                    break
            #  If no such index exists, this permutation is the last one
            else:
                return

            # Find the largest index j greater than j such that A[i] < A[j]
            for j in range(size - 1, i, -1):
                if A[i] < A[j]:
                    break

            # Swap the value of A[i] with that of A[j], then reverse the
            # sequence from A[i + 1] to form the new permutation
            A[i], A[j] = A[j], A[i]
            A[i + 1 :] = A[: i - size : -1]  # A[i + 1:][::-1]

    # Algorithm: modified from the above
    def _partial(A, r):
        # Split A into the first r items and the last r items
        head, tail = A[:r], A[r:]
        right_head_indexes = range(r - 1, -1, -1)
        left_tail_indexes = range(len(tail))

        while True:
            # Yield the permutation we have
            yield tuple(head)

            # Starting from the right, find the first index of the head with
            # value smaller than the maximum value of the tail - call it i.
            pivot = tail[-1]
            for i in right_head_indexes:
                if head[i] < pivot:
                    break
                pivot = head[i]
            else:
                return

            # Starting from the left, find the first value of the tail
            # with a value greater than head[i] and swap.
            for j in left_tail_indexes:
                if tail[j] > head[i]:
                    head[i], tail[j] = tail[j], head[i]
                    break
            # If we didn't find one, start from the right and find the first
            # index of the head with a value greater than head[i] and swap.
            else:
                for j in right_head_indexes:
                    if head[j] > head[i]:
                        head[i], head[j] = head[j], head[i]
                        break

            # Reverse head[i + 1:] and swap it with tail[:r - (i + 1)]
            tail += head[: i - r : -1]  # head[i + 1:][::-1]
            i += 1
            head[i:], tail[:] = tail[: r - i], tail[r - i :]

    items = sorted(iterable)

    size = len(items)
    if r is None:
        r = size

    if 0 < r <= size:
        return _full(items) if (r == size) else _partial(items, r)

    return iter(() if r else ((),))


def intersperse(e, iterable, n=1):
    """Intersperse filler element *e* among the items in *iterable*, leaving
    *n* items between each filler element.

        >>> list(intersperse('!', [1, 2, 3, 4, 5]))
        [1, '!', 2, '!', 3, '!', 4, '!', 5]

        >>> list(intersperse(None, [1, 2, 3, 4, 5], n=2))
        [1, 2, None, 3, 4, None, 5]

    """
    if n == 0:
        raise ValueError('n must be > 0')
    elif n == 1:
        # interleave(repeat(e), iterable) -> e, x_0, e, e, x_1, e, x_2...
        # islice(..., 1, None) -> x_0, e, e, x_1, e, x_2...
        return islice(interleave(repeat(e), iterable), 1, None)
    else:
        # interleave(filler, chunks) -> [e], [x_0, x_1], [e], [x_2, x_3]...
        # islice(..., 1, None) -> [x_0, x_1], [e], [x_2, x_3]...
        # flatten(...) -> x_0, x_1, e, x_2, x_3...
        filler = repeat([e])
        chunks = chunked(iterable, n)
        return flatten(islice(interleave(filler, chunks), 1, None))


def unique_to_each(*iterables):
    """Return the elements from each of the input iterables that aren't in the
    other input iterables.

    For example, suppose you have a set of packages, each with a set of
    dependencies::

        {'pkg_1': {'A', 'B'}, 'pkg_2': {'B', 'C'}, 'pkg_3': {'B', 'D'}}

    If you remove one package, which dependencies can also be removed?

    If ``pkg_1`` is removed, then ``A`` is no longer necessary - it is not
    associated with ``pkg_2`` or ``pkg_3``. Similarly, ``C`` is only needed for
    ``pkg_2``, and ``D`` is only needed for ``pkg_3``::

        >>> unique_to_each({'A', 'B'}, {'B', 'C'}, {'B', 'D'})
        [['A'], ['C'], ['D']]

    If there are duplicates in one input iterable that aren't in the others
    they will be duplicated in the output. Input order is preserved::

        >>> unique_to_each("mississippi", "missouri")
        [['p', 'p'], ['o', 'u', 'r']]

    It is assumed that the elements of each iterable are hashable.

    """
    pool = [list(it) for it in iterables]
    counts = Counter(chain.from_iterable(map(set, pool)))
    uniques = {element for element in counts if counts[element] == 1}
    return [list(filter(uniques.__contains__, it)) for it in pool]


def windowed(seq, n, fillvalue=None, step=1):
    """Return a sliding window of width *n* over the given iterable.

        >>> all_windows = windowed([1, 2, 3, 4, 5], 3)
        >>> list(all_windows)
        [(1, 2, 3), (2, 3, 4), (3, 4, 5)]

    When the window is larger than the iterable, *fillvalue* is used in place
    of missing values:

        >>> list(windowed([1, 2, 3], 4))
        [(1, 2, 3, None)]

    Each window will advance in increments of *step*:

        >>> list(windowed([1, 2, 3, 4, 5, 6], 3, fillvalue='!', step=2))
        [(1, 2, 3), (3, 4, 5), (5, 6, '!')]

    To slide into the iterable's items, use :func:`chain` to add filler items
    to the left:

        >>> iterable = [1, 2, 3, 4]
        >>> n = 3
        >>> padding = [None] * (n - 1)
        >>> list(windowed(chain(padding, iterable), 3))
        [(None, None, 1), (None, 1, 2), (1, 2, 3), (2, 3, 4)]
    """
    if n < 0:
        raise ValueError('n must be >= 0')
    if n == 0:
        yield tuple()
        return
    if step < 1:
        raise ValueError('step must be >= 1')

    window = deque(maxlen=n)
    i = n
    for _ in map(window.append, seq):
        i -= 1
        if not i:
            i = step
            yield tuple(window)

    size = len(window)
    if size < n:
        yield tuple(chain(window, repeat(fillvalue, n - size)))
    elif 0 < i < min(step, n):
        window += (fillvalue,) * i
        yield tuple(window)


def substrings(iterable):
    """Yield all of the substrings of *iterable*.

        >>> [''.join(s) for s in substrings('more')]
        ['m', 'o', 'r', 'e', 'mo', 'or', 're', 'mor', 'ore', 'more']

    Note that non-string iterables can also be subdivided.

        >>> list(substrings([0, 1, 2]))
        [(0,), (1,), (2,), (0, 1), (1, 2), (0, 1, 2)]

    """
    # The length-1 substrings
    seq = []
    for item in iter(iterable):
        seq.append(item)
        yield (item,)
    seq = tuple(seq)
    item_count = len(seq)

    # And the rest
    for n in range(2, item_count + 1):
        for i in range(item_count - n + 1):
            yield seq[i : i + n]


def substrings_indexes(seq, reverse=False):
    """Yield all substrings and their positions in *seq*

    The items yielded will be a tuple of the form ``(substr, i, j)``, where
    ``substr == seq[i:j]``.

    This function only works for iterables that support slicing, such as
    ``str`` objects.

    >>> for item in substrings_indexes('more'):
    ...    print(item)
    ('m', 0, 1)
    ('o', 1, 2)
    ('r', 2, 3)
    ('e', 3, 4)
    ('mo', 0, 2)
    ('or', 1, 3)
    ('re', 2, 4)
    ('mor', 0, 3)
    ('ore', 1, 4)
    ('more', 0, 4)

    Set *reverse* to ``True`` to yield the same items in the opposite order.


    """
    r = range(1, len(seq) + 1)
    if reverse:
        r = reversed(r)
    return (
        (seq[i : i + L], i, i + L) for L in r for i in range(len(seq) - L + 1)
    )


class bucket:
    """Wrap *iterable* and return an object that buckets it iterable into
    child iterables based on a *key* function.

        >>> iterable = ['a1', 'b1', 'c1', 'a2', 'b2', 'c2', 'b3']
        >>> s = bucket(iterable, key=lambda x: x[0])  # Bucket by 1st character
        >>> sorted(list(s))  # Get the keys
        ['a', 'b', 'c']
        >>> a_iterable = s['a']
        >>> next(a_iterable)
        'a1'
        >>> next(a_iterable)
        'a2'
        >>> list(s['b'])
        ['b1', 'b2', 'b3']

    The original iterable will be advanced and its items will be cached until
    they are used by the child iterables. This may require significant storage.

    By default, attempting to select a bucket to which no items belong  will
    exhaust the iterable and cache all values.
    If you specify a *validator* function, selected buckets will instead be
    checked against it.

        >>> from itertools import count
        >>> it = count(1, 2)  # Infinite sequence of odd numbers
        >>> key = lambda x: x % 10  # Bucket by last digit
        >>> validator = lambda x: x in {1, 3, 5, 7, 9}  # Odd digits only
        >>> s = bucket(it, key=key, validator=validator)
        >>> 2 in s
        False
        >>> list(s[2])
        []

    """

    def __init__(self, iterable, key, validator=None):
        self._it = iter(iterable)
        self._key = key
        self._cache = defaultdict(deque)
        self._validator = validator or (lambda x: True)

    def __contains__(self, value):
        if not self._validator(value):
            return False

        try:
            item = next(self[value])
        except StopIteration:
            return False
        else:
            self._cache[value].appendleft(item)

        return True

    def _get_values(self, value):
        """
        Helper to yield items from the parent iterator that match *value*.
        Items that don't match are stored in the local cache as they
        are encountered.
        """
        while True:
            # If we've cached some items that match the target value, emit
            # the first one and evict it from the cache.
            if self._cache[value]:
                yield self._cache[value].popleft()
            # Otherwise we need to advance the parent iterator to search for
            # a matching item, caching the rest.
            else:
                while True:
                    try:
                        item = next(self._it)
                    except StopIteration:
                        return
                    item_value = self._key(item)
                    if item_value == value:
                        yield item
                        break
                    elif self._validator(item_value):
                        self._cache[item_value].append(item)

    def __iter__(self):
        for item in self._it:
            item_value = self._key(item)
            if self._validator(item_value):
                self._cache[item_value].append(item)

        yield from self._cache.keys()

    def __getitem__(self, value):
        if not self._validator(value):
            return iter(())

        return self._get_values(value)


def spy(iterable, n=1):
    """Return a 2-tuple with a list containing the first *n* elements of
    *iterable*, and an iterator with the same items as *iterable*.
    This allows you to "look ahead" at the items in the iterable without
    advancing it.

    There is one item in the list by default:

        >>> iterable = 'abcdefg'
        >>> head, iterable = spy(iterable)
        >>> head
        ['a']
        >>> list(iterable)
        ['a', 'b', 'c', 'd', 'e', 'f', 'g']

    You may use unpacking to retrieve items instead of lists:

        >>> (head,), iterable = spy('abcdefg')
        >>> head
        'a'
        >>> (first, second), iterable = spy('abcdefg', 2)
        >>> first
        'a'
        >>> second
        'b'

    The number of items requested can be larger than the number of items in
    the iterable:

        >>> iterable = [1, 2, 3, 4, 5]
        >>> head, iterable = spy(iterable, 10)
        >>> head
        [1, 2, 3, 4, 5]
        >>> list(iterable)
        [1, 2, 3, 4, 5]

    """
    it = iter(iterable)
    head = take(n, it)

    return head.copy(), chain(head, it)


def interleave(*iterables):
    """Return a new iterable yielding from each iterable in turn,
    until the shortest is exhausted.

        >>> list(interleave([1, 2, 3], [4, 5], [6, 7, 8]))
        [1, 4, 6, 2, 5, 7]

    For a version that doesn't terminate after the shortest iterable is
    exhausted, see :func:`interleave_longest`.

    """
    return chain.from_iterable(zip(*iterables))


def interleave_longest(*iterables):
    """Return a new iterable yielding from each iterable in turn,
    skipping any that are exhausted.

        >>> list(interleave_longest([1, 2, 3], [4, 5], [6, 7, 8]))
        [1, 4, 6, 2, 5, 7, 3, 8]

    This function produces the same output as :func:`roundrobin`, but may
    perform better for some inputs (in particular when the number of iterables
    is large).

    """
    i = chain.from_iterable(zip_longest(*iterables, fillvalue=_marker))
    return (x for x in i if x is not _marker)


def collapse(iterable, base_type=None, levels=None):
    """Flatten an iterable with multiple levels of nesting (e.g., a list of
    lists of tuples) into non-iterable types.

        >>> iterable = [(1, 2), ([3, 4], [[5], [6]])]
        >>> list(collapse(iterable))
        [1, 2, 3, 4, 5, 6]

    Binary and text strings are not considered iterable and
    will not be collapsed.

    To avoid collapsing other types, specify *base_type*:

        >>> iterable = ['ab', ('cd', 'ef'), ['gh', 'ij']]
        >>> list(collapse(iterable, base_type=tuple))
        ['ab', ('cd', 'ef'), 'gh', 'ij']

    Specify *levels* to stop flattening after a certain level:

    >>> iterable = [('a', ['b']), ('c', ['d'])]
    >>> list(collapse(iterable))  # Fully flattened
    ['a', 'b', 'c', 'd']
    >>> list(collapse(iterable, levels=1))  # Only one level flattened
    ['a', ['b'], 'c', ['d']]

    """

    def walk(node, level):
        if (
            ((levels is not None) and (level > levels))
            or isinstance(node, (str, bytes))
            or ((base_type is not None) and isinstance(node, base_type))
        ):
            yield node
            return

        try:
            tree = iter(node)
        except TypeError:
            yield node
            return
        else:
            for child in tree:
                yield from walk(child, level + 1)

    yield from walk(iterable, 0)


def side_effect(func, iterable, chunk_size=None, before=None, after=None):
    """Invoke *func* on each item in *iterable* (or on each *chunk_size* group
    of items) before yielding the item.

    `func` must be a function that takes a single argument. Its return value
    will be discarded.

    *before* and *after* are optional functions that take no arguments. They
    will be executed before iteration starts and after it ends, respectively.

    `side_effect` can be used for logging, updating progress bars, or anything
    that is not functionally "pure."

    Emitting a status message:

        >>> from more_itertools import consume
        >>> func = lambda item: print('Received {}'.format(item))
        >>> consume(side_effect(func, range(2)))
        Received 0
        Received 1

    Operating on chunks of items:

        >>> pair_sums = []
        >>> func = lambda chunk: pair_sums.append(sum(chunk))
        >>> list(side_effect(func, [0, 1, 2, 3, 4, 5], 2))
        [0, 1, 2, 3, 4, 5]
        >>> list(pair_sums)
        [1, 5, 9]

    Writing to a file-like object:

        >>> from io import StringIO
        >>> from more_itertools import consume
        >>> f = StringIO()
        >>> func = lambda x: print(x, file=f)
        >>> before = lambda: print(u'HEADER', file=f)
        >>> after = f.close
        >>> it = [u'a', u'b', u'c']
        >>> consume(side_effect(func, it, before=before, after=after))
        >>> f.closed
        True

    """
    try:
        if before is not None:
            before()

        if chunk_size is None:
            for item in iterable:
                func(item)
                yield item
        else:
            for chunk in chunked(iterable, chunk_size):
                func(chunk)
                yield from chunk
    finally:
        if after is not None:
            after()


def sliced(seq, n, strict=False):
    """Yield slices of length *n* from the sequence *seq*.

    >>> list(sliced((1, 2, 3, 4, 5, 6), 3))
    [(1, 2, 3), (4, 5, 6)]

    By the default, the last yielded slice will have fewer than *n* elements
    if the length of *seq* is not divisible by *n*:

    >>> list(sliced((1, 2, 3, 4, 5, 6, 7, 8), 3))
    [(1, 2, 3), (4, 5, 6), (7, 8)]

    If the length of *seq* is not divisible by *n* and *strict* is
    ``True``, then ``ValueError`` will be raised before the last
    slice is yielded.

    This function will only work for iterables that support slicing.
    For non-sliceable iterables, see :func:`chunked`.

    """
    iterator = takewhile(len, (seq[i : i + n] for i in count(0, n)))
    if strict:

        def ret():
            for _slice in iterator:
                if len(_slice) != n:
                    raise ValueError("seq is not divisible by n.")
                yield _slice

        return iter(ret())
    else:
        return iterator


def split_at(iterable, pred, maxsplit=-1, keep_separator=False):
    """Yield lists of items from *iterable*, where each list is delimited by
    an item where callable *pred* returns ``True``.

        >>> list(split_at('abcdcba', lambda x: x == 'b'))
        [['a'], ['c', 'd', 'c'], ['a']]

        >>> list(split_at(range(10), lambda n: n % 2 == 1))
        [[0], [2], [4], [6], [8], []]

    At most *maxsplit* splits are done. If *maxsplit* is not specified or -1,
    then there is no limit on the number of splits:

        >>> list(split_at(range(10), lambda n: n % 2 == 1, maxsplit=2))
        [[0], [2], [4, 5, 6, 7, 8, 9]]

    By default, the delimiting items are not included in the output.
    The include them, set *keep_separator* to ``True``.

        >>> list(split_at('abcdcba', lambda x: x == 'b', keep_separator=True))
        [['a'], ['b'], ['c', 'd', 'c'], ['b'], ['a']]

    """
    if maxsplit == 0:
        yield list(iterable)
        return

    buf = []
    it = iter(iterable)
    for item in it:
        if pred(item):
            yield buf
            if keep_separator:
                yield [item]
            if maxsplit == 1:
                yield list(it)
                return
            buf = []
            maxsplit -= 1
        else:
            buf.append(item)
    yield buf


def split_before(iterable, pred, maxsplit=-1):
    """Yield lists of items from *iterable*, where each list ends just before
    an item for which callable *pred* returns ``True``:

        >>> list(split_before('OneTwo', lambda s: s.isupper()))
        [['O', 'n', 'e'], ['T', 'w', 'o']]

        >>> list(split_before(range(10), lambda n: n % 3 == 0))
        [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]

    At most *maxsplit* splits are done. If *maxsplit* is not specified or -1,
    then there is no limit on the number of splits:

        >>> list(split_before(range(10), lambda n: n % 3 == 0, maxsplit=2))
        [[0, 1, 2], [3, 4, 5], [6, 7, 8, 9]]
    """
    if maxsplit == 0:
        yield list(iterable)
        return

    buf = []
    it = iter(iterable)
    for item in it:
        if pred(item) and buf:
            yield buf
            if maxsplit == 1:
                yield [item] + list(it)
                return
            buf = []
            maxsplit -= 1
        buf.append(item)
    if buf:
        yield buf


def split_after(iterable, pred, maxsplit=-1):
    """Yield lists of items from *iterable*, where each list ends with an
    item where callable *pred* returns ``True``:

        >>> list(split_after('one1two2', lambda s: s.isdigit()))
        [['o', 'n', 'e', '1'], ['t', 'w', 'o', '2']]

        >>> list(split_after(range(10), lambda n: n % 3 == 0))
        [[0], [1, 2, 3], [4, 5, 6], [7, 8, 9]]

    At most *maxsplit* splits are done. If *maxsplit* is not specified or -1,
    then there is no limit on the number of splits:

        >>> list(split_after(range(10), lambda n: n % 3 == 0, maxsplit=2))
        [[0], [1, 2, 3], [4, 5, 6, 7, 8, 9]]

    """
    if maxsplit == 0:
        yield list(iterable)
        return

    buf = []
    it = iter(iterable)
    for item in it:
        buf.append(item)
        if pred(item) and buf:
            yield buf
            if maxsplit == 1:
                yield list(it)
                return
            buf = []
            maxsplit -= 1
    if buf:
        yield buf


def split_when(iterable, pred, maxsplit=-1):
    """Split *iterable* into pieces based on the output of *pred*.
    *pred* should be a function that takes successive pairs of items and
    returns ``True`` if the iterable should be split in between them.

    For example, to find runs of increasing numbers, split the iterable when
    element ``i`` is larger than element ``i + 1``:

        >>> list(split_when([1, 2, 3, 3, 2, 5, 2, 4, 2], lambda x, y: x > y))
        [[1, 2, 3, 3], [2, 5], [2, 4], [2]]

    At most *maxsplit* splits are done. If *maxsplit* is not specified or -1,
    then there is no limit on the number of splits:

        >>> list(split_when([1, 2, 3, 3, 2, 5, 2, 4, 2],
        ...                 lambda x, y: x > y, maxsplit=2))
        [[1, 2, 3, 3], [2, 5], [2, 4, 2]]

    """
    if maxsplit == 0:
        yield list(iterable)
        return

    it = iter(iterable)
    try:
        cur_item = next(it)
    except StopIteration:
        return

    buf = [cur_item]
    for next_item in it:
        if pred(cur_item, next_item):
            yield buf
            if maxsplit == 1:
                yield [next_item] + list(it)
                return
            buf = []
            maxsplit -= 1

        buf.append(next_item)
        cur_item = next_item

    yield buf


def split_into(iterable, sizes):
    """Yield a list of sequential items from *iterable* of length 'n' for each
    integer 'n' in *sizes*.

        >>> list(split_into([1,2,3,4,5,6], [1,2,3]))
        [[1], [2, 3], [4, 5, 6]]

    If the sum of *sizes* is smaller than the length of *iterable*, then the
    remaining items of *iterable* will not be returned.

        >>> list(split_into([1,2,3,4,5,6], [2,3]))
        [[1, 2], [3, 4, 5]]

    If the sum of *sizes* is larger than the length of *iterable*, fewer items
    will be returned in the iteration that overruns *iterable* and further
    lists will be empty:

        >>> list(split_into([1,2,3,4], [1,2,3,4]))
        [[1], [2, 3], [4], []]

    When a ``None`` object is encountered in *sizes*, the returned list will
    contain items up to the end of *iterable* the same way that itertools.slice
    does:

        >>> list(split_into([1,2,3,4,5,6,7,8,9,0], [2,3,None]))
        [[1, 2], [3, 4, 5], [6, 7, 8, 9, 0]]

    :func:`split_into` can be useful for grouping a series of items where the
    sizes of the groups are not uniform. An example would be where in a row
    from a table, multiple columns represent elements of the same feature
    (e.g. a point represented by x,y,z) but, the format is not the same for
    all columns.
    """
    # convert the iterable argument into an iterator so its contents can
    # be consumed by islice in case it is a generator
    it = iter(iterable)

    for size in sizes:
        if size is None:
            yield list(it)
            return
        else:
            yield list(islice(it, size))


def padded(iterable, fillvalue=None, n=None, next_multiple=False):
    """Yield the elements from *iterable*, followed by *fillvalue*, such that
    at least *n* items are emitted.

        >>> list(padded([1, 2, 3], '?', 5))
        [1, 2, 3, '?', '?']

    If *next_multiple* is ``True``, *fillvalue* will be emitted until the
    number of items emitted is a multiple of *n*::

        >>> list(padded([1, 2, 3, 4], n=3, next_multiple=True))
        [1, 2, 3, 4, None, None]

    If *n* is ``None``, *fillvalue* will be emitted indefinitely.

    """
    it = iter(iterable)
    if n is None:
        yield from chain(it, repeat(fillvalue))
    elif n < 1:
        raise ValueError('n must be at least 1')
    else:
        item_count = 0
        for item in it:
            yield item
            item_count += 1

        remaining = (n - item_count) % n if next_multiple else n - item_count
        for _ in range(remaining):
            yield fillvalue


def repeat_last(iterable, default=None):
    """After the *iterable* is exhausted, keep yielding its last element.

        >>> list(islice(repeat_last(range(3)), 5))
        [0, 1, 2, 2, 2]

    If the iterable is empty, yield *default* forever::

        >>> list(islice(repeat_last(range(0), 42), 5))
        [42, 42, 42, 42, 42]

    """
    item = _marker
    for item in iterable:
        yield item
    final = default if item is _marker else item
    yield from repeat(final)


def distribute(n, iterable):
    """Distribute the items from *iterable* among *n* smaller iterables.

        >>> group_1, group_2 = distribute(2, [1, 2, 3, 4, 5, 6])
        >>> list(group_1)
        [1, 3, 5]
        >>> list(group_2)
        [2, 4, 6]

    If the length of *iterable* is not evenly divisible by *n*, then the
    length of the returned iterables will not be identical:

        >>> children = distribute(3, [1, 2, 3, 4, 5, 6, 7])
        >>> [list(c) for c in children]
        [[1, 4, 7], [2, 5], [3, 6]]

    If the length of *iterable* is smaller than *n*, then the last returned
    iterables will be empty:

        >>> children = distribute(5, [1, 2, 3])
        >>> [list(c) for c in children]
        [[1], [2], [3], [], []]

    This function uses :func:`itertools.tee` and may require significant
    storage. If you need the order items in the smaller iterables to match the
    original iterable, see :func:`divide`.

    """
    if n < 1:
        raise ValueError('n must be at least 1')

    children = tee(iterable, n)
    return [islice(it, index, None, n) for index, it in enumerate(children)]


def stagger(iterable, offsets=(-1, 0, 1), longest=False, fillvalue=None):
    """Yield tuples whose elements are offset from *iterable*.
    The amount by which the `i`-th item in each tuple is offset is given by
    the `i`-th item in *offsets*.

        >>> list(stagger([0, 1, 2, 3]))
        [(None, 0, 1), (0, 1, 2), (1, 2, 3)]
        >>> list(stagger(range(8), offsets=(0, 2, 4)))
        [(0, 2, 4), (1, 3, 5), (2, 4, 6), (3, 5, 7)]

    By default, the sequence will end when the final element of a tuple is the
    last item in the iterable. To continue until the first element of a tuple
    is the last item in the iterable, set *longest* to ``True``::

        >>> list(stagger([0, 1, 2, 3], longest=True))
        [(None, 0, 1), (0, 1, 2), (1, 2, 3), (2, 3, None), (3, None, None)]

    By default, ``None`` will be used to replace offsets beyond the end of the
    sequence. Specify *fillvalue* to use some other value.

    """
    children = tee(iterable, len(offsets))

    return zip_offset(
        *children, offsets=offsets, longest=longest, fillvalue=fillvalue
    )


class UnequalIterablesError(ValueError):
    def __init__(self, details=None):
        msg = 'Iterables have different lengths'
        if details is not None:
            msg += (': index 0 has length {}; index {} has length {}').format(
                *details
            )

        super().__init__(msg)


def _zip_equal_generator(iterables):
    for combo in zip_longest(*iterables, fillvalue=_marker):
        for val in combo:
            if val is _marker:
                raise UnequalIterablesError()
        yield combo


def zip_equal(*iterables):
    """``zip`` the input *iterables* together, but raise
    ``UnequalIterablesError`` if they aren't all the same length.

        >>> it_1 = range(3)
        >>> it_2 = iter('abc')
        >>> list(zip_equal(it_1, it_2))
        [(0, 'a'), (1, 'b'), (2, 'c')]

        >>> it_1 = range(3)
        >>> it_2 = iter('abcd')
        >>> list(zip_equal(it_1, it_2)) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        more_itertools.more.UnequalIterablesError: Iterables have different
        lengths

    """
    if hexversion >= 0x30A00A6:
        warnings.warn(
            (
                'zip_equal will be removed in a future version of '
                'more-itertools. Use the builtin zip function with '
                'strict=True instead.'
            ),
            DeprecationWarning,
        )
    # Check whether the iterables are all the same size.
    try:
        first_size = len(iterables[0])
        for i, it in enumerate(iterables[1:], 1):
            size = len(it)
            if size != first_size:
                break
        else:
            # If we didn't break out, we can use the built-in zip.
            return zip(*iterables)

        # If we did break out, there was a mismatch.
        raise UnequalIterablesError(details=(first_size, i, size))
    # If any one of the iterables didn't have a length, start reading
    # them until one runs out.
    except TypeError:
        return _zip_equal_generator(iterables)


def zip_offset(*iterables, offsets, longest=False, fillvalue=None):
    """``zip`` the input *iterables* together, but offset the `i`-th iterable
    by the `i`-th item in *offsets*.

        >>> list(zip_offset('0123', 'abcdef', offsets=(0, 1)))
        [('0', 'b'), ('1', 'c'), ('2', 'd'), ('3', 'e')]

    This can be used as a lightweight alternative to SciPy or pandas to analyze
    data sets in which some series have a lead or lag relationship.

    By default, the sequence will end when the shortest iterable is exhausted.
    To continue until the longest iterable is exhausted, set *longest* to
    ``True``.

        >>> list(zip_offset('0123', 'abcdef', offsets=(0, 1), longest=True))
        [('0', 'b'), ('1', 'c'), ('2', 'd'), ('3', 'e'), (None, 'f')]

    By default, ``None`` will be used to replace offsets beyond the end of the
    sequence. Specify *fillvalue* to use some other value.

    """
    if len(iterables) != len(offsets):
        raise ValueError("Number of iterables and offsets didn't match")

    staggered = []
    for it, n in zip(iterables, offsets):
        if n < 0:
            staggered.append(chain(repeat(fillvalue, -n), it))
        elif n > 0:
            staggered.append(islice(it, n, None))
        else:
            staggered.append(it)

    if longest:
        return zip_longest(*staggered, fillvalue=fillvalue)

    return zip(*staggered)


def sort_together(iterables, key_list=(0,), key=None, reverse=False):
    """Return the input iterables sorted together, with *key_list* as the
    priority for sorting. All iterables are trimmed to the length of the
    shortest one.

    This can be used like the sorting function in a spreadsheet. If each
    iterable represents a column of data, the key list determines which
    columns are used for sorting.

    By default, all iterables are sorted using the ``0``-th iterable::

        >>> iterables = [(4, 3, 2, 1), ('a', 'b', 'c', 'd')]
        >>> sort_together(iterables)
        [(1, 2, 3, 4), ('d', 'c', 'b', 'a')]

    Set a different key list to sort according to another iterable.
    Specifying multiple keys dictates how ties are broken::

        >>> iterables = [(3, 1, 2), (0, 1, 0), ('c', 'b', 'a')]
        >>> sort_together(iterables, key_list=(1, 2))
        [(2, 3, 1), (0, 0, 1), ('a', 'c', 'b')]

    To sort by a function of the elements of the iterable, pass a *key*
    function. Its arguments are the elements of the iterables corresponding to
    the key list::

        >>> names = ('a', 'b', 'c')
        >>> lengths = (1, 2, 3)
        >>> widths = (5, 2, 1)
        >>> def area(length, width):
        ...     return length * width
        >>> sort_together([names, lengths, widths], key_list=(1, 2), key=area)
        [('c', 'b', 'a'), (3, 2, 1), (1, 2, 5)]

    Set *reverse* to ``True`` to sort in descending order.

        >>> sort_together([(1, 2, 3), ('c', 'b', 'a')], reverse=True)
        [(3, 2, 1), ('a', 'b', 'c')]

    """
    if key is None:
        # if there is no key function, the key argument to sorted is an
        # itemgetter
        key_argument = itemgetter(*key_list)
    else:
        # if there is a key function, call it with the items at the offsets
        # specified by the key function as arguments
        key_list = list(key_list)
        if len(key_list) == 1:
            # if key_list contains a single item, pass the item at that offset
            # as the only argument to the key function
            key_offset = key_list[0]
            key_argument = lambda zipped_items: key(zipped_items[key_offset])
        else:
            # if key_list contains multiple items, use itemgetter to return a
            # tuple of items, which we pass as *args to the key function
            get_key_items = itemgetter(*key_list)
            key_argument = lambda zipped_items: key(
                *get_key_items(zipped_items)
            )

    return list(
        zip(*sorted(zip(*iterables), key=key_argument, reverse=reverse))
    )


def unzip(iterable):
    """The inverse of :func:`zip`, this function disaggregates the elements
    of the zipped *iterable*.

    The ``i``-th iterable contains the ``i``-th element from each element
    of the zipped iterable. The first element is used to to determine the
    length of the remaining elements.

        >>> iterable = [('a', 1), ('b', 2), ('c', 3), ('d', 4)]
        >>> letters, numbers = unzip(iterable)
        >>> list(letters)
        ['a', 'b', 'c', 'd']
        >>> list(numbers)
        [1, 2, 3, 4]

    This is similar to using ``zip(*iterable)``, but it avoids reading
    *iterable* into memory. Note, however, that this function uses
    :func:`itertools.tee` and thus may require significant storage.

    """
    head, iterable = spy(iter(iterable))
    if not head:
        # empty iterable, e.g. zip([], [], [])
        return ()
    # spy returns a one-length iterable as head
    head = head[0]
    iterables = tee(iterable, len(head))

    def itemgetter(i):
        def getter(obj):
            try:
                return obj[i]
            except IndexError:
                # basically if we have an iterable like
                # iter([(1, 2, 3), (4, 5), (6,)])
                # the second unzipped iterable would fail at the third tuple
                # since it would try to access tup[1]
                # same with the third unzipped iterable and the second tuple
                # to support these "improperly zipped" iterables,
                # we create a custom itemgetter
                # which just stops the unzipped iterables
                # at first length mismatch
                raise StopIteration

        return getter

    return tuple(map(itemgetter(i), it) for i, it in enumerate(iterables))


def divide(n, iterable):
    """Divide the elements from *iterable* into *n* parts, maintaining
    order.

        >>> group_1, group_2 = divide(2, [1, 2, 3, 4, 5, 6])
        >>> list(group_1)
        [1, 2, 3]
        >>> list(group_2)
        [4, 5, 6]

    If the length of *iterable* is not evenly divisible by *n*, then the
    length of the returned iterables will not be identical:

        >>> children = divide(3, [1, 2, 3, 4, 5, 6, 7])
        >>> [list(c) for c in children]
        [[1, 2, 3], [4, 5], [6, 7]]

    If the length of the iterable is smaller than n, then the last returned
    iterables will be empty:

        >>> children = divide(5, [1, 2, 3])
        >>> [list(c) for c in children]
        [[1], [2], [3], [], []]

    This function will exhaust the iterable before returning and may require
    significant storage. If order is not important, see :func:`distribute`,
    which does not first pull the iterable into memory.

    """
    if n < 1:
        raise ValueError('n must be at least 1')

    try:
        iterable[:0]
    except TypeError:
        seq = tuple(iterable)
    else:
        seq = iterable

    q, r = divmod(len(seq), n)

    ret = []
    stop = 0
    for i in range(1, n + 1):
        start = stop
        stop += q + 1 if i <= r else q
        ret.append(iter(seq[start:stop]))

    return ret


def always_iterable(obj, base_type=(str, bytes)):
    """If *obj* is iterable, return an iterator over its items::

        >>> obj = (1, 2, 3)
        >>> list(always_iterable(obj))
        [1, 2, 3]

    If *obj* is not iterable, return a one-item iterable containing *obj*::

        >>> obj = 1
        >>> list(always_iterable(obj))
        [1]

    If *obj* is ``None``, return an empty iterable:

        >>> obj = None
        >>> list(always_iterable(None))
        []

    By default, binary and text strings are not considered iterable::

        >>> obj = 'foo'
        >>> list(always_iterable(obj))
        ['foo']

    If *base_type* is set, objects for which ``isinstance(obj, base_type)``
    returns ``True`` won't be considered iterable.

        >>> obj = {'a': 1}
        >>> list(always_iterable(obj))  # Iterate over the dict's keys
        ['a']
        >>> list(always_iterable(obj, base_type=dict))  # Treat dicts as a unit
        [{'a': 1}]

    Set *base_type* to ``None`` to avoid any special handling and treat objects
    Python considers iterable as iterable:

        >>> obj = 'foo'
        >>> list(always_iterable(obj, base_type=None))
        ['f', 'o', 'o']
    """
    if obj is None:
        return iter(())

    if (base_type is not None) and isinstance(obj, base_type):
        return iter((obj,))

    try:
        return iter(obj)
    except TypeError:
        return iter((obj,))


def adjacent(predicate, iterable, distance=1):
    """Return an iterable over `(bool, item)` tuples where the `item` is
    drawn from *iterable* and the `bool` indicates whether
    that item satisfies the *predicate* or is adjacent to an item that does.

    For example, to find whether items are adjacent to a ``3``::

        >>> list(adjacent(lambda x: x == 3, range(6)))
        [(False, 0), (False, 1), (True, 2), (True, 3), (True, 4), (False, 5)]

    Set *distance* to change what counts as adjacent. For example, to find
    whether items are two places away from a ``3``:

        >>> list(adjacent(lambda x: x == 3, range(6), distance=2))
        [(False, 0), (True, 1), (True, 2), (True, 3), (True, 4), (True, 5)]

    This is useful for contextualizing the results of a search function.
    For example, a code comparison tool might want to identify lines that
    have changed, but also surrounding lines to give the viewer of the diff
    context.

    The predicate function will only be called once for each item in the
    iterable.

    See also :func:`groupby_transform`, which can be used with this function
    to group ranges of items with the same `bool` value.

    """
    # Allow distance=0 mainly for testing that it reproduces results with map()
    if distance < 0:
        raise ValueError('distance must be at least 0')

    i1, i2 = tee(iterable)
    padding = [False] * distance
    selected = chain(padding, map(predicate, i1), padding)
    adjacent_to_selected = map(any, windowed(selected, 2 * distance + 1))
    return zip(adjacent_to_selected, i2)


def groupby_transform(iterable, keyfunc=None, valuefunc=None, reducefunc=None):
    """An extension of :func:`itertools.groupby` that can apply transformations
    to the grouped data.

    * *keyfunc* is a function computing a key value for each item in *iterable*
    * *valuefunc* is a function that transforms the individual items from
      *iterable* after grouping
    * *reducefunc* is a function that transforms each group of items

    >>> iterable = 'aAAbBBcCC'
    >>> keyfunc = lambda k: k.upper()
    >>> valuefunc = lambda v: v.lower()
    >>> reducefunc = lambda g: ''.join(g)
    >>> list(groupby_transform(iterable, keyfunc, valuefunc, reducefunc))
    [('A', 'aaa'), ('B', 'bbb'), ('C', 'ccc')]

    Each optional argument defaults to an identity function if not specified.

    :func:`groupby_transform` is useful when grouping elements of an iterable
    using a separate iterable as the key. To do this, :func:`zip` the iterables
    and pass a *keyfunc* that extracts the first element and a *valuefunc*
    that extracts the second element::

        >>> from operator import itemgetter
        >>> keys = [0, 0, 1, 1, 1, 2, 2, 2, 3]
        >>> values = 'abcdefghi'
        >>> iterable = zip(keys, values)
        >>> grouper = groupby_transform(iterable, itemgetter(0), itemgetter(1))
        >>> [(k, ''.join(g)) for k, g in grouper]
        [(0, 'ab'), (1, 'cde'), (2, 'fgh'), (3, 'i')]

    Note that the order of items in the iterable is significant.
    Only adjacent items are grouped together, so if you don't want any
    duplicate groups, you should sort the iterable by the key function.

    """
    ret = groupby(iterable, keyfunc)
    if valuefunc:
        ret = ((k, map(valuefunc, g)) for k, g in ret)
    if reducefunc:
        ret = ((k, reducefunc(g)) for k, g in ret)

    return ret


class numeric_range(abc.Sequence, abc.Hashable):
    """An extension of the built-in ``range()`` function whose arguments can
    be any orderable numeric type.

    With only *stop* specified, *start* defaults to ``0`` and *step*
    defaults to ``1``. The output items will match the type of *stop*:

        >>> list(numeric_range(3.5))
        [0.0, 1.0, 2.0, 3.0]

    With only *start* and *stop* specified, *step* defaults to ``1``. The
    output items will match the type of *start*:

        >>> from decimal import Decimal
        >>> start = Decimal('2.1')
        >>> stop = Decimal('5.1')
        >>> list(numeric_range(start, stop))
        [Decimal('2.1'), Decimal('3.1'), Decimal('4.1')]

    With *start*, *stop*, and *step*  specified the output items will match
    the type of ``start + step``:

        >>> from fractions import Fraction
        >>> start = Fraction(1, 2)  # Start at 1/2
        >>> stop = Fraction(5, 2)  # End at 5/2
        >>> step = Fraction(1, 2)  # Count by 1/2
        >>> list(numeric_range(start, stop, step))
        [Fraction(1, 2), Fraction(1, 1), Fraction(3, 2), Fraction(2, 1)]

    If *step* is zero, ``ValueError`` is raised. Negative steps are supported:

        >>> list(numeric_range(3, -1, -1.0))
        [3.0, 2.0, 1.0, 0.0]

    Be aware of the limitations of floating point numbers; the representation
    of the yielded numbers may be surprising.

    ``datetime.datetime`` objects can be used for *start* and *stop*, if *step*
    is a ``datetime.timedelta`` object:

        >>> import datetime
        >>> start = datetime.datetime(2019, 1, 1)
        >>> stop = datetime.datetime(2019, 1, 3)
        >>> step = datetime.timedelta(days=1)
        >>> items = iter(numeric_range(start, stop, step))
        >>> next(items)
        datetime.datetime(2019, 1, 1, 0, 0)
        >>> next(items)
        datetime.datetime(2019, 1, 2, 0, 0)

    """

    _EMPTY_HASH = hash(range(0, 0))

    def __init__(self, *args):
        argc = len(args)
        if argc == 1:
            (self._stop,) = args
            self._start = type(self._stop)(0)
            self._step = type(self._stop - self._start)(1)
        elif argc == 2:
            self._start, self._stop = args
            self._step = type(self._stop - self._start)(1)
        elif argc == 3:
            self._start, self._stop, self._step = args
        elif argc == 0:
            raise TypeError(
                'numeric_range expected at least '
                '1 argument, got {}'.format(argc)
            )
        else:
            raise TypeError(
                'numeric_range expected at most '
                '3 arguments, got {}'.format(argc)
            )

        self._zero = type(self._step)(0)
        if self._step == self._zero:
            raise ValueError('numeric_range() arg 3 must not be zero')
        self._growing = self._step > self._zero
        self._init_len()

    def __bool__(self):
        if self._growing:
            return self._start < self._stop
        else:
            return self._start > self._stop

    def __contains__(self, elem):
        if self._growing:
            if self._start <= elem < self._stop:
                return (elem - self._start) % self._step == self._zero
        else:
            if self._start >= elem > self._stop:
                return (self._start - elem) % (-self._step) == self._zero

        return False

    def __eq__(self, other):
        if isinstance(other, numeric_range):
            empty_self = not bool(self)
            empty_other = not bool(other)
            if empty_self or empty_other:
                return empty_self and empty_other  # True if both empty
            else:
                return (
                    self._start == other._start
                    and self._step == other._step
                    and self._get_by_index(-1) == other._get_by_index(-1)
                )
        else:
            return False

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._get_by_index(key)
        elif isinstance(key, slice):
            step = self._step if key.step is None else key.step * self._step

            if key.start is None or key.start <= -self._len:
                start = self._start
            elif key.start >= self._len:
                start = self._stop
            else:  # -self._len < key.start < self._len
                start = self._get_by_index(key.start)

            if key.stop is None or key.stop >= self._len:
                stop = self._stop
            elif key.stop <= -self._len:
                stop = self._start
            else:  # -self._len < key.stop < self._len
                stop = self._get_by_index(key.stop)

            return numeric_range(start, stop, step)
        else:
            raise TypeError(
                'numeric range indices must be '
                'integers or slices, not {}'.format(type(key).__name__)
            )

    def __hash__(self):
        if self:
            return hash((self._start, self._get_by_index(-1), self._step))
        else:
            return self._EMPTY_HASH

    def __iter__(self):
        values = (self._start + (n * self._step) for n in count())
        if self._growing:
            return takewhile(partial(gt, self._stop), values)
        else:
            return takewhile(partial(lt, self._stop), values)

    def __len__(self):
        return self._len

    def _init_len(self):
        if self._growing:
            start = self._start
            stop = self._stop
            step = self._step
        else:
            start = self._stop
            stop = self._start
            step = -self._step
        distance = stop - start
        if distance <= self._zero:
            self._len = 0
        else:  # distance > 0 and step > 0: regular euclidean division
            q, r = divmod(distance, step)
            self._len = int(q) + int(r != self._zero)

    def __reduce__(self):
        return numeric_range, (self._start, self._stop, self._step)

    def __repr__(self):
        if self._step == 1:
            return "numeric_range({}, {})".format(
                repr(self._start), repr(self._stop)
            )
        else:
            return "numeric_range({}, {}, {})".format(
                repr(self._start), repr(self._stop), repr(self._step)
            )

    def __reversed__(self):
        return iter(
            numeric_range(
                self._get_by_index(-1), self._start - self._step, -self._step
            )
        )

    def count(self, value):
        return int(value in self)

    def index(self, value):
        if self._growing:
            if self._start <= value < self._stop:
                q, r = divmod(value - self._start, self._step)
                if r == self._zero:
                    return int(q)
        else:
            if self._start >= value > self._stop:
                q, r = divmod(self._start - value, -self._step)
                if r == self._zero:
                    return int(q)

        raise ValueError("{} is not in numeric range".format(value))

    def _get_by_index(self, i):
        if i < 0:
            i += self._len
        if i < 0 or i >= self._len:
            raise IndexError("numeric range object index out of range")
        return self._start + i * self._step


def count_cycle(iterable, n=None):
    """Cycle through the items from *iterable* up to *n* times, yielding
    the number of completed cycles along with each item. If *n* is omitted the
    process repeats indefinitely.

    >>> list(count_cycle('AB', 3))
    [(0, 'A'), (0, 'B'), (1, 'A'), (1, 'B'), (2, 'A'), (2, 'B')]

    """
    iterable = tuple(iterable)
    if not iterable:
        return iter(())
    counter = count() if n is None else range(n)
    return ((i, item) for i in counter for item in iterable)


def mark_ends(iterable):
    """Yield 3-tuples of the form ``(is_first, is_last, item)``.

    >>> list(mark_ends('ABC'))
    [(True, False, 'A'), (False, False, 'B'), (False, True, 'C')]

    Use this when looping over an iterable to take special action on its first
    and/or last items:

    >>> iterable = ['Header', 100, 200, 'Footer']
    >>> total = 0
    >>> for is_first, is_last, item in mark_ends(iterable):
    ...     if is_first:
    ...         continue  # Skip the header
    ...     if is_last:
    ...         continue  # Skip the footer
    ...     total += item
    >>> print(total)
    300
    """
    it = iter(iterable)

    try:
        b = next(it)
    except StopIteration:
        return

    try:
        for i in count():
            a = b
            b = next(it)
            yield i == 0, False, a

    except StopIteration:
        yield i == 0, True, a


def locate(iterable, pred=bool, window_size=None):
    """Yield the index of each item in *iterable* for which *pred* returns
    ``True``.

    *pred* defaults to :func:`bool`, which will select truthy items:

        >>> list(locate([0, 1, 1, 0, 1, 0, 0]))
        [1, 2, 4]

    Set *pred* to a custom function to, e.g., find the indexes for a particular
    item.

        >>> list(locate(['a', 'b', 'c', 'b'], lambda x: x == 'b'))
        [1, 3]

    If *window_size* is given, then the *pred* function will be called with
    that many items. This enables searching for sub-sequences:

        >>> iterable = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3]
        >>> pred = lambda *args: args == (1, 2, 3)
        >>> list(locate(iterable, pred=pred, window_size=3))
        [1, 5, 9]

    Use with :func:`seekable` to find indexes and then retrieve the associated
    items:

        >>> from itertools import count
        >>> from more_itertools import seekable
        >>> source = (3 * n + 1 if (n % 2) else n // 2 for n in count())
        >>> it = seekable(source)
        >>> pred = lambda x: x > 100
        >>> indexes = locate(it, pred=pred)
        >>> i = next(indexes)
        >>> it.seek(i)
        >>> next(it)
        106

    """
    if window_size is None:
        return compress(count(), map(pred, iterable))

    if window_size < 1:
        raise ValueError('window size must be at least 1')

    it = windowed(iterable, window_size, fillvalue=_marker)
    return compress(count(), starmap(pred, it))


def lstrip(iterable, pred):
    """Yield the items from *iterable*, but strip any from the beginning
    for which *pred* returns ``True``.

    For example, to remove a set of items from the start of an iterable:

        >>> iterable = (None, False, None, 1, 2, None, 3, False, None)
        >>> pred = lambda x: x in {None, False, ''}
        >>> list(lstrip(iterable, pred))
        [1, 2, None, 3, False, None]

    This function is analogous to to :func:`str.lstrip`, and is essentially
    an wrapper for :func:`itertools.dropwhile`.

    """
    return dropwhile(pred, iterable)


def rstrip(iterable, pred):
    """Yield the items from *iterable*, but strip any from the end
    for which *pred* returns ``True``.

    For example, to remove a set of items from the end of an iterable:

        >>> iterable = (None, False, None, 1, 2, None, 3, False, None)
        >>> pred = lambda x: x in {None, False, ''}
        >>> list(rstrip(iterable, pred))
        [None, False, None, 1, 2, None, 3]

    This function is analogous to :func:`str.rstrip`.

    """
    cache = []
    cache_append = cache.append
    cache_clear = cache.clear
    for x in iterable:
        if pred(x):
            cache_append(x)
        else:
            yield from cache
            cache_clear()
            yield x


def strip(iterable, pred):
    """Yield the items from *iterable*, but strip any from the
    beginning and end for which *pred* returns ``True``.

    For example, to remove a set of items from both ends of an iterable:

        >>> iterable = (None, False, None, 1, 2, None, 3, False, None)
        >>> pred = lambda x: x in {None, False, ''}
        >>> list(strip(iterable, pred))
        [1, 2, None, 3]

    This function is analogous to :func:`str.strip`.

    """
    return rstrip(lstrip(iterable, pred), pred)


class islice_extended:
    """An extension of :func:`itertools.islice` that supports negative values
    for *stop*, *start*, and *step*.

        >>> iterable = iter('abcdefgh')
        >>> list(islice_extended(iterable, -4, -1))
        ['e', 'f', 'g']

    Slices with negative values require some caching of *iterable*, but this
    function takes care to minimize the amount of memory required.

    For example, you can use a negative step with an infinite iterator:

        >>> from itertools import count
        >>> list(islice_extended(count(), 110, 99, -2))
        [110, 108, 106, 104, 102, 100]

    You can also use slice notation directly:

        >>> iterable = map(str, count())
        >>> it = islice_extended(iterable)[10:20:2]
        >>> list(it)
        ['10', '12', '14', '16', '18']

    """

    def __init__(self, iterable, *args):
        it = iter(iterable)
        if args:
            self._iterable = _islice_helper(it, slice(*args))
        else:
            self._iterable = it

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._iterable)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return islice_extended(_islice_helper(self._iterable, key))

        raise TypeError('islice_extended.__getitem__ argument must be a slice')


def _islice_helper(it, s):
    start = s.start
    stop = s.stop
    if s.step == 0:
        raise ValueError('step argument must be a non-zero integer or None.')
    step = s.step or 1

    if step > 0:
        start = 0 if (start is None) else start

        if start < 0:
            # Consume all but the last -start items
            cache = deque(enumerate(it, 1), maxlen=-start)
            len_iter = cache[-1][0] if cache else 0

            # Adjust start to be positive
            i = max(len_iter + start, 0)

            # Adjust stop to be positive
            if stop is None:
                j = len_iter
            elif stop >= 0:
                j = min(stop, len_iter)
            else:
                j = max(len_iter + stop, 0)

            # Slice the cache
            n = j - i
            if n <= 0:
                return

            for index, item in islice(cache, 0, n, step):
                yield item
        elif (stop is not None) and (stop < 0):
            # Advance to the start position
            next(islice(it, start, start), None)

            # When stop is negative, we have to carry -stop items while
            # iterating
            cache = deque(islice(it, -stop), maxlen=-stop)

            for index, item in enumerate(it):
                cached_item = cache.popleft()
                if index % step == 0:
                    yield cached_item
                cache.append(item)
        else:
            # When both start and stop are positive we have the normal case
            yield from islice(it, start, stop, step)
    else:
        start = -1 if (start is None) else start

        if (stop is not None) and (stop < 0):
            # Consume all but the last items
            n = -stop - 1
            cache = deque(enumerate(it, 1), maxlen=n)
            len_iter = cache[-1][0] if cache else 0

            # If start and stop are both negative they are comparable and
            # we can just slice. Otherwise we can adjust start to be negative
            # and then slice.
            if start < 0:
                i, j = start, stop
            else:
                i, j = min(start - len_iter, -1), None

            for index, item in list(cache)[i:j:step]:
                yield item
        else:
            # Advance to the stop position
            if stop is not None:
                m = stop + 1
                next(islice(it, m, m), None)

            # stop is positive, so if start is negative they are not comparable
            # and we need the rest of the items.
            if start < 0:
                i = start
                n = None
            # stop is None and start is positive, so we just need items up to
            # the start index.
            elif stop is None:
                i = None
                n = start + 1
            # Both stop and start are positive, so they are comparable.
            else:
                i = None
                n = start - stop
                if n <= 0:
                    return

            cache = list(islice(it, n))

            yield from cache[i::step]


def always_reversible(iterable):
    """An extension of :func:`reversed` that supports all iterables, not
    just those which implement the ``Reversible`` or ``Sequence`` protocols.

        >>> print(*always_reversible(x for x in range(3)))
        2 1 0

    If the iterable is already reversible, this function returns the
    result of :func:`reversed()`. If the iterable is not reversible,
    this function will cache the remaining items in the iterable and
    yield them in reverse order, which may require significant storage.
    """
    try:
        return reversed(iterable)
    except TypeError:
        return reversed(list(iterable))


def consecutive_groups(iterable, ordering=lambda x: x):
    """Yield groups of consecutive items using :func:`itertools.groupby`.
    The *ordering* function determines whether two items are adjacent by
    returning their position.

    By default, the ordering function is the identity function. This is
    suitable for finding runs of numbers:

        >>> iterable = [1, 10, 11, 12, 20, 30, 31, 32, 33, 40]
        >>> for group in consecutive_groups(iterable):
        ...     print(list(group))
        [1]
        [10, 11, 12]
        [20]
        [30, 31, 32, 33]
        [40]

    For finding runs of adjacent letters, try using the :meth:`index` method
    of a string of letters:

        >>> from string import ascii_lowercase
        >>> iterable = 'abcdfgilmnop'
        >>> ordering = ascii_lowercase.index
        >>> for group in consecutive_groups(iterable, ordering):
        ...     print(list(group))
        ['a', 'b', 'c', 'd']
        ['f', 'g']
        ['i']
        ['l', 'm', 'n', 'o', 'p']

    Each group of consecutive items is an iterator that shares it source with
    *iterable*. When an an output group is advanced, the previous group is
    no longer available unless its elements are copied (e.g., into a ``list``).

        >>> iterable = [1, 2, 11, 12, 21, 22]
        >>> saved_groups = []
        >>> for group in consecutive_groups(iterable):
        ...     saved_groups.append(list(group))  # Copy group elements
        >>> saved_groups
        [[1, 2], [11, 12], [21, 22]]

    """
    for k, g in groupby(
        enumerate(iterable), key=lambda x: x[0] - ordering(x[1])
    ):
        yield map(itemgetter(1), g)


def difference(iterable, func=sub, *, initial=None):
    """This function is the inverse of :func:`itertools.accumulate`. By default
    it will compute the first difference of *iterable* using
    :func:`operator.sub`:

        >>> from itertools import accumulate
        >>> iterable = accumulate([0, 1, 2, 3, 4])  # produces 0, 1, 3, 6, 10
        >>> list(difference(iterable))
        [0, 1, 2, 3, 4]

    *func* defaults to :func:`operator.sub`, but other functions can be
    specified. They will be applied as follows::

        A, B, C, D, ... --> A, func(B, A), func(C, B), func(D, C), ...

    For example, to do progressive division:

        >>> iterable = [1, 2, 6, 24, 120]
        >>> func = lambda x, y: x // y
        >>> list(difference(iterable, func))
        [1, 2, 3, 4, 5]

    If the *initial* keyword is set, the first element will be skipped when
    computing successive differences.

        >>> it = [10, 11, 13, 16]  # from accumulate([1, 2, 3], initial=10)
        >>> list(difference(it, initial=10))
        [1, 2, 3]

    """
    a, b = tee(iterable)
    try:
        first = [next(b)]
    except StopIteration:
        return iter([])

    if initial is not None:
        first = []

    return chain(first, starmap(func, zip(b, a)))


class SequenceView(Sequence):
    """Return a read-only view of the sequence object *target*.

    :class:`SequenceView` objects are analogous to Python's built-in
    "dictionary view" types. They provide a dynamic view of a sequence's items,
    meaning that when the sequence updates, so does the view.

        >>> seq = ['0', '1', '2']
        >>> view = SequenceView(seq)
        >>> view
        SequenceView(['0', '1', '2'])
        >>> seq.append('3')
        >>> view
        SequenceView(['0', '1', '2', '3'])

    Sequence views support indexing, slicing, and length queries. They act
    like the underlying sequence, except they don't allow assignment:

        >>> view[1]
        '1'
        >>> view[1:-1]
        ['1', '2']
        >>> len(view)
        4

    Sequence views are useful as an alternative to copying, as they don't
    require (much) extra storage.

    """

    def __init__(self, target):
        if not isinstance(target, Sequence):
            raise TypeError
        self._target = target

    def __getitem__(self, index):
        return self._target[index]

    def __len__(self):
        return len(self._target)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self._target))


class seekable:
    """Wrap an iterator to allow for seeking backward and forward. This
    progressively caches the items in the source iterable so they can be
    re-visited.

    Call :meth:`seek` with an index to seek to that position in the source
    iterable.

    To "reset" an iterator, seek to ``0``:

        >>> from itertools import count
        >>> it = seekable((str(n) for n in count()))
        >>> next(it), next(it), next(it)
        ('0', '1', '2')
        >>> it.seek(0)
        >>> next(it), next(it), next(it)
        ('0', '1', '2')
        >>> next(it)
        '3'

    You can also seek forward:

        >>> it = seekable((str(n) for n in range(20)))
        >>> it.seek(10)
        >>> next(it)
        '10'
        >>> it.seek(20)  # Seeking past the end of the source isn't a problem
        >>> list(it)
        []
        >>> it.seek(0)  # Resetting works even after hitting the end
        >>> next(it), next(it), next(it)
        ('0', '1', '2')

    Call :meth:`peek` to look ahead one item without advancing the iterator:

        >>> it = seekable('1234')
        >>> it.peek()
        '1'
        >>> list(it)
        ['1', '2', '3', '4']
        >>> it.peek(default='empty')
        'empty'

    Before the iterator is at its end, calling :func:`bool` on it will return
    ``True``. After it will return ``False``:

        >>> it = seekable('5678')
        >>> bool(it)
        True
        >>> list(it)
        ['5', '6', '7', '8']
        >>> bool(it)
        False

    You may view the contents of the cache with the :meth:`elements` method.
    That returns a :class:`SequenceView`, a view that updates automatically:

        >>> it = seekable((str(n) for n in range(10)))
        >>> next(it), next(it), next(it)
        ('0', '1', '2')
        >>> elements = it.elements()
        >>> elements
        SequenceView(['0', '1', '2'])
        >>> next(it)
        '3'
        >>> elements
        SequenceView(['0', '1', '2', '3'])

    By default, the cache grows as the source iterable progresses, so beware of
    wrapping very large or infinite iterables. Supply *maxlen* to limit the
    size of the cache (this of course limits how far back you can seek).

        >>> from itertools import count
        >>> it = seekable((str(n) for n in count()), maxlen=2)
        >>> next(it), next(it), next(it), next(it)
        ('0', '1', '2', '3')
        >>> list(it.elements())
        ['2', '3']
        >>> it.seek(0)
        >>> next(it), next(it), next(it), next(it)
        ('2', '3', '4', '5')
        >>> next(it)
        '6'

    """

    def __init__(self, iterable, maxlen=None):
        self._source = iter(iterable)
        if maxlen is None:
            self._cache = []
        else:
            self._cache = deque([], maxlen)
        self._index = None

    def __iter__(self):
        return self

    def __next__(self):
        if self._index is not None:
            try:
                item = self._cache[self._index]
            except IndexError:
                self._index = None
            else:
                self._index += 1
                return item

        item = next(self._source)
        self._cache.append(item)
        return item

    def __bool__(self):
        try:
            self.peek()
        except StopIteration:
            return False
        return True

    def peek(self, default=_marker):
        try:
            peeked = next(self)
        except StopIteration:
            if default is _marker:
                raise
            return default
        if self._index is None:
            self._index = len(self._cache)
        self._index -= 1
        return peeked

    def elements(self):
        return SequenceView(self._cache)

    def seek(self, index):
        self._index = index
        remainder = index - len(self._cache)
        if remainder > 0:
            consume(self, remainder)


class run_length:
    """
    :func:`run_length.encode` compresses an iterable with run-length encoding.
    It yields groups of repeated items with the count of how many times they
    were repeated:

        >>> uncompressed = 'abbcccdddd'
        >>> list(run_length.encode(uncompressed))
        [('a', 1), ('b', 2), ('c', 3), ('d', 4)]

    :func:`run_length.decode` decompresses an iterable that was previously
    compressed with run-length encoding. It yields the items of the
    decompressed iterable:

        >>> compressed = [('a', 1), ('b', 2), ('c', 3), ('d', 4)]
        >>> list(run_length.decode(compressed))
        ['a', 'b', 'b', 'c', 'c', 'c', 'd', 'd', 'd', 'd']

    """

    @staticmethod
    def encode(iterable):
        return ((k, ilen(g)) for k, g in groupby(iterable))

    @staticmethod
    def decode(iterable):
        return chain.from_iterable(repeat(k, n) for k, n in iterable)


def exactly_n(iterable, n, predicate=bool):
    """Return ``True`` if exactly ``n`` items in the iterable are ``True``
    according to the *predicate* function.

        >>> exactly_n([True, True, False], 2)
        True
        >>> exactly_n([True, True, False], 1)
        False
        >>> exactly_n([0, 1, 2, 3, 4, 5], 3, lambda x: x < 3)
        True

    The iterable will be advanced until ``n + 1`` truthy items are encountered,
    so avoid calling it on infinite iterables.

    """
    return len(take(n + 1, filter(predicate, iterable))) == n


def circular_shifts(iterable):
    """Return a list of circular shifts of *iterable*.

    >>> circular_shifts(range(4))
    [(0, 1, 2, 3), (1, 2, 3, 0), (2, 3, 0, 1), (3, 0, 1, 2)]
    """
    lst = list(iterable)
    return take(len(lst), windowed(cycle(lst), len(lst)))


def make_decorator(wrapping_func, result_index=0):
    """Return a decorator version of *wrapping_func*, which is a function that
    modifies an iterable. *result_index* is the position in that function's
    signature where the iterable goes.

    This lets you use itertools on the "production end," i.e. at function
    definition. This can augment what the function returns without changing the
    function's code.

    For example, to produce a decorator version of :func:`chunked`:

        >>> from more_itertools import chunked
        >>> chunker = make_decorator(chunked, result_index=0)
        >>> @chunker(3)
        ... def iter_range(n):
        ...     return iter(range(n))
        ...
        >>> list(iter_range(9))
        [[0, 1, 2], [3, 4, 5], [6, 7, 8]]

    To only allow truthy items to be returned:

        >>> truth_serum = make_decorator(filter, result_index=1)
        >>> @truth_serum(bool)
        ... def boolean_test():
        ...     return [0, 1, '', ' ', False, True]
        ...
        >>> list(boolean_test())
        [1, ' ', True]

    The :func:`peekable` and :func:`seekable` wrappers make for practical
    decorators:

        >>> from more_itertools import peekable
        >>> peekable_function = make_decorator(peekable)
        >>> @peekable_function()
        ... def str_range(*args):
        ...     return (str(x) for x in range(*args))
        ...
        >>> it = str_range(1, 20, 2)
        >>> next(it), next(it), next(it)
        ('1', '3', '5')
        >>> it.peek()
        '7'
        >>> next(it)
        '7'

    """
    # See https://sites.google.com/site/bbayles/index/decorator_factory for
    # notes on how this works.
    def decorator(*wrapping_args, **wrapping_kwargs):
        def outer_wrapper(f):
            def inner_wrapper(*args, **kwargs):
                result = f(*args, **kwargs)
                wrapping_args_ = list(wrapping_args)
                wrapping_args_.insert(result_index, result)
                return wrapping_func(*wrapping_args_, **wrapping_kwargs)

            return inner_wrapper

        return outer_wrapper

    return decorator


def map_reduce(iterable, keyfunc, valuefunc=None, reducefunc=None):
    """Return a dictionary that maps the items in *iterable* to categories
    defined by *keyfunc*, transforms them with *valuefunc*, and
    then summarizes them by category with *reducefunc*.

    *valuefunc* defaults to the identity function if it is unspecified.
    If *reducefunc* is unspecified, no summarization takes place:

        >>> keyfunc = lambda x: x.upper()
        >>> result = map_reduce('abbccc', keyfunc)
        >>> sorted(result.items())
        [('A', ['a']), ('B', ['b', 'b']), ('C', ['c', 'c', 'c'])]

    Specifying *valuefunc* transforms the categorized items:

        >>> keyfunc = lambda x: x.upper()
        >>> valuefunc = lambda x: 1
        >>> result = map_reduce('abbccc', keyfunc, valuefunc)
        >>> sorted(result.items())
        [('A', [1]), ('B', [1, 1]), ('C', [1, 1, 1])]

    Specifying *reducefunc* summarizes the categorized items:

        >>> keyfunc = lambda x: x.upper()
        >>> valuefunc = lambda x: 1
        >>> reducefunc = sum
        >>> result = map_reduce('abbccc', keyfunc, valuefunc, reducefunc)
        >>> sorted(result.items())
        [('A', 1), ('B', 2), ('C', 3)]

    You may want to filter the input iterable before applying the map/reduce
    procedure:

        >>> all_items = range(30)
        >>> items = [x for x in all_items if 10 <= x <= 20]  # Filter
        >>> keyfunc = lambda x: x % 2  # Evens map to 0; odds to 1
        >>> categories = map_reduce(items, keyfunc=keyfunc)
        >>> sorted(categories.items())
        [(0, [10, 12, 14, 16, 18, 20]), (1, [11, 13, 15, 17, 19])]
        >>> summaries = map_reduce(items, keyfunc=keyfunc, reducefunc=sum)
        >>> sorted(summaries.items())
        [(0, 90), (1, 75)]

    Note that all items in the iterable are gathered into a list before the
    summarization step, which may require significant storage.

    The returned object is a :obj:`collections.defaultdict` with the
    ``default_factory`` set to ``None``, such that it behaves like a normal
    dictionary.

    """
    valuefunc = (lambda x: x) if (valuefunc is None) else valuefunc

    ret = defaultdict(list)
    for item in iterable:
        key = keyfunc(item)
        value = valuefunc(item)
        ret[key].append(value)

    if reducefunc is not None:
        for key, value_list in ret.items():
            ret[key] = reducefunc(value_list)

    ret.default_factory = None
    return ret


def rlocate(iterable, pred=bool, window_size=None):
    """Yield the index of each item in *iterable* for which *pred* returns
    ``True``, starting from the right and moving left.

    *pred* defaults to :func:`bool`, which will select truthy items:

        >>> list(rlocate([0, 1, 1, 0, 1, 0, 0]))  # Truthy at 1, 2, and 4
        [4, 2, 1]

    Set *pred* to a custom function to, e.g., find the indexes for a particular
    item:

        >>> iterable = iter('abcb')
        >>> pred = lambda x: x == 'b'
        >>> list(rlocate(iterable, pred))
        [3, 1]

    If *window_size* is given, then the *pred* function will be called with
    that many items. This enables searching for sub-sequences:

        >>> iterable = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3]
        >>> pred = lambda *args: args == (1, 2, 3)
        >>> list(rlocate(iterable, pred=pred, window_size=3))
        [9, 5, 1]

    Beware, this function won't return anything for infinite iterables.
    If *iterable* is reversible, ``rlocate`` will reverse it and search from
    the right. Otherwise, it will search from the left and return the results
    in reverse order.

    See :func:`locate` to for other example applications.

    """
    if window_size is None:
        try:
            len_iter = len(iterable)
            return (len_iter - i - 1 for i in locate(reversed(iterable), pred))
        except TypeError:
            pass

    return reversed(list(locate(iterable, pred, window_size)))


def replace(iterable, pred, substitutes, count=None, window_size=1):
    """Yield the items from *iterable*, replacing the items for which *pred*
    returns ``True`` with the items from the iterable *substitutes*.

        >>> iterable = [1, 1, 0, 1, 1, 0, 1, 1]
        >>> pred = lambda x: x == 0
        >>> substitutes = (2, 3)
        >>> list(replace(iterable, pred, substitutes))
        [1, 1, 2, 3, 1, 1, 2, 3, 1, 1]

    If *count* is given, the number of replacements will be limited:

        >>> iterable = [1, 1, 0, 1, 1, 0, 1, 1, 0]
        >>> pred = lambda x: x == 0
        >>> substitutes = [None]
        >>> list(replace(iterable, pred, substitutes, count=2))
        [1, 1, None, 1, 1, None, 1, 1, 0]

    Use *window_size* to control the number of items passed as arguments to
    *pred*. This allows for locating and replacing subsequences.

        >>> iterable = [0, 1, 2, 5, 0, 1, 2, 5]
        >>> window_size = 3
        >>> pred = lambda *args: args == (0, 1, 2)  # 3 items passed to pred
        >>> substitutes = [3, 4] # Splice in these items
        >>> list(replace(iterable, pred, substitutes, window_size=window_size))
        [3, 4, 5, 3, 4, 5]

    """
    if window_size < 1:
        raise ValueError('window_size must be at least 1')

    # Save the substitutes iterable, since it's used more than once
    substitutes = tuple(substitutes)

    # Add padding such that the number of windows matches the length of the
    # iterable
    it = chain(iterable, [_marker] * (window_size - 1))
    windows = windowed(it, window_size)

    n = 0
    for w in windows:
        # If the current window matches our predicate (and we haven't hit
        # our maximum number of replacements), splice in the substitutes
        # and then consume the following windows that overlap with this one.
        # For example, if the iterable is (0, 1, 2, 3, 4...)
        # and the window size is 2, we have (0, 1), (1, 2), (2, 3)...
        # If the predicate matches on (0, 1), we need to zap (0, 1) and (1, 2)
        if pred(*w):
            if (count is None) or (n < count):
                n += 1
                yield from substitutes
                consume(windows, window_size - 1)
                continue

        # If there was no match (or we've reached the replacement limit),
        # yield the first item from the window.
        if w and (w[0] is not _marker):
            yield w[0]


def partitions(iterable):
    """Yield all possible order-preserving partitions of *iterable*.

    >>> iterable = 'abc'
    >>> for part in partitions(iterable):
    ...     print([''.join(p) for p in part])
    ['abc']
    ['a', 'bc']
    ['ab', 'c']
    ['a', 'b', 'c']

    This is unrelated to :func:`partition`.

    """
    sequence = list(iterable)
    n = len(sequence)
    for i in powerset(range(1, n)):
        yield [sequence[i:j] for i, j in zip((0,) + i, i + (n,))]


def set_partitions(iterable, k=None):
    """
    Yield the set partitions of *iterable* into *k* parts. Set partitions are
    not order-preserving.

    >>> iterable = 'abc'
    >>> for part in set_partitions(iterable, 2):
    ...     print([''.join(p) for p in part])
    ['a', 'bc']
    ['ab', 'c']
    ['b', 'ac']


    If *k* is not given, every set partition is generated.

    >>> iterable = 'abc'
    >>> for part in set_partitions(iterable):
    ...     print([''.join(p) for p in part])
    ['abc']
    ['a', 'bc']
    ['ab', 'c']
    ['b', 'ac']
    ['a', 'b', 'c']

    """
    L = list(iterable)
    n = len(L)
    if k is not None:
        if k < 1:
            raise ValueError(
                "Can't partition in a negative or zero number of groups"
            )
        elif k > n:
            return

    def set_partitions_helper(L, k):
        n = len(L)
        if k == 1:
            yield [L]
        elif n == k:
            yield [[s] for s in L]
        else:
            e, *M = L
            for p in set_partitions_helper(M, k - 1):
                yield [[e], *p]
            for p in set_partitions_helper(M, k):
                for i in range(len(p)):
                    yield p[:i] + [[e] + p[i]] + p[i + 1 :]

    if k is None:
        for k in range(1, n + 1):
            yield from set_partitions_helper(L, k)
    else:
        yield from set_partitions_helper(L, k)


class time_limited:
    """
    Yield items from *iterable* until *limit_seconds* have passed.
    If the time limit expires before all items have been yielded, the
    ``timed_out`` parameter will be set to ``True``.

    >>> from time import sleep
    >>> def generator():
    ...     yield 1
    ...     yield 2
    ...     sleep(0.2)
    ...     yield 3
    >>> iterable = time_limited(0.1, generator())
    >>> list(iterable)
    [1, 2]
    >>> iterable.timed_out
    True

    Note that the time is checked before each item is yielded, and iteration
    stops if  the time elapsed is greater than *limit_seconds*. If your time
    limit is 1 second, but it takes 2 seconds to generate the first item from
    the iterable, the function will run for 2 seconds and not yield anything.

    """

    def __init__(self, limit_seconds, iterable):
        if limit_seconds < 0:
            raise ValueError('limit_seconds must be positive')
        self.limit_seconds = limit_seconds
        self._iterable = iter(iterable)
        self._start_time = monotonic()
        self.timed_out = False

    def __iter__(self):
        return self

    def __next__(self):
        item = next(self._iterable)
        if monotonic() - self._start_time > self.limit_seconds:
            self.timed_out = True
            raise StopIteration

        return item


def only(iterable, default=None, too_long=None):
    """If *iterable* has only one item, return it.
    If it has zero items, return *default*.
    If it has more than one item, raise the exception given by *too_long*,
    which is ``ValueError`` by default.

    >>> only([], default='missing')
    'missing'
    >>> only([1])
    1
    >>> only([1, 2])  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    ValueError: Expected exactly one item in iterable, but got 1, 2,
     and perhaps more.'
    >>> only([1, 2], too_long=TypeError)  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    TypeError

    Note that :func:`only` attempts to advance *iterable* twice to ensure there
    is only one item.  See :func:`spy` or :func:`peekable` to check
    iterable contents less destructively.
    """
    it = iter(iterable)
    first_value = next(it, default)

    try:
        second_value = next(it)
    except StopIteration:
        pass
    else:
        msg = (
            'Expected exactly one item in iterable, but got {!r}, {!r}, '
            'and perhaps more.'.format(first_value, second_value)
        )
        raise too_long or ValueError(msg)

    return first_value


def ichunked(iterable, n):
    """Break *iterable* into sub-iterables with *n* elements each.
    :func:`ichunked` is like :func:`chunked`, but it yields iterables
    instead of lists.

    If the sub-iterables are read in order, the elements of *iterable*
    won't be stored in memory.
    If they are read out of order, :func:`itertools.tee` is used to cache
    elements as necessary.

    >>> from itertools import count
    >>> all_chunks = ichunked(count(), 4)
    >>> c_1, c_2, c_3 = next(all_chunks), next(all_chunks), next(all_chunks)
    >>> list(c_2)  # c_1's elements have been cached; c_3's haven't been
    [4, 5, 6, 7]
    >>> list(c_1)
    [0, 1, 2, 3]
    >>> list(c_3)
    [8, 9, 10, 11]

    """
    source = iter(iterable)

    while True:
        # Check to see whether we're at the end of the source iterable
        item = next(source, _marker)
        if item is _marker:
            return

        # Clone the source and yield an n-length slice
        source, it = tee(chain([item], source))
        yield islice(it, n)

        # Advance the source iterable
        consume(source, n)


def distinct_combinations(iterable, r):
    """Yield the distinct combinations of *r* items taken from *iterable*.

        >>> list(distinct_combinations([0, 0, 1], 2))
        [(0, 0), (0, 1)]

    Equivalent to ``set(combinations(iterable))``, except duplicates are not
    generated and thrown away. For larger input sequences this is much more
    efficient.

    """
    if r < 0:
        raise ValueError('r must be non-negative')
    elif r == 0:
        yield ()
        return
    pool = tuple(iterable)
    generators = [unique_everseen(enumerate(pool), key=itemgetter(1))]
    current_combo = [None] * r
    level = 0
    while generators:
        try:
            cur_idx, p = next(generators[-1])
        except StopIteration:
            generators.pop()
            level -= 1
            continue
        current_combo[level] = p
        if level + 1 == r:
            yield tuple(current_combo)
        else:
            generators.append(
                unique_everseen(
                    enumerate(pool[cur_idx + 1 :], cur_idx + 1),
                    key=itemgetter(1),
                )
            )
            level += 1


def filter_except(validator, iterable, *exceptions):
    """Yield the items from *iterable* for which the *validator* function does
    not raise one of the specified *exceptions*.

    *validator* is called for each item in *iterable*.
    It should be a function that accepts one argument and raises an exception
    if that item is not valid.

    >>> iterable = ['1', '2', 'three', '4', None]
    >>> list(filter_except(int, iterable, ValueError, TypeError))
    ['1', '2', '4']

    If an exception other than one given by *exceptions* is raised by
    *validator*, it is raised like normal.
    """
    for item in iterable:
        try:
            validator(item)
        except exceptions:
            pass
        else:
            yield item


def map_except(function, iterable, *exceptions):
    """Transform each item from *iterable* with *function* and yield the
    result, unless *function* raises one of the specified *exceptions*.

    *function* is called to transform each item in *iterable*.
    It should be a accept one argument.

    >>> iterable = ['1', '2', 'three', '4', None]
    >>> list(map_except(int, iterable, ValueError, TypeError))
    [1, 2, 4]

    If an exception other than one given by *exceptions* is raised by
    *function*, it is raised like normal.
    """
    for item in iterable:
        try:
            yield function(item)
        except exceptions:
            pass


def _sample_unweighted(iterable, k):
    # Implementation of "Algorithm L" from the 1994 paper by Kim-Hung Li:
    # "Reservoir-Sampling Algorithms of Time Complexity O(n(1+log(N/n)))".

    # Fill up the reservoir (collection of samples) with the first `k` samples
    reservoir = take(k, iterable)

    # Generate random number that's the largest in a sample of k U(0,1) numbers
    # Largest order statistic: https://en.wikipedia.org/wiki/Order_statistic
    W = exp(log(random()) / k)

    # The number of elements to skip before changing the reservoir is a random
    # number with a geometric distribution. Sample it using random() and logs.
    next_index = k + floor(log(random()) / log(1 - W))

    for index, element in enumerate(iterable, k):

        if index == next_index:
            reservoir[randrange(k)] = element
            # The new W is the largest in a sample of k U(0, `old_W`) numbers
            W *= exp(log(random()) / k)
            next_index += floor(log(random()) / log(1 - W)) + 1

    return reservoir


def _sample_weighted(iterable, k, weights):
    # Implementation of "A-ExpJ" from the 2006 paper by Efraimidis et al. :
    # "Weighted random sampling with a reservoir".

    # Log-transform for numerical stability for weights that are small/large
    weight_keys = (log(random()) / weight for weight in weights)

    # Fill up the reservoir (collection of samples) with the first `k`
    # weight-keys and elements, then heapify the list.
    reservoir = take(k, zip(weight_keys, iterable))
    heapify(reservoir)

    # The number of jumps before changing the reservoir is a random variable
    # with an exponential distribution. Sample it using random() and logs.
    smallest_weight_key, _ = reservoir[0]
    weights_to_skip = log(random()) / smallest_weight_key

    for weight, element in zip(weights, iterable):
        if weight >= weights_to_skip:
            # The notation here is consistent with the paper, but we store
            # the weight-keys in log-space for better numerical stability.
            smallest_weight_key, _ = reservoir[0]
            t_w = exp(weight * smallest_weight_key)
            r_2 = uniform(t_w, 1)  # generate U(t_w, 1)
            weight_key = log(r_2) / weight
            heapreplace(reservoir, (weight_key, element))
            smallest_weight_key, _ = reservoir[0]
            weights_to_skip = log(random()) / smallest_weight_key
        else:
            weights_to_skip -= weight

    # Equivalent to [element for weight_key, element in sorted(reservoir)]
    return [heappop(reservoir)[1] for _ in range(k)]


def sample(iterable, k, weights=None):
    """Return a *k*-length list of elements chosen (without replacement)
    from the *iterable*. Like :func:`random.sample`, but works on iterables
    of unknown length.

    >>> iterable = range(100)
    >>> sample(iterable, 5)  # doctest: +SKIP
    [81, 60, 96, 16, 4]

    An iterable with *weights* may also be given:

    >>> iterable = range(100)
    >>> weights = (i * i + 1 for i in range(100))
    >>> sampled = sample(iterable, 5, weights=weights)  # doctest: +SKIP
    [79, 67, 74, 66, 78]

    The algorithm can also be used to generate weighted random permutations.
    The relative weight of each item determines the probability that it
    appears late in the permutation.

    >>> data = "abcdefgh"
    >>> weights = range(1, len(data) + 1)
    >>> sample(data, k=len(data), weights=weights)  # doctest: +SKIP
    ['c', 'a', 'b', 'e', 'g', 'd', 'h', 'f']
    """
    if k == 0:
        return []

    iterable = iter(iterable)
    if weights is None:
        return _sample_unweighted(iterable, k)
    else:
        weights = iter(weights)
        return _sample_weighted(iterable, k, weights)


def is_sorted(iterable, key=None, reverse=False):
    """Returns ``True`` if the items of iterable are in sorted order, and
    ``False`` otherwise. *key* and *reverse* have the same meaning that they do
    in the built-in :func:`sorted` function.

    >>> is_sorted(['1', '2', '3', '4', '5'], key=int)
    True
    >>> is_sorted([5, 4, 3, 1, 2], reverse=True)
    False

    The function returns ``False`` after encountering the first out-of-order
    item. If there are no out-of-order items, the iterable is exhausted.
    """

    compare = lt if reverse else gt
    it = iterable if (key is None) else map(key, iterable)
    return not any(starmap(compare, pairwise(it)))


class AbortThread(BaseException):
    pass


class callback_iter:
    """Convert a function that uses callbacks to an iterator.

    Let *func* be a function that takes a `callback` keyword argument.
    For example:

    >>> def func(callback=None):
    ...     for i, c in [(1, 'a'), (2, 'b'), (3, 'c')]:
    ...         if callback:
    ...             callback(i, c)
    ...     return 4


    Use ``with callback_iter(func)`` to get an iterator over the parameters
    that are delivered to the callback.

    >>> with callback_iter(func) as it:
    ...     for args, kwargs in it:
    ...         print(args)
    (1, 'a')
    (2, 'b')
    (3, 'c')

    The function will be called in a background thread. The ``done`` property
    indicates whether it has completed execution.

    >>> it.done
    True

    If it completes successfully, its return value will be available
    in the ``result`` property.

    >>> it.result
    4

    Notes:

    * If the function uses some keyword argument besides ``callback``, supply
      *callback_kwd*.
    * If it finished executing, but raised an exception, accessing the
      ``result`` property will raise the same exception.
    * If it hasn't finished executing, accessing the ``result``
      property from within the ``with`` block will raise ``RuntimeError``.
    * If it hasn't finished executing, accessing the ``result`` property from
      outside the ``with`` block will raise a
      ``more_itertools.AbortThread`` exception.
    * Provide *wait_seconds* to adjust how frequently the it is polled for
      output.

    """

    def __init__(self, func, callback_kwd='callback', wait_seconds=0.1):
        self._func = func
        self._callback_kwd = callback_kwd
        self._aborted = False
        self._future = None
        self._wait_seconds = wait_seconds
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._iterator = self._reader()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._aborted = True
        self._executor.shutdown()

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._iterator)

    @property
    def done(self):
        if self._future is None:
            return False
        return self._future.done()

    @property
    def result(self):
        if not self.done:
            raise RuntimeError('Function has not yet completed')

        return self._future.result()

    def _reader(self):
        q = Queue()

        def callback(*args, **kwargs):
            if self._aborted:
                raise AbortThread('canceled by user')

            q.put((args, kwargs))

        self._future = self._executor.submit(
            self._func, **{self._callback_kwd: callback}
        )

        while True:
            try:
                item = q.get(timeout=self._wait_seconds)
            except Empty:
                pass
            else:
                q.task_done()
                yield item

            if self._future.done():
                break

        remaining = []
        while True:
            try:
                item = q.get_nowait()
            except Empty:
                break
            else:
                q.task_done()
                remaining.append(item)
        q.join()
        yield from remaining


def windowed_complete(iterable, n):
    """
    Yield ``(beginning, middle, end)`` tuples, where:

    * Each ``middle`` has *n* items from *iterable*
    * Each ``beginning`` has the items before the ones in ``middle``
    * Each ``end`` has the items after the ones in ``middle``

    >>> iterable = range(7)
    >>> n = 3
    >>> for beginning, middle, end in windowed_complete(iterable, n):
    ...     print(beginning, middle, end)
    () (0, 1, 2) (3, 4, 5, 6)
    (0,) (1, 2, 3) (4, 5, 6)
    (0, 1) (2, 3, 4) (5, 6)
    (0, 1, 2) (3, 4, 5) (6,)
    (0, 1, 2, 3) (4, 5, 6) ()

    Note that *n* must be at least 0 and most equal to the length of
    *iterable*.

    This function will exhaust the iterable and may require significant
    storage.
    """
    if n < 0:
        raise ValueError('n must be >= 0')

    seq = tuple(iterable)
    size = len(seq)

    if n > size:
        raise ValueError('n must be <= len(seq)')

    for i in range(size - n + 1):
        beginning = seq[:i]
        middle = seq[i : i + n]
        end = seq[i + n :]
        yield beginning, middle, end


def all_unique(iterable, key=None):
    """
    Returns ``True`` if all the elements of *iterable* are unique (no two
    elements are equal).

        >>> all_unique('ABCB')
        False

    If a *key* function is specified, it will be used to make comparisons.

        >>> all_unique('ABCb')
        True
        >>> all_unique('ABCb', str.lower)
        False

    The function returns as soon as the first non-unique element is
    encountered. Iterables with a mix of hashable and unhashable items can
    be used, but the function will be slower for unhashable items.
    """
    seenset = set()
    seenset_add = seenset.add
    seenlist = []
    seenlist_add = seenlist.append
    for element in map(key, iterable) if key else iterable:
        try:
            if element in seenset:
                return False
            seenset_add(element)
        except TypeError:
            if element in seenlist:
                return False
            seenlist_add(element)
    return True


def nth_product(index, *args):
    """Equivalent to ``list(product(*args))[index]``.

    The products of *args* can be ordered lexicographically.
    :func:`nth_product` computes the product at sort position *index* without
    computing the previous products.

        >>> nth_product(8, range(2), range(2), range(2), range(2))
        (1, 0, 0, 0)

    ``IndexError`` will be raised if the given *index* is invalid.
    """
    pools = list(map(tuple, reversed(args)))
    ns = list(map(len, pools))

    c = reduce(mul, ns)

    if index < 0:
        index += c

    if not 0 <= index < c:
        raise IndexError

    result = []
    for pool, n in zip(pools, ns):
        result.append(pool[index % n])
        index //= n

    return tuple(reversed(result))


def nth_permutation(iterable, r, index):
    """Equivalent to ``list(permutations(iterable, r))[index]```

    The subsequences of *iterable* that are of length *r* where order is
    important can be ordered lexicographically. :func:`nth_permutation`
    computes the subsequence at sort position *index* directly, without
    computing the previous subsequences.

        >>> nth_permutation('ghijk', 2, 5)
        ('h', 'i')

    ``ValueError`` will be raised If *r* is negative or greater than the length
    of *iterable*.
    ``IndexError`` will be raised if the given *index* is invalid.
    """
    pool = list(iterable)
    n = len(pool)

    if r is None or r == n:
        r, c = n, factorial(n)
    elif not 0 <= r < n:
        raise ValueError
    else:
        c = factorial(n) // factorial(n - r)

    if index < 0:
        index += c

    if not 0 <= index < c:
        raise IndexError

    if c == 0:
        return tuple()

    result = [0] * r
    q = index * factorial(n) // c if r < n else index
    for d in range(1, n + 1):
        q, i = divmod(q, d)
        if 0 <= n - d < r:
            result[n - d] = i
        if q == 0:
            break

    return tuple(map(pool.pop, result))


def value_chain(*args):
    """Yield all arguments passed to the function in the same order in which
    they were passed. If an argument itself is iterable then iterate over its
    values.

        >>> list(value_chain(1, 2, 3, [4, 5, 6]))
        [1, 2, 3, 4, 5, 6]

    Binary and text strings are not considered iterable and are emitted
    as-is:

        >>> list(value_chain('12', '34', ['56', '78']))
        ['12', '34', '56', '78']


    Multiple levels of nesting are not flattened.

    """
    for value in args:
        if isinstance(value, (str, bytes)):
            yield value
            continue
        try:
            yield from value
        except TypeError:
            yield value


def product_index(element, *args):
    """Equivalent to ``list(product(*args)).index(element)``

    The products of *args* can be ordered lexicographically.
    :func:`product_index` computes the first index of *element* without
    computing the previous products.

        >>> product_index([8, 2], range(10), range(5))
        42

    ``ValueError`` will be raised if the given *element* isn't in the product
    of *args*.
    """
    index = 0

    for x, pool in zip_longest(element, args, fillvalue=_marker):
        if x is _marker or pool is _marker:
            raise ValueError('element is not a product of args')

        pool = tuple(pool)
        index = index * len(pool) + pool.index(x)

    return index


def combination_index(element, iterable):
    """Equivalent to ``list(combinations(iterable, r)).index(element)``

    The subsequences of *iterable* that are of length *r* can be ordered
    lexicographically. :func:`combination_index` computes the index of the
    first *element*, without computing the previous combinations.

        >>> combination_index('adf', 'abcdefg')
        10

    ``ValueError`` will be raised if the given *element* isn't one of the
    combinations of *iterable*.
    """
    element = enumerate(element)
    k, y = next(element, (None, None))
    if k is None:
        return 0

    indexes = []
    pool = enumerate(iterable)
    for n, x in pool:
        if x == y:
            indexes.append(n)
            tmp, y = next(element, (None, None))
            if tmp is None:
                break
            else:
                k = tmp
    else:
        raise ValueError('element is not a combination of iterable')

    n, _ = last(pool, default=(n, None))

    # Python versiosn below 3.8 don't have math.comb
    index = 1
    for i, j in enumerate(reversed(indexes), start=1):
        j = n - j
        if i <= j:
            index += factorial(j) // (factorial(i) * factorial(j - i))

    return factorial(n + 1) // (factorial(k + 1) * factorial(n - k)) - index


def permutation_index(element, iterable):
    """Equivalent to ``list(permutations(iterable, r)).index(element)```

    The subsequences of *iterable* that are of length *r* where order is
    important can be ordered lexicographically. :func:`permutation_index`
    computes the index of the first *element* directly, without computing
    the previous permutations.

        >>> permutation_index([1, 3, 2], range(5))
        19

    ``ValueError`` will be raised if the given *element* isn't one of the
    permutations of *iterable*.
    """
    index = 0
    pool = list(iterable)
    for i, x in zip(range(len(pool), -1, -1), element):
        r = pool.index(x)
        index = index * i + r
        del pool[r]

    return index


class countable:
    """Wrap *iterable* and keep a count of how many items have been consumed.

    The ``items_seen`` attribute starts at ``0`` and increments as the iterable
    is consumed:

        >>> iterable = map(str, range(10))
        >>> it = countable(iterable)
        >>> it.items_seen
        0
        >>> next(it), next(it)
        ('0', '1')
        >>> list(it)
        ['2', '3', '4', '5', '6', '7', '8', '9']
        >>> it.items_seen
        10
    """

    def __init__(self, iterable):
        self._it = iter(iterable)
        self.items_seen = 0

    def __iter__(self):
        return self

    def __next__(self):
        item = next(self._it)
        self.items_seen += 1

        return item

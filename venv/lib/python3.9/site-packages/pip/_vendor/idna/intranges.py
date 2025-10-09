"""
Given a list of integers, made up of (hopefully) a small number of long runs
of consecutive integers, compute a representation of the form
((start1, end1), (start2, end2) ...). Then answer the question "was x present
in the original list?" in time O(log(# runs)).
"""

import bisect
from typing import List, Tuple


def intranges_from_list(list_: List[int]) -> Tuple[int, ...]:
    """Represent a list of integers as a sequence of ranges:
    ((start_0, end_0), (start_1, end_1), ...), such that the original
    integers are exactly those x such that start_i <= x < end_i for some i.

    Ranges are encoded as single integers (start << 32 | end), not as tuples.
    """

    sorted_list = sorted(list_)
    ranges = []
    last_write = -1
    for i in range(len(sorted_list)):
        if i + 1 < len(sorted_list):
            if sorted_list[i] == sorted_list[i + 1] - 1:
                continue
        current_range = sorted_list[last_write + 1 : i + 1]
        ranges.append(_encode_range(current_range[0], current_range[-1] + 1))
        last_write = i

    return tuple(ranges)


def _encode_range(start: int, end: int) -> int:
    return (start << 32) | end


def _decode_range(r: int) -> Tuple[int, int]:
    return (r >> 32), (r & ((1 << 32) - 1))


def intranges_contain(int_: int, ranges: Tuple[int, ...]) -> bool:
    """Determine if `int_` falls into one of the ranges in `ranges`."""
    tuple_ = _encode_range(int_, 0)
    pos = bisect.bisect_left(ranges, tuple_)
    # we could be immediately ahead of a tuple (start, end)
    # with start < int_ <= end
    if pos > 0:
        left, right = _decode_range(ranges[pos - 1])
        if left <= int_ < right:
            return True
    # or we could be immediately behind a tuple (int_, end)
    if pos < len(ranges):
        left, _ = _decode_range(ranges[pos])
        if left == int_:
            return True
    return False

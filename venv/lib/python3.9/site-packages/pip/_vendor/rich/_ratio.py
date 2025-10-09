from fractions import Fraction
from math import ceil
from typing import cast, List, Optional, Sequence, Protocol


class Edge(Protocol):
    """Any object that defines an edge (such as Layout)."""

    size: Optional[int] = None
    ratio: int = 1
    minimum_size: int = 1


def ratio_resolve(total: int, edges: Sequence[Edge]) -> List[int]:
    """Divide total space to satisfy size, ratio, and minimum_size, constraints.

    The returned list of integers should add up to total in most cases, unless it is
    impossible to satisfy all the constraints. For instance, if there are two edges
    with a minimum size of 20 each and `total` is 30 then the returned list will be
    greater than total. In practice, this would mean that a Layout object would
    clip the rows that would overflow the screen height.

    Args:
        total (int): Total number of characters.
        edges (List[Edge]): Edges within total space.

    Returns:
        List[int]: Number of characters for each edge.
    """
    # Size of edge or None for yet to be determined
    sizes = [(edge.size or None) for edge in edges]

    _Fraction = Fraction

    # While any edges haven't been calculated
    while None in sizes:
        # Get flexible edges and index to map these back on to sizes list
        flexible_edges = [
            (index, edge)
            for index, (size, edge) in enumerate(zip(sizes, edges))
            if size is None
        ]
        # Remaining space in total
        remaining = total - sum(size or 0 for size in sizes)
        if remaining <= 0:
            # No room for flexible edges
            return [
                ((edge.minimum_size or 1) if size is None else size)
                for size, edge in zip(sizes, edges)
            ]
        # Calculate number of characters in a ratio portion
        portion = _Fraction(
            remaining, sum((edge.ratio or 1) for _, edge in flexible_edges)
        )

        # If any edges will be less than their minimum, replace size with the minimum
        for index, edge in flexible_edges:
            if portion * edge.ratio <= edge.minimum_size:
                sizes[index] = edge.minimum_size
                # New fixed size will invalidate calculations, so we need to repeat the process
                break
        else:
            # Distribute flexible space and compensate for rounding error
            # Since edge sizes can only be integers we need to add the remainder
            # to the following line
            remainder = _Fraction(0)
            for index, edge in flexible_edges:
                size, remainder = divmod(portion * edge.ratio + remainder, 1)
                sizes[index] = size
            break
    # Sizes now contains integers only
    return cast(List[int], sizes)


def ratio_reduce(
    total: int, ratios: List[int], maximums: List[int], values: List[int]
) -> List[int]:
    """Divide an integer total in to parts based on ratios.

    Args:
        total (int): The total to divide.
        ratios (List[int]): A list of integer ratios.
        maximums (List[int]): List of maximums values for each slot.
        values (List[int]): List of values

    Returns:
        List[int]: A list of integers guaranteed to sum to total.
    """
    ratios = [ratio if _max else 0 for ratio, _max in zip(ratios, maximums)]
    total_ratio = sum(ratios)
    if not total_ratio:
        return values[:]
    total_remaining = total
    result: List[int] = []
    append = result.append
    for ratio, maximum, value in zip(ratios, maximums, values):
        if ratio and total_ratio > 0:
            distributed = min(maximum, round(ratio * total_remaining / total_ratio))
            append(value - distributed)
            total_remaining -= distributed
            total_ratio -= ratio
        else:
            append(value)
    return result


def ratio_distribute(
    total: int, ratios: List[int], minimums: Optional[List[int]] = None
) -> List[int]:
    """Distribute an integer total in to parts based on ratios.

    Args:
        total (int): The total to divide.
        ratios (List[int]): A list of integer ratios.
        minimums (List[int]): List of minimum values for each slot.

    Returns:
        List[int]: A list of integers guaranteed to sum to total.
    """
    if minimums:
        ratios = [ratio if _min else 0 for ratio, _min in zip(ratios, minimums)]
    total_ratio = sum(ratios)
    assert total_ratio > 0, "Sum of ratios must be > 0"

    total_remaining = total
    distributed_total: List[int] = []
    append = distributed_total.append
    if minimums is None:
        _minimums = [0] * len(ratios)
    else:
        _minimums = minimums
    for ratio, minimum in zip(ratios, _minimums):
        if total_ratio > 0:
            distributed = max(minimum, ceil(ratio * total_remaining / total_ratio))
        else:
            distributed = total_remaining
        append(distributed)
        total_ratio -= ratio
        total_remaining -= distributed
    return distributed_total


if __name__ == "__main__":
    from dataclasses import dataclass

    @dataclass
    class E:
        size: Optional[int] = None
        ratio: int = 1
        minimum_size: int = 1

    resolved = ratio_resolve(110, [E(None, 1, 1), E(None, 1, 1), E(None, 1, 1)])
    print(sum(resolved))

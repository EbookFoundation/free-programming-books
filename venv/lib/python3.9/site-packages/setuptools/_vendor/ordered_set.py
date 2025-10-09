"""
An OrderedSet is a custom MutableSet that remembers its order, so that every
entry has an index that can be looked up.

Based on a recipe originally posted to ActiveState Recipes by Raymond Hettiger,
and released under the MIT license.
"""
import itertools as it
from collections import deque

try:
    # Python 3
    from collections.abc import MutableSet, Sequence
except ImportError:
    # Python 2.7
    from collections import MutableSet, Sequence

SLICE_ALL = slice(None)
__version__ = "3.1"


def is_iterable(obj):
    """
    Are we being asked to look up a list of things, instead of a single thing?
    We check for the `__iter__` attribute so that this can cover types that
    don't have to be known by this module, such as NumPy arrays.

    Strings, however, should be considered as atomic values to look up, not
    iterables. The same goes for tuples, since they are immutable and therefore
    valid entries.

    We don't need to check for the Python 2 `unicode` type, because it doesn't
    have an `__iter__` attribute anyway.
    """
    return (
        hasattr(obj, "__iter__")
        and not isinstance(obj, str)
        and not isinstance(obj, tuple)
    )


class OrderedSet(MutableSet, Sequence):
    """
    An OrderedSet is a custom MutableSet that remembers its order, so that
    every entry has an index that can be looked up.

    Example:
        >>> OrderedSet([1, 1, 2, 3, 2])
        OrderedSet([1, 2, 3])
    """

    def __init__(self, iterable=None):
        self.items = []
        self.map = {}
        if iterable is not None:
            self |= iterable

    def __len__(self):
        """
        Returns the number of unique elements in the ordered set

        Example:
            >>> len(OrderedSet([]))
            0
            >>> len(OrderedSet([1, 2]))
            2
        """
        return len(self.items)

    def __getitem__(self, index):
        """
        Get the item at a given index.

        If `index` is a slice, you will get back that slice of items, as a
        new OrderedSet.

        If `index` is a list or a similar iterable, you'll get a list of
        items corresponding to those indices. This is similar to NumPy's
        "fancy indexing". The result is not an OrderedSet because you may ask
        for duplicate indices, and the number of elements returned should be
        the number of elements asked for.

        Example:
            >>> oset = OrderedSet([1, 2, 3])
            >>> oset[1]
            2
        """
        if isinstance(index, slice) and index == SLICE_ALL:
            return self.copy()
        elif is_iterable(index):
            return [self.items[i] for i in index]
        elif hasattr(index, "__index__") or isinstance(index, slice):
            result = self.items[index]
            if isinstance(result, list):
                return self.__class__(result)
            else:
                return result
        else:
            raise TypeError("Don't know how to index an OrderedSet by %r" % index)

    def copy(self):
        """
        Return a shallow copy of this object.

        Example:
            >>> this = OrderedSet([1, 2, 3])
            >>> other = this.copy()
            >>> this == other
            True
            >>> this is other
            False
        """
        return self.__class__(self)

    def __getstate__(self):
        if len(self) == 0:
            # The state can't be an empty list.
            # We need to return a truthy value, or else __setstate__ won't be run.
            #
            # This could have been done more gracefully by always putting the state
            # in a tuple, but this way is backwards- and forwards- compatible with
            # previous versions of OrderedSet.
            return (None,)
        else:
            return list(self)

    def __setstate__(self, state):
        if state == (None,):
            self.__init__([])
        else:
            self.__init__(state)

    def __contains__(self, key):
        """
        Test if the item is in this ordered set

        Example:
            >>> 1 in OrderedSet([1, 3, 2])
            True
            >>> 5 in OrderedSet([1, 3, 2])
            False
        """
        return key in self.map

    def add(self, key):
        """
        Add `key` as an item to this OrderedSet, then return its index.

        If `key` is already in the OrderedSet, return the index it already
        had.

        Example:
            >>> oset = OrderedSet()
            >>> oset.append(3)
            0
            >>> print(oset)
            OrderedSet([3])
        """
        if key not in self.map:
            self.map[key] = len(self.items)
            self.items.append(key)
        return self.map[key]

    append = add

    def update(self, sequence):
        """
        Update the set with the given iterable sequence, then return the index
        of the last element inserted.

        Example:
            >>> oset = OrderedSet([1, 2, 3])
            >>> oset.update([3, 1, 5, 1, 4])
            4
            >>> print(oset)
            OrderedSet([1, 2, 3, 5, 4])
        """
        item_index = None
        try:
            for item in sequence:
                item_index = self.add(item)
        except TypeError:
            raise ValueError(
                "Argument needs to be an iterable, got %s" % type(sequence)
            )
        return item_index

    def index(self, key):
        """
        Get the index of a given entry, raising an IndexError if it's not
        present.

        `key` can be an iterable of entries that is not a string, in which case
        this returns a list of indices.

        Example:
            >>> oset = OrderedSet([1, 2, 3])
            >>> oset.index(2)
            1
        """
        if is_iterable(key):
            return [self.index(subkey) for subkey in key]
        return self.map[key]

    # Provide some compatibility with pd.Index
    get_loc = index
    get_indexer = index

    def pop(self):
        """
        Remove and return the last element from the set.

        Raises KeyError if the set is empty.

        Example:
            >>> oset = OrderedSet([1, 2, 3])
            >>> oset.pop()
            3
        """
        if not self.items:
            raise KeyError("Set is empty")

        elem = self.items[-1]
        del self.items[-1]
        del self.map[elem]
        return elem

    def discard(self, key):
        """
        Remove an element.  Do not raise an exception if absent.

        The MutableSet mixin uses this to implement the .remove() method, which
        *does* raise an error when asked to remove a non-existent item.

        Example:
            >>> oset = OrderedSet([1, 2, 3])
            >>> oset.discard(2)
            >>> print(oset)
            OrderedSet([1, 3])
            >>> oset.discard(2)
            >>> print(oset)
            OrderedSet([1, 3])
        """
        if key in self:
            i = self.map[key]
            del self.items[i]
            del self.map[key]
            for k, v in self.map.items():
                if v >= i:
                    self.map[k] = v - 1

    def clear(self):
        """
        Remove all items from this OrderedSet.
        """
        del self.items[:]
        self.map.clear()

    def __iter__(self):
        """
        Example:
            >>> list(iter(OrderedSet([1, 2, 3])))
            [1, 2, 3]
        """
        return iter(self.items)

    def __reversed__(self):
        """
        Example:
            >>> list(reversed(OrderedSet([1, 2, 3])))
            [3, 2, 1]
        """
        return reversed(self.items)

    def __repr__(self):
        if not self:
            return "%s()" % (self.__class__.__name__,)
        return "%s(%r)" % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        """
        Returns true if the containers have the same items. If `other` is a
        Sequence, then order is checked, otherwise it is ignored.

        Example:
            >>> oset = OrderedSet([1, 3, 2])
            >>> oset == [1, 3, 2]
            True
            >>> oset == [1, 2, 3]
            False
            >>> oset == [2, 3]
            False
            >>> oset == OrderedSet([3, 2, 1])
            False
        """
        # In Python 2 deque is not a Sequence, so treat it as one for
        # consistent behavior with Python 3.
        if isinstance(other, (Sequence, deque)):
            # Check that this OrderedSet contains the same elements, in the
            # same order, as the other object.
            return list(self) == list(other)
        try:
            other_as_set = set(other)
        except TypeError:
            # If `other` can't be converted into a set, it's not equal.
            return False
        else:
            return set(self) == other_as_set

    def union(self, *sets):
        """
        Combines all unique items.
        Each items order is defined by its first appearance.

        Example:
            >>> oset = OrderedSet.union(OrderedSet([3, 1, 4, 1, 5]), [1, 3], [2, 0])
            >>> print(oset)
            OrderedSet([3, 1, 4, 5, 2, 0])
            >>> oset.union([8, 9])
            OrderedSet([3, 1, 4, 5, 2, 0, 8, 9])
            >>> oset | {10}
            OrderedSet([3, 1, 4, 5, 2, 0, 10])
        """
        cls = self.__class__ if isinstance(self, OrderedSet) else OrderedSet
        containers = map(list, it.chain([self], sets))
        items = it.chain.from_iterable(containers)
        return cls(items)

    def __and__(self, other):
        # the parent implementation of this is backwards
        return self.intersection(other)

    def intersection(self, *sets):
        """
        Returns elements in common between all sets. Order is defined only
        by the first set.

        Example:
            >>> oset = OrderedSet.intersection(OrderedSet([0, 1, 2, 3]), [1, 2, 3])
            >>> print(oset)
            OrderedSet([1, 2, 3])
            >>> oset.intersection([2, 4, 5], [1, 2, 3, 4])
            OrderedSet([2])
            >>> oset.intersection()
            OrderedSet([1, 2, 3])
        """
        cls = self.__class__ if isinstance(self, OrderedSet) else OrderedSet
        if sets:
            common = set.intersection(*map(set, sets))
            items = (item for item in self if item in common)
        else:
            items = self
        return cls(items)

    def difference(self, *sets):
        """
        Returns all elements that are in this set but not the others.

        Example:
            >>> OrderedSet([1, 2, 3]).difference(OrderedSet([2]))
            OrderedSet([1, 3])
            >>> OrderedSet([1, 2, 3]).difference(OrderedSet([2]), OrderedSet([3]))
            OrderedSet([1])
            >>> OrderedSet([1, 2, 3]) - OrderedSet([2])
            OrderedSet([1, 3])
            >>> OrderedSet([1, 2, 3]).difference()
            OrderedSet([1, 2, 3])
        """
        cls = self.__class__
        if sets:
            other = set.union(*map(set, sets))
            items = (item for item in self if item not in other)
        else:
            items = self
        return cls(items)

    def issubset(self, other):
        """
        Report whether another set contains this set.

        Example:
            >>> OrderedSet([1, 2, 3]).issubset({1, 2})
            False
            >>> OrderedSet([1, 2, 3]).issubset({1, 2, 3, 4})
            True
            >>> OrderedSet([1, 2, 3]).issubset({1, 4, 3, 5})
            False
        """
        if len(self) > len(other):  # Fast check for obvious cases
            return False
        return all(item in other for item in self)

    def issuperset(self, other):
        """
        Report whether this set contains another set.

        Example:
            >>> OrderedSet([1, 2]).issuperset([1, 2, 3])
            False
            >>> OrderedSet([1, 2, 3, 4]).issuperset({1, 2, 3})
            True
            >>> OrderedSet([1, 4, 3, 5]).issuperset({1, 2, 3})
            False
        """
        if len(self) < len(other):  # Fast check for obvious cases
            return False
        return all(item in self for item in other)

    def symmetric_difference(self, other):
        """
        Return the symmetric difference of two OrderedSets as a new set.
        That is, the new set will contain all elements that are in exactly
        one of the sets.

        Their order will be preserved, with elements from `self` preceding
        elements from `other`.

        Example:
            >>> this = OrderedSet([1, 4, 3, 5, 7])
            >>> other = OrderedSet([9, 7, 1, 3, 2])
            >>> this.symmetric_difference(other)
            OrderedSet([4, 5, 9, 2])
        """
        cls = self.__class__ if isinstance(self, OrderedSet) else OrderedSet
        diff1 = cls(self).difference(other)
        diff2 = cls(other).difference(self)
        return diff1.union(diff2)

    def _update_items(self, items):
        """
        Replace the 'items' list of this OrderedSet with a new one, updating
        self.map accordingly.
        """
        self.items = items
        self.map = {item: idx for (idx, item) in enumerate(items)}

    def difference_update(self, *sets):
        """
        Update this OrderedSet to remove items from one or more other sets.

        Example:
            >>> this = OrderedSet([1, 2, 3])
            >>> this.difference_update(OrderedSet([2, 4]))
            >>> print(this)
            OrderedSet([1, 3])

            >>> this = OrderedSet([1, 2, 3, 4, 5])
            >>> this.difference_update(OrderedSet([2, 4]), OrderedSet([1, 4, 6]))
            >>> print(this)
            OrderedSet([3, 5])
        """
        items_to_remove = set()
        for other in sets:
            items_to_remove |= set(other)
        self._update_items([item for item in self.items if item not in items_to_remove])

    def intersection_update(self, other):
        """
        Update this OrderedSet to keep only items in another set, preserving
        their order in this set.

        Example:
            >>> this = OrderedSet([1, 4, 3, 5, 7])
            >>> other = OrderedSet([9, 7, 1, 3, 2])
            >>> this.intersection_update(other)
            >>> print(this)
            OrderedSet([1, 3, 7])
        """
        other = set(other)
        self._update_items([item for item in self.items if item in other])

    def symmetric_difference_update(self, other):
        """
        Update this OrderedSet to remove items from another set, then
        add items from the other set that were not present in this set.

        Example:
            >>> this = OrderedSet([1, 4, 3, 5, 7])
            >>> other = OrderedSet([9, 7, 1, 3, 2])
            >>> this.symmetric_difference_update(other)
            >>> print(this)
            OrderedSet([4, 5, 9, 2])
        """
        items_to_add = [item for item in other if item not in self]
        items_to_remove = set(other)
        self._update_items(
            [item for item in self.items if item not in items_to_remove] + items_to_add
        )

#
# Copyright 2018 3liz
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Simple LRU cache implementation based on Ordered dict
"""
from collections import OrderedDict
from typing import Any, Sequence, Tuple

class lrucache():

    def __init__(self, size: int) -> None:
        self._table    = OrderedDict()
        self._capacity = size

        # Adjust the size
        self.size(size)

    def __len__(self) -> int:
        return len(self._table)

    def clear(self) -> None:
        self._table.clear()

    def __contains__(self, key: Any) -> bool:
        return key in self._table

    def peek(self, key: Any) -> Any:
        """ Looks up a value in the cache without affecting cache order

            Return None if the key doesn't exists
        """
        # Look up the node
        return self._table.get(key)

    def __getitem__(self, key: Any) -> Any:
        """ Look up the node
        """
        # Update the list ordering
        self._table.move_to_end(key)
        return self._table[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        """ Define a dict like setter
        """
        # First, see if any value is stored under 'key' in the cache already.
        # If so we are going to replace that value with the new one.
        if key in self._table:
            del self._table[key]

        # Keep size
        while len(self._table) >= self._capacity:
            self._table.popitem(last=False)

        OrderedDict.__setitem__(self._table, key, value)

    def __delitem__(self, key: Any) -> None:
        """ Remove from _
        """
        del self._table[key]

    def __iter__(self) -> Sequence[Any]:
        """ Return an iterator that returns the keys in the cache.
        
            Values are returned in order from the most recently to least recently used. 
            Does not modify the cache order.

            Make the cache behaves like a dictionary
        """
        return reversed(self._table.keys())

    def items(self) -> Sequence[Tuple[Any,Any]]:
        """ Return an iterator that returns the (key, value) pairs in the cache.

            Items are returned  in order from the most recently to least recently used. 
            Does not modify the cache order.
        """
        return reversed(self._table.items())

    def keys(self) -> Sequence[Any]:
        """ Return an iterator that returns the keys in the cache.
        
            Keys are returned in order from the most recently to least recently used. 
            Does not modify the cache order.
        """
        return reversed(self._table.keys())

    def values(self) -> Sequence[Any]:
        """ Return an iterator that returns the values in the cache.
            
            Values are returned  in order from the most recently to least recently used. 
            Does not modify the cache order.
        """
        return reversed(self._table.values())

    def size(self, size :int=None) -> int:
        """ Set the size of the cache

            :param int size: maximum number of elements in the cache
        """
        if size is not None:
            assert size > 0
            if size < self._capacity:
                d = self._table
                # Remove extra items
                while len(d) > size:
                    d.popitem(last=False)
            self._capacity = size

        return self._capacity


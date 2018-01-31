''' Cache implementaion with a Least Recently Used (LRU) replacement policy and
    a basic dictionary interface.

The cache is implemented using a combination of a python dictionary (hash
table) and a circular doubly linked list. Items in the cache are stored in
nodes. These nodes make up the linked list. The list is used to efficiently
maintain the order that the items have been used in. The front or head of
the list contains the most recently used item, the tail of the list
contains the least recently used item. When an item is used it can easily
(in a constant amount of time) be moved to the front of the list, thus
updating its position in the ordering. These nodes are also placed in the
hash table under their associated key. The hash table allows efficient
lookup of values by key.

'''

# Copyright (C) 2006, 2009, 2010, 2011 Jay Hutchinson

# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.

# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


# Class for the node objects.
class _dlnode(object):
    def __init__(self):
        self.empty = True


class lrucache(object):

    def __init__(self, size, callback=None):

        self.callback = callback

        # Create an empty hash table.
        self.table = {}

        # Initialize the doubly linked list with one empty node. This is an
        # invariant. The cache size must always be greater than zero. Each
        # node has a 'prev' and 'next' variable to hold the node that comes
        # before it and after it respectivly. Initially the two variables
        # each point to the head node itself, creating a circular doubly
        # linked list of size one. Then the size() method is used to adjust
        # the list to the desired size.

        self.head = _dlnode()
        self.head.next = self.head
        self.head.prev = self.head

        self.listSize = 1

        # Adjust the size
        self.size(size)

    def __len__(self):
        return len(self.table)

    def clear(self):
        for node in self.dli():
            node.empty = True
            node.key = None
            node.value = None

        self.table.clear()

    def __contains__(self, key):
        return key in self.table

    def peek(self, key):
        """ Looks up a value in the cache without affecting cache order

            Return None if the key doesn't exists
        """
        # Look up the node
        node = self.table.get(key)
        if node is not None:
            return node.value

    def __getitem__(self, key):
        """ Look up the node
        """
        node = self.table[key]

        # Update the list ordering. Move this node so that is directly
        # proceeds the head node. Then set the 'head' variable to it. This
        # makes it the new head of the list.
        self.mtf(node)
        self.head = node

        # Return the value.
        return node.value

    def __setitem__(self, key, value):
        """ Define a dict like setter
        """
        # First, see if any value is stored under 'key' in the cache already.
        # If so we are going to replace that value with the new one.
        if key in self.table:

            # Lookup the node
            node = self.table[key]

            # Replace the value.
            node.value = value

            # Update the list ordering.
            self.mtf(node)
            self.head = node

            return

        # Ok, no value is currently stored under 'key' in the cache. We need
        # to choose a node to place the new item in. There are two cases. If
        # the cache is full some item will have to be pushed out of the
        # cache. We want to choose the node with the least recently used
        # item. This is the node at the tail of the list. If the cache is not
        # full we want to choose a node that is empty. Because of the way the
        # list is managed, the empty nodes are always together at the tail
        # end of the list. Thus, in either case, by chooseing the node at the
        # tail of the list our conditions are satisfied.

        # Since the list is circular, the tail node directly preceeds the
        # 'head' node.
        node = self.head.prev

        # If the node already contains something we need to remove the old
        # key from the dictionary.
        if not node.empty:
            if self.callback is not None:
                self.callback(node.key, node.value)
            del self.table[node.key]

        # Place the new key and value in the node
        node.empty = False
        node.key = key
        node.value = value

        # Add the node to the dictionary under the new key.
        self.table[key] = node

        # We need to move the node to the head of the list. The node is the
        # tail node, so it directly preceeds the head node due to the list
        # being circular. Therefore, the ordering is already correct, we just
        # need to adjust the 'head' variable.
        self.head = node

    def __delitem__(self, key):

        # Lookup the node, then remove it from the hash table.
        node = self.table[key]
        del self.table[key]

        node.empty = True

        # Not strictly necessary.
        node.key = None
        node.value = None

        # Because this node is now empty we want to reuse it before any
        # non-empty node. To do that we want to move it to the tail of the
        # list. We move it so that it directly preceeds the 'head' node. This
        # makes it the tail node. The 'head' is then adjusted. This
        # adjustment ensures correctness even for the case where the 'node'
        # is the 'head' node.
        self.mtf(node)
        self.head = node.next

    def __iter__(self):
        """ Return an iterator that returns the keys in the cache.
        
            Values are returned in order from the most recently to least recently used. 
            Does not modify the cache order.

            Make the cache behaves like a dictionary
        """
        for node in self.dli():
            yield node.key

    def items(self):
        """ Return an iterator that returns the (key, value) pairs in the cache.

            Items are returned  in order from the most recently to least recently used. 
            Does not modify the cache order.
        """
        for node in self.dli():
            yield (node.key, node.value)

    def keys(self):
        """ Return an iterator that returns the keys in the cache.
        
            Keys are returned in order from the most recently to least recently used. 
            Does not modify the cache order.
        """
        for node in self.dli():
            yield node.key

    def values(self):
        """ Return an iterator that returns the values in the cache.
            
            Values are returned  in order from the most recently to least recently used. 
            Does not modify the cache order.
        """
        for node in self.dli():
            yield node.value

    def size(self, size=None):
        """ Set the size of the cache

            :param int size: maximum number of elements in the cache
        """
        if size is not None:
            assert size > 0
            if size > self.listSize:
                self.addTailNode(size - self.listSize)
            elif size < self.listSize:
                self.removeTailNode(self.listSize - size)

        return self.listSize

    def addTailNode(self, n):
        """ Increases the size of the cache by inserting n empty nodes at the tail
            of the list.
        """
        for _ in range(n):
            node = _dlnode()
            node.next = self.head
            node.prev = self.head.prev

            self.head.prev.next = node
            self.head.prev = node

        self.listSize += n

    def removeTailNode(self, n):
        """ Decreases the size of the list by removing n nodes from the tail of the
            list.
        """
        assert self.listSize > n
        for _ in range(n):
            node = self.head.prev
            if not node.empty:
                if self.callback is not None:
                    self.callback(node.key, node.value)
                del self.table[node.key]

            # Splice the tail node out of the list
            self.head.prev = node.prev
            node.prev.next = self.head

            # The next four lines are not strictly necessary.
            node.prev = None
            node.next = None

            node.key = None
            node.value = None

        self.listSize -= n

    def mtf(self, node):
        """ Ajusts ordering of nodes

            This method adjusts the ordering of the doubly linked list so that
            'node' directly precedes the 'head' node. Because of the order of
            operations, if 'node' already directly precedes the 'head' node or if
            'node' is the 'head' node the order of the list will be unchanged.
        """
        node.prev.next = node.next
        node.next.prev = node.prev

        node.prev = self.head.prev
        node.next = self.head.prev.next

        node.next.prev = node
        node.prev.next = node

    def dli(self):
        """ Iterate over non empty nodes

            This method returns an iterator that iterates over the non-empty nodes
            in the doubly linked list in order from the most recently to the least
            recently used.
        """
        node = self.head
        for _ in range(len(self.table)):
            yield node
            node = node.next



#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Handle caching projects from files
"""

import os.path

from typing import TypeVar, Tuple
from collections import namedtuple
from .lru import lrucache

# Forward declarations
Storage = TypeVar('Storage')

CacheDetails=namedtuple("CacheDetails",('value','timestamp'))

class FileCache():
    def __init__(self, size: int, store: Storage) -> None:
        """ Initialize file cache

            :param size: size of the lru cache
            :param store: data store for paths and validation 
        """
        from qgis.core import QgsProject

        self.cache = lrucache(size)
        self.store = store

        self.QgsProject = QgsProject

    def remove(self, key: str) -> None:
        del self.cache[key]

    def clear(self) -> None:
        self.cache.clear()

    def validate(self, key: str) -> bool:
        # Get actual path for the project
        path, timestamp = self.store.getpath(key)
        details = self.cache.peek(key)
        if details is not None:
            if details.timestamp < timestamp:
                # Invalidate the cache
                del self.cache[key]
            else:
                return False
        # Load project
        project = self.QgsProject()
        project.read(path)
        self.cache[key] = CacheDetails(project, timestamp)
        self.on_cache_update( key, path )
        return True

    def on_cache_update(self, key: str, path: str ) -> None:
        """ Called when cache is updated
        """
        pass

    def lookup(self, key: str) -> Tuple['QgsProject', bool]:
        updated = self.validate(key)
        return self.cache[key].value, updated


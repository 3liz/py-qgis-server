""" Handle caching projects from files
"""

import os.path

from collections import namedtuple
from .pylru import lrucache


CacheDetails=namedtuple("CacheDetails",('value','timestamp'))

class FileCache():
    def __init__(self, size, store):
        """ Initialize file cache

            :param size: size of the lru cache
            :param store: data store for paths and validation 
        """
        from qgis.core import QgsProject

        self.cache = lrucache(size)
        self.store = store

        self.QgsProject = QgsProject

    def remove(self, key):
        del self.cache[key]

    def clear(self):
        self.cache.clear()

    def validate(self, key):
        from qgis.core import QgsProject
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
        project = QgsProject()
        project.read(path)
        self.cache[key] = CacheDetails(project, timestamp)
        self.on_cache_update( key, path )
        return True

    def on_cache_update(self, key, path ):
        """ Called when cache is updated
        """
        pass

    def lookup(self, key):
        self.validate(key)
        return self.cache[key].value


#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Qgis project cache and protocol resolver
"""

import os
import logging

from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

from .utils.filecache import FileCache
from .utils.decorators import singleton

from .config import get_config

LOGGER = logging.getLogger('QGSRV')

@singleton
class _Cache(FileCache):

    def __init__(self):
        config    = get_config('cache')
        cachesize = config.getint('size')
        rootdir   = Path(config['rootdir'])

        protocols = {}

        def get_protocol_path(scheme):
            """ Resolve protocol path
            """
            LOGGER.debug("Resolving '%s' protocol", scheme)
            rootpath = protocols.get(scheme)
            if not rootpath:
                varname  = "QGSRV_%s_PROTOCOL" % scheme.replace('-','_').upper()
                LOGGER.debug("Lookup scheme '%s' in variable variable %s", scheme, varname) 
                rootpath = os.environ.get(varname)
                if not rootpath:
                    LOGGER.error('Undefined protocol %s' % scheme)
                    raise FileNotFoundError(scheme)
                rootpath = Path(rootpath)
                # XXX Security concern
                if not rootpath.is_absolute():
                    raise ValueError("protocol path must be absolute not %s" % rootpath)
                protocols[scheme] = rootpath
            return rootpath

        class _Store:
            def getpath(self, key, exists=False):
                
                key = urlparse(key)
                if not key.scheme or key.scheme == 'file':
                    rootpath = rootdir
                else:
                    rootpath = get_protocol_path(key.scheme)
                
                key = key.path.strip('/')
                path = rootpath / key
                path = path.with_suffix('.qgs')
                if not path.is_file():
                    raise FileNotFoundError(str(path))

                # Get modification time for the file
                timestamp = datetime.fromtimestamp(path.stat().st_mtime)
                return str(path), timestamp

        # Init FileCache
        super().__init__(size=cachesize, store=_Store())  

    def on_cache_update(self, key, path):
        LOGGER.info("Cache '%s' updated with path: %s" % (key,path)) 


def cache_lookup( path ):
    return _Cache().lookup(path)



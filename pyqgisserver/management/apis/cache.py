#
# Copyright 2021 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
    Wrapper around more tornado-like request handler for
    implementing Qgis server API
"""
import logging

from tornado.web import HTTPError # noqa F401

from pyqgisserver.qgscache.cachemanager import (get_cacheservice, get_project_summary)
 
from .handler import RequestHandler, register_handlers

LOGGER = logging.getLogger('SRVLOG')


class CacheCollection(RequestHandler):

    def get(self, key: str=None) -> None: 
        """ Return plugin info
        """
        if not key:
            # Try to get key from param
            key = self.request.parameter('MAP')

        if not key:
            raise HTTPError(400,reason="Missing project specification")

        cache = get_cacheservice()
        details = cache.peek(key)
        if not details:
            raise HTTPError(404,reason=f"Project '{key}' not in cache")
 
        self.write(get_project_summary(key, details.project))  
                
        
def register( serverIface ):
    """ Register plugins api handlers
    """
    register_handlers(serverIface, "/cache","CacheManagment",
                      [
                          (r'/content/(?P<key>.+)$', CacheCollection),
                          (r'/', CacheCollection),
                      ])
                      


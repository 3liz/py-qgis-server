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
            raise HTTPError(403)

        # We don't want to update the cache
        # Unless the project is not loaded
        cache = get_cacheservice()
        try:
            project, _, _ = cache.get_project(key, strict=False)
        except cache.UnreadableResourceError:
            raise HTTPError(422,reason=f"Cannot read project resource '{key}'") from None
        except cache.PathNotAllowedError:
            raise HTTPError(403,reason="Project path not allowed") from None
        except FileNotFoundError:
            raise HTTPError(404,reason=f"Project '{key}' not found") from None
        
        self.write(get_project_summary(key, project))  
                
        
def register( serverIface ):
    """ Register plugins api handlers
    """
    register_handlers(serverIface, "/cache","CacheManagment",
                      [
                          (r'/cache/(?P<key>[^\/]+)/?$', CacheCollection),
                          (r'/', CacheCollection),
                      ])
                      


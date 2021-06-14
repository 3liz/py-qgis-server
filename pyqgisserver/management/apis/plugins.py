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
from typing import Optional 

from pyqgisserver.plugins import plugin_list, plugin_metadata
from .handler import RequestHandler, register_handlers

LOGGER = logging.getLogger('SRVLOG')



class PluginCollection(RequestHandler):

    def get(self, name: Optional[str]=None) -> None: 
        """ Return plugin info
        """
        if name:
            # Return plugin informations
            metadata = plugin_metadata(name)
            if not metadata:
                raise HTTPError(404)
            self.write({'name': name, 'status': 'loaded', 'metadata': metadata })
        else:
            def link(name):
                return self.public_url(f"/{name}")
            # List all loaded plugins
            self.write({ 'plugins': [{ 'name': n, 'status': 'loaded', 'link': link(n) } for n in plugin_list()]})

        
def register( serverIface ):
    """ Register plugins api handlers
    """
    register_handlers(serverIface, "/plugins","PluginsManagment",
                      [
                          (r'/$', PluginCollection),
                          (r'/(?P<name>[^\/]+)/?$', PluginCollection),
                      ])
                      

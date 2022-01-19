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

from pyqgisserver.plugins import plugin_list, plugin_metadata, failed_plugins
from .handler import RequestHandler, register_handlers

LOGGER = logging.getLogger('SRVLOG')


class PluginCollection(RequestHandler):

    def get(self, name: Optional[str]=None) -> None: 
        """ Return plugin info
        """
        if name:
            if name in failed_plugins:
                self.write({ 'name': name, 'error_log' : failed_plugins[name], 'status': 'failed' })
                return
            # Return plugin informations
            metadata = plugin_metadata(name)
            if not metadata:
                raise HTTPError(404)
            self.write({'name': name, 'status': 'loaded', 'metadata': metadata })
        else:
            def _link(name, status):
                return { 
                    'href': self.public_url(f"/{name}"),
                    'status': status,
                    'name': name,
                    'type': 'application/json',
                    'title': f'Details for plugin {name}',
                }
            # List all loaded plugins
            plugins = [_link(n,'loaded') for n in plugin_list()]
            plugins.extend([_link(n,'failed') for n in failed_plugins])
            self.write({'links': plugins })

        
def register( serverIface ):
    """ Register plugins api handlers
    """
    register_handlers(serverIface, "/plugins","PluginsManagment",
                      [
                          (r'/(?P<name>[^\/]+)/?$', PluginCollection),
                          (r'/', PluginCollection),
                      ])



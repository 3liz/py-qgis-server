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

from tornado.web import HTTPError  # noqa F401
from typing import Optional

from pyqgisserver.config import confservice
from pyqgisserver.plugins import plugin_list, plugin_metadata, failed_plugins
from .handler import RequestHandler, register_handlers

LOGGER = logging.getLogger('SRVLOG')


class PluginCollection(RequestHandler):

    def __init__(self, context):
        super().__init__(context)
        config = confservice['management']
        self.management_proxy_url = config['proxy_url'].strip('/')

    def get(self, name: Optional[str] = None) -> None:
        """ Return plugin info
        """
        if name:
            if name in failed_plugins:
                self.write({'name': name, 'error_log': failed_plugins[name], 'status': 'failed'})
                return
            # Return plugin informations
            metadata = plugin_metadata(name)
            if not metadata:
                raise HTTPError(404)
            self.write({'name': name, 'status': 'loaded', 'metadata': metadata})
        else:
            management_proxy_url = self.management_proxy_url
            def _link(name, status):
                if management_proxy_url:
                    href = f"{management_proxy_url}/plugins/{name}"
                else:
                    href = self.public_url(f"/{name}")
                return {
                    'href': href,
                    'status': status,
                    'name': name,
                    'type': 'application/json',
                    'title': f'Details for plugin {name}',
                }
            # List all loaded plugins
            plugins = [_link(n, 'loaded') for n in plugin_list()]
            plugins.extend([_link(n, 'failed') for n in failed_plugins])
            self.write({'links': plugins})


def register(serverIface):
    """ Register plugins api handlers
    """
    register_handlers(serverIface, "/plugins", "PluginsManagment",
                      [
                          (r'/(?P<name>[^\/]+)/?$', PluginCollection),
                          (r'/', PluginCollection),
                      ])

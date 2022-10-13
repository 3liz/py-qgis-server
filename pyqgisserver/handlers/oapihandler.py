#
# Copyright 2018-2019 3liz
# Author: David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Qgis server handler
"""
import logging

from .asynchandler import AsyncClientHandler

from typing import Awaitable

LOGGER = logging.getLogger('SRVLOG')


class OAPIHandler(AsyncClientHandler):
    """ Handle Qgis api
    """
    def initialize(self, service: str, **kwargs) -> None:
        super().initialize(**kwargs )
        self.ogc_scheme = 'OAF'
        self._service_name = service.upper()

    def prepare(self) -> None:
        super().prepare()
        # Replace MAP key with uppercase
        args = self.request.arguments
        if 'MAP' in args:
            return 
        for k in args:
            if k.upper() == 'MAP':
                key = k
                val = args[k]
                break
        else:
            return
        del args[key]
        args['MAP'] = val

    async def delete(self) -> Awaitable[None]:
        await self.handle_request('DELETE')

    async def put(self) -> Awaitable[None]:
        await self.handle_request('PUT')

    async def patch(self) -> Awaitable[None]:
        await self.handle_request('PATCH')

    async def options(self) -> Awaitable[None]:
        await self.handle_request('OPTIONS')

    def get_monitor_params( self ) -> None:
        """ Override
        """
        params = dict(
            MAP = self.request.arguments.get('MAP','__unknown__'),
            SERVICE = self._service_name,
            REQUEST = self.request.path,
        )
        return params



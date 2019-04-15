#
# Copyright 2018 3liz
# Author: David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Qgis server handler
"""
import logging
from time import time

from ..logger import log_rrequest
from ..zeromq.client import RequestTimeoutError, RequestGatewayError

from .basehandler import BaseHandler, HTTPError

LOGGER = logging.getLogger('QGSRV')


class OwsHandler(BaseHandler):

    """ Proxy to Qgis 0MQ worker
    """
    def initialize(self, client, timeout, monitor=None, profiles=None, map_rewrite=None, http_proxy=False):
        super().initialize()

        self._client      = client
        self._timeout     = timeout
        self._monitor     = monitor
        self._profiles    = profiles
        self._proxy       = http_proxy
        if map_rewrite:
            self._rewrite_map = lambda profile,path:map_rewrite % dict(profile=profile,path=project_path) 
        else:
            self._rewrite_map = None

    async def handle_request(self, method, data=None, profile=None):
        reqtime = time()
        try:
            # Handle profile
            if self._profiles and not self._profiles.apply_profile(profile, self.request, http_proxy=self._proxy):
                raise HTTPError(403,reason="Unauthorized profile")

            proxy_url = self.proxy_url(self._proxy, profile=profile)

            delta = None
            project_path = self.get_argument('MAP')
            query        = self.encode_arguments()

            if self._rewrite_map:
                project_path = self._rewrite_map(project_path, profile)

            headers = {
                'X-Map-Location': project_path 
            } 
            if proxy_url: headers['X-Proxy-Location']=proxy_url
            if self.url_encoded:
                # Do not let qgis server handle url encoded prameters
                method = 'GET'
                data   = None

            response = await self._client.fetch(query=query, method=method, headers=headers, data=data,
                                                timeout=self._timeout)
            status = response.status
            hdrs   = response.headers
            delta  = time() - reqtime

            log_rrequest(status, method, query, delta, hdrs)
           
            # Send response
            for k,v in hdrs.items():
                self.set_header(k,v)

            if status == 206:
                # Partial response
                self.set_status(200)
                self.write(response.data)
                chunk = await self._client.fetch_more(response, timeout=self._timeout)
                if chunk:
                    await self.flush()
                while chunk:
                    self.write(chunk)
                    self.flush()
                    chunk = await self._client.fetch_more(response)
                delta = time() - reqtime
            elif status == 509:
                self.send_error(status, reason="Server busy, please retry later")
            else:
                self.set_status(status)
                self.write(response.data)

        except RequestTimeoutError:
              status = 503
              delta = time() - reqtime
              self.send_error(status, reason="Request timeout error")
        except RequestGatewayError:
              status = 502
              delta = time() - reqtime
              self.send_error(status, reason="Server busy, please retry later")

        if self._monitor:
              self._monitor.emit( status, self.request.arguments,  delta)

    async def get(self, profile=None):
        """ Handle Get method
        """
        await self.handle_request('GET', profile=profile)
          
    async def post(self, profile=None):
        """ Handle Post method
        """
        await self.handle_request('POST', data=self.request.body, profile=profile)
        




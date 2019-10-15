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
from time import time

from ..logger import log_rrequest
from ..zeromq.client import RequestTimeoutError, RequestGatewayError

from .basehandler import BaseHandler, HTTPError

LOGGER = logging.getLogger('SRVLOG')


class OwsHandler(BaseHandler):

    """ Proxy to Qgis 0MQ worker
    """
    def initialize(self, client, timeout, monitor=None, filters=None, http_proxy=False):
        super().initialize()

        self._client      = client
        self._timeout     = timeout
        self._monitor     = monitor
        self._filters     = filters
        self._proxy       = http_proxy

    async def prepare(self):
        # Handle filters
        super().prepare()
        for filt in self._filters:
            await filt.apply( self )

    async def handle_request(self, method, data=None ):
        reqtime = time()
        try:
            proxy_url = self.proxy_url(self._proxy)

            delta = None
            project_path = self.get_argument('MAP')
            query        = self.encode_arguments()

            headers = {
                'X-Map-Location': project_path 
            }

            if proxy_url: headers['X-Proxy-Location']=proxy_url
            if self.has_body_arguments:
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

    async def get(self):
        """ Handle Get method
        """
        await self.handle_request('GET')
          
    async def post(self):
        """ Handle Post method
        """
        await self.handle_request('POST', data=self.request.body)
        




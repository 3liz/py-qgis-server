#
# Copyright 2018 3liz
# Author: David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Qgis server handler
"""
import os
import logging
from time import time

from ..config import get_config
from ..logger import log_rrequest
from ..zeromq.client import RequestTimeoutError, RequestGatewayError

from .basehandler import BaseHandler, HTTPError

LOGGER = logging.getLogger('QGSRV')


class OwsHandler(BaseHandler):

    """ Proxy to Qgis 0MQ worker
    """
    def initialize(self, client, timeout):
        super().initialize()
        self._client  = client
        self._timeout = timeout

    async def handle_request(self, method, data=None):
        reqtime = time()
        try:
            project_path = self.get_argument('MAP')
            query        = self.encode_arguments()
            proxy_url    = self.proxy_url()
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
            
            log_rrequest(status, method, query, time()-reqtime, hdrs)
            
            # Send response
            self.set_status(status)
            for k,v in hdrs.items():
                self.set_header(k,v)
            self.write(response.data)
            if status == 200:
                chunk = await self._client.fetch_more(response)
                if chunk:
                    await self.flush()
                while chunk:
                    self.write(chunk)
                    self.flush()
                    chunk = await self._client.fetch_more(response)
            elif status == 509:
                self.send_error(status, reason="Server busy, please retry later") 

        except RequestTimeoutError:
             raise HTTPError(504)
        except RequestGatewayError:
             raise HTTPError(502)

    async def get(self):
        """ Handle Get method
        """
        await self.handle_request('GET')
          
    async def post(self):
        """ Handle Post method
        """
        await self.handle_request('POST', data=self.request.body)
        




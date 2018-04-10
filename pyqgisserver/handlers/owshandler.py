""" Qgis server handler
"""
import os
import logging
from time import time

from ..config import get_config
from ..logger import log_rrequest
from ..zeromq.client import RequestTimeoutError, RequestGatewayError

from .basehandler import BaseHandler, HTTPError2

LOGGER = logging.getLogger('QGSRV')

class OwsHandler(BaseHandler):

    """ Proxy to Qgis 0MQ worker
    """

    def initialize(self, client):
        super().initialize()
        self._client = client
        self.conf = get_config('server')

    async def handle_request(self, method, data=None):
        reqtime = time()
        try:
            project_path = self.get_query_argument('MAP')
            query        = self.request.query
            proxy_url    = self.proxy_url()
            headers = {
                'X-Map-Location': project_path 
            } 
            if proxy_url: headers['X-Proxy-Location']= proxy_url
            
            response = await self._client.fetch(query=query, method=method, headers=headers, data=data)
            if response.status == 200:
                async for chunk in self._client.fetch_more(response):
                    self.write(chunk)
                    self.flush()

            status = response.status
            hdrs   = response.headers
        except RequestTimeoutError:
             status, hdrs = 504,{}
        except RequestGatewayError:
             status, hdrs = 502,{}

        if self.connection_closed:
            return

        log_rrequest(status, method, query, time()-reqtime, hdrs)
        self.send_error(status, reason="Server busy, please retry later" if status==509 else None)
        
    async def get(self):
        """ Handle Get method
        """
        await self.handle_request('GET')
          
    async def post(self):
        """ Handle Post method
        """
        await self.handle_request('POST', data=self.request.body)
        




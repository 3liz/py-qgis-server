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
from ..zeromq.client import RequestTimeoutError, RequestGatewayError, AsyncClient
from ..monitor import Monitor

from .basehandler import BaseHandler

from typing import Optional, Awaitable, List, Dict

LOGGER = logging.getLogger('SRVLOG')


class AsyncClientHandler(BaseHandler):

    """ Proxy to Qgis 0MQ worker
    """
    def initialize(self, client: AsyncClient, timeout: int, 
                   monitor: Optional[Monitor]=None, 
                   http_proxy: bool=False,
                   allowed_hdrs: List[str]=[] ) -> None:

        super().initialize()

        self._client       = client
        self._timeout      = timeout
        self._monitor      = monitor
        self._proxy        = http_proxy
        self._stats        = self.application.stats
        self._allowed_hdrs = allowed_hdrs
        self._proxy_url    = None

        self.ogc_scheme   = None

    def set_backend_headers(self, headers) -> Dict[str,str]:
        """ Set headers passed to backend
        """
        project_path = self.get_argument('MAP',default=None)
       
        if project_path:
            headers['X-Map-Location']=project_path 
        if self.ogc_scheme:
            headers['X-Ogc-Scheme'] = self.ogc_scheme

        # Pass etag
        headers['If-None-Match'] = self.request.headers.get("If-None-Match", "")

        def copy_headers(pats):
            headers.update((k,v) for k,v in self.request.headers.items() if \
                           any(map(k.upper().startswith,pats)))

        # Copy custom Qgis/Forwarded headers
        # see https://github.com/qgis/QGIS/pull/41333
        copy_headers(self._allowed_hdrs)

    async def handle_request(self, method: str, endpoint: Optional[str]=None) -> Awaitable[None]:
        reqtime = time()
        try:
            delta = None
            query = self.encode_arguments()

            headers = {}
            proxy_url = self.proxy_url(self._proxy, endpoint)
            if proxy_url: 
                headers['X-Forwarded-Url']=proxy_url

            self.set_backend_headers(headers)

            data = self.request.body

            if self.get_argument('SERVICE', default=None) and  self.has_body_arguments:
                # Do not let qgis server handle url encoded parameters
                data = None
                if method == 'POST':
                    method = 'GET'

            self._stats.num_requests +=1

            response = await self._client.fetch(query=query, method=method, 
                                                headers=headers, data=data,
                                                timeout=self._timeout)
            status = response.status
            hdrs   = response.headers
            delta  = time() - reqtime

            log_rrequest(proxy_url, status, method, query, delta, hdrs)
           
            # Send response
            for k,v in hdrs.items():
                self.set_header(k,v)

            # Send CORS Header
            self.set_access_control_headers()

            if status == 206:
                # Partial response
                self.set_status(200)
                self.write(response.data)
                await self.flush()
                async for chunk in self._client.fetch_more(response, timeout=self._timeout):
                    self.write(chunk)
                    await self.flush()
                delta = time() - reqtime
            elif status == 509:
                self.send_error(status, reason="Server busy, please retry later")
            else:
                self.set_status(status)
                if response.data:
                    # XXX Tornado do no like 304 
                    # with (potentially empty) chunk
                    self.write(response.data)

        except RequestTimeoutError:
            status = 504
            delta = time() - reqtime
            # Log the request with status code 499 indicating
            # that the request has not returned
            log_rrequest(proxy_url, 499, method, query, delta, {})
            self.send_error(status, reason="Request timeout error")
        except RequestGatewayError:
            status = 502
            delta = time() - reqtime
            # Log the request 
            log_rrequest(proxy_url, 499, method, query, delta, {})
            self.send_error(status, reason="Backend request error")

        if status >= 500:
            self._stats.num_errors +=1

        if self._monitor:
            self._monitor.emit( status, self.request.arguments,  delta, 
                                meta=self.request.headers)

    async def get(self, endpoint: Optional[str]=None) -> Awaitable[None]:
        """ Handle Get method
        """
        await self.handle_request('GET', endpoint)

    async def post(self, endpoint: Optional[str]=None) -> Awaitable[None]:
        """ Handle Post method
        """
        await self.handle_request('POST', endpoint)
        
    def options(self, endpoint: Optional[str]=None) -> None:
        """ Implement OPTIONS for validating CORS
        """
        self.set_option_headers('GET, POST, OPTIONS')

    def head(self, endpoint: Optional[str]=None) -> Awaitable[None]:
        """ Handle HEAD method

            HEAD method is not forwarded because qgis server 
            return 501.
            
            Because of this the actuel HEAD method does not return anything meaningful about 
            the resources referenced from the url - may this will change it the future.
        """
        pass



class OwsHandler(AsyncClientHandler):

    def initialize( self, *args, **kwargs ) -> None:
        super().initialize(*args, **kwargs )
        self.ogc_scheme = 'OWS'


class _FilterHandlerMixIn:
    """ Handle filter handlers
    """
    def initialize(self, filters: Optional[List]=None, **kwargs) -> None:
        super().initialize(**kwargs)
        
        self._filters = filters or []

    async def prepare(self) -> Awaitable[None]:
        # Handle filters
        super().prepare()
        for filt in self._filters:
            await filt.apply( self )


class OwsFilterHandler(_FilterHandlerMixIn,OwsHandler):
    pass


class OwsApiHandler(AsyncClientHandler):
    """ Handle Qgis api
    """
    def initialize( self, *args, **kwargs ) -> None:
        super().initialize(*args, **kwargs )
        self.ogc_scheme = 'OAF'

    async def get(self, endpoint: Optional[str]=None) -> Awaitable[None]:
        """ Fix issue with the landing page api when not 
            specifying index.html.
        """
        await super().get(endpoint)
 
    async def delete(self, endpoint: Optional[str]=None) -> Awaitable[None]:
        await self.handle_request('DELETE', endpoint)

    async def head(self, endpoint: Optional[str]=None) -> Awaitable[None]:
        await self.handle_request('HEAD', endpoint)

    async def put(self, endpoint: Optional[str]=None) -> Awaitable[None]:
        await self.handle_request('PUT', endpoint)

    async def patch(self, endpoint: Optional[str]=None) -> Awaitable[None]:
        await self.handle_request('PATCH', endpoint)

    async def options(self, endpoint: Optional[str]=None) -> Awaitable[None]:
        await self.handle_request('OPTIONS', endpoint)


class OwsApiFilterHandler(_FilterHandlerMixIn, OwsApiHandler):
    pass


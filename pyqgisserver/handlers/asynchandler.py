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
from urllib.parse import urlencode

from ..logger import log_rrequest
from ..zeromq.client import RequestTimeoutError, RequestGatewayError, AsyncClient
from ..monitor import Monitor

from .basehandler import BaseHandler

from typing import Any, Optional, Awaitable, List, Dict

LOGGER = logging.getLogger('SRVLOG')

class AsyncClientHandler(BaseHandler):

    """ Proxy to Qgis 0MQ worker
    """
    def initialize(self, client: AsyncClient, timeout: int, 
                   monitor: Optional[Monitor]=None, 
                   allowed_hdrs: List[str]=[] ) -> None:

        super().initialize()

        self._client       = client
        self._timeout      = timeout
        self._monitor      = monitor
        self._stats        = self.application.stats
        self._allowed_hdrs = allowed_hdrs

        self.ogc_scheme   = None

    def encode_arguments(self) -> str:
        return '?'+urlencode({k:v[0] for k,v in self.request.arguments.items()})

    def set_backend_headers(self, headers: Dict) -> None:
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

    async def handle_request(self, method: str) -> Awaitable[None]:
        reqtime = time()

        try:
            meta = None
            response = None
            delta = None
            query = self.encode_arguments()

            headers = {}
            proxy_url = self.proxy_url()
            if proxy_url:
                # Send the full path to Qgis 
                headers['X-Forwarded-Url']=f"{proxy_url}{self.request.path.lstrip('/')}"

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

            meta = response.metadata

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

        # Send monitoring info
        self.emit( status, delta, meta or {})

    def emit(self, status: int, response_time: float, meta: Dict) -> None:
        if not self._monitor:
            return

        if meta:
            LOGGER.debug("### Adv. Metrics => %s", meta)

        params = self.get_monitor_params()
        if params:
            params.update(
                # RESPONSE TIME MUST BE IN MILLISECONDS
                RESPONSE_TIME = int(response_time*1000.0),
                RESPONSE_STATUS  = status,
                RESPONSE_MEMUSED = meta.get('mem_used',0)
            )
            self._monitor.emit( params, meta=self.request.headers )

    async def get(self) -> Awaitable[None]:
        """ Handle Get method
        """
        await self.handle_request('GET')

    async def post(self) -> Awaitable[None]:
        """ Handle Post method
        """
        await self.handle_request('POST')

    async def head(self) -> Awaitable[None]:
        """ Handle HEAD method
        """
        await self.handle_request('HEAD')

    def options(self) -> None:
        """ Implement OPTIONS for validating CORS
        """
        self.set_option_headers('GET, POST, OPTIONS')

    def get_monitor_params( self ) -> Optional[Dict[str,Any]]:
        """ Emit monitoring info
        """
        return None

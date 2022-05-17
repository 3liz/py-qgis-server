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

from typing import Any, Union, Optional, Awaitable, List, Dict

LOGGER = logging.getLogger('SRVLOG')


def _decode( b: Union[str,bytes] ) -> str:
    if not isinstance(b,str):
        return b.decode('utf-8')
    return b


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
            proxy_url = self.proxy_url(self._proxy)
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

class OwsHandler(AsyncClientHandler):

    def initialize(self, *args, getfeaturelimit: int=-1,  **kwargs) -> None:
        super().initialize(*args, **kwargs)
        self.getfeaturelimit = getfeaturelimit
        self.ogc_scheme = 'OWS'

    MONITOR_ARGUMENTS = (
        'MAP',
        'SERVICE',
        'REQUEST',
    )

    def get_monitor_params(self) -> Dict[str,Any]:
        """ Override
        """
        args = self.request.arguments
        params = { k:_decode(args.get(k,["__unknown__"])[0]) for k in self.MONITOR_ARGUMENTS }
        return params

    def prepare(self) -> None:
        super().prepare()
        # Replace query arguments to upper case: (it's ok for OWS)
        self.request.arguments = { k.upper():v for (k,v) in self.request.arguments.items() }

    def fix_getfeature(self, arguments: Dict) -> Dict:
        """ Take care of WFS/GetFeature limit

            Qgis does not set a default limit and unlimited
            request may cause issues
        """
        if self.getfeaturelimit > 0 \
                and arguments.get('SERVICE', b'').upper() == b'WFS' \
                and arguments.get('REQUEST', b'').lower() == b'getfeature':

            if arguments.get('VERSION', b'').startswith(b'2.'):
                key = 'COUNT'
            else:
                key = 'MAXFEATURES'

            limit = self.getfeaturelimit
            try:
                actual_limit = int(arguments.get(key,0))
                if actual_limit > 0:
                    limit =  min(limit, actual_limit)
            except ValueError:
                pass
            arguments[key] = str(limit).encode()

        return arguments

    def encode_arguments(self) -> str:
        arguments = {k:v[0] for k,v in self.request.arguments.items()}
        return '?'+urlencode(self.fix_getfeature(arguments))


class OwsApiHandler(AsyncClientHandler):
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



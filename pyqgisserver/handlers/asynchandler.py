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
from typing import Any, Dict, List, Optional, Union, cast
from urllib.parse import urlencode

from ..logger import log_rrequest
from ..monitor import MonitorABC
from ..zeromq.client import (
    AsyncClient,
    RequestGatewayError,
    RequestTimeoutError,
)
from .basehandler import BaseHandler

LOGGER = logging.getLogger('SRVLOG')


class AsyncClientHandler(BaseHandler):

    """ Proxy to Qgis 0MQ worker
    """

    def initialize(   # type: ignore [override]
        self,
        client: AsyncClient,
        timeout: int,
        monitor: Optional[MonitorABC] = None,
        allowed_hdrs: List[str] = [],
    ):
        super().initialize()

        self._client = client
        self._timeout = timeout
        self._monitor = monitor
        self._stats = self.application.stats  # type: ignore [attr-defined]
        self._allowed_hdrs = allowed_hdrs

        self.ogc_scheme: Union[str, None] = None

    def encode_arguments(self) -> str:
        return '?' + urlencode({k: v[0] for k, v in self.request.arguments.items()})

    def set_backend_headers(self, headers: Dict):
        """ Set headers passed to backend
        """
        project_path = self.get_argument('MAP', default=None)

        if project_path:
            headers['X-Map-Location'] = project_path
        if self.ogc_scheme:
            headers['X-Ogc-Scheme'] = self.ogc_scheme

        # Pass etag
        headers['If-None-Match'] = self.request.headers.get("If-None-Match", "")

        # Pass Accept
        # This header is used by QGIS Server WFS3 to get the content type
        # (html or json) if the request url does not have an extension
        # See: QgsServerOgcApiHandler::contentTypeFromRequest()
        headers['Accept'] = self.request.headers.get("Accept", "")

        def copy_headers(pats):
            headers.update((k, v) for k, v in self.request.headers.items() if
                           any(map(k.upper().startswith, pats)))

        # Copy custom Qgis/Forwarded headers
        # see https://github.com/qgis/QGIS/pull/41333
        copy_headers(self._allowed_hdrs)

    async def handle_request(self, method: str):
        reqtime = time()

        try:
            meta = None
            response = None
            delta = None
            query = self.encode_arguments()

            headers = {}
            proxy_url = self.proxy_url()
            req_url: Union[str, None]
            if proxy_url:
                # Send the full path to Qgis
                req_url = f"{proxy_url}{self.request.path.lstrip('/')}"
                headers['X-Qgis-Forwarded-Url'] = req_url
            else:
                req_url = self.request.uri

            self.set_backend_headers(headers)

            data: Optional[bytes] = self.request.body

            if self.get_argument('SERVICE', default=None) and self.has_body_arguments:
                # Do not let qgis server handle url encoded parameters
                data = None
                if method == 'POST':
                    method = 'GET'

            self._stats.num_requests += 1

            response = await self._client.fetch(
                query=query,
                method=method,
                headers=headers,
                data=data,
                timeout=self._timeout,
            )

            status = response.status
            hdrs = cast(Dict, response.headers)
            delta = time() - reqtime

            log_rrequest(req_url, status, method, query, delta, hdrs)

            # Send response
            for k, v in hdrs.items():
                self.set_header(k, v)

            # Send CORS Header
            self.set_access_control_headers()

            if status == 206:
                # Partial response
                self.set_status(200)
                if response.data:
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
            log_rrequest(req_url, 499, method, query, delta, {})
            self.send_error(status, reason="Request timeout error")
        except RequestGatewayError:
            status = 502
            delta = time() - reqtime
            # Log the request
            log_rrequest(req_url, 499, method, query, delta, {})
            self.send_error(status, reason="Backend request error")

        if status >= 500:
            self._stats.num_errors += 1

        # Send monitoring info
        self.emit(status, delta, meta or {})

    def emit(self, status: int, response_time: float, meta: Dict[str, str]):
        if not self._monitor:
            return

        if meta:
            LOGGER.debug("### Adv. Metrics => %s", meta)

        params = self.get_monitor_params()
        if params:
            params.update(
                # RESPONSE TIME MUST BE IN MILLISECONDS
                RESPONSE_TIME=int(response_time * 1000.0),
                RESPONSE_STATUS=status,
                RESPONSE_MEMUSED=meta.get('mem_used', 0),
            )
            self._monitor.emit(params, meta={k: v for k, v in self.request.headers.get_all()})

    async def get(self):
        """ Handle Get method
        """
        await self.handle_request('GET')

    async def post(self):
        """ Handle Post method
        """
        await self.handle_request('POST')

    async def head(self):
        """ Handle HEAD method
        """
        await self.handle_request('HEAD')

    def options(self):
        """ Implement OPTIONS for validating CORS
        """
        self.set_option_headers('GET, POST, OPTIONS')

    def get_monitor_params(self) -> Optional[Dict[str, Any]]:
        """ Emit monitoring info
        """
        return None

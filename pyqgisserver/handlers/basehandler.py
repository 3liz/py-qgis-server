#
# Copyright 2018 3liz
# Author: David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Base Request handler 
"""
import tornado.web
import logging
import json
from tornado.web import HTTPError # noqa F401
from typing import Any, Union, Optional

from ..version import __version__
from ..config import confservice

LOGGER = logging.getLogger('SRVLOG')


class BaseHandler(tornado.web.RequestHandler):
    """ Base class for HTTP request hanlers
    """
    def initialize(self) -> None:
        super().initialize()
        self._links    = []
        self.connection_closed = False
        self.logger = LOGGER
        self._cfg   = confservice['server']
        self._cross_origin = self._cfg.getboolean('cross_origin')

    def prepare(self) -> None:
        self.has_body_arguments = len(self.request.body_arguments)>0

    def compute_etag(self) -> None:
        # Disable etag computation
        pass

    def set_default_headers(self) -> None:
        """ Override defaults HTTP headers 
        """
        # XXX By default tornado set Content-Type to xml/text
        # this may have unwanted side effects
        self.clear_header("Content-Type")
        self.set_header("Server",f"Py-Qgis-Server {__version__}")

    def on_connection_close(self) -> None:
        """ Override, log and set 'connection_closed' to True
        """
        self.connection_closed = True
        self.logger.warning("Connection closed by client: {}".format(self.request.uri))

    def set_option_headers(self, allow_header: Optional[str]=None) -> None:
        """  Set correct headers for 'OPTION' method
        """
        if not allow_header:
            allow_header = ', '.join( me for me in self.SUPPORTED_METHODS if hasattr(self, me.lower()) )
        
        self.set_header("Allow", allow_header)
        if self.set_access_control_headers():
            # Required in CORS context
            # see https://developer.mozilla.org/fr/docs/Web/HTTP/M%C3%A9thode/OPTIONS
            self.set_header('Access-Control-Allow-Methods', allow_header)

    def set_access_control_headers(self) -> bool:
        """  Handle Access control and cross origin headers (CORS)
        """
        origin = self.request.headers.get('Origin')
        if origin:
            if self._cross_origin:
                self.set_header('Access-Control-Allow-Origin', '*')
            else:
                self.set_header('Access-Control-Allow-Origin', origin)
                self.set_header('Vary', 'Origin')
            return True
        else:
            return False

    def write_json(self, chunk: Union[str,dict]) -> None:
        """ Write body as json

            The method will also set CORS implicitely for any origin
            If this a security issue, we should allow it
            explicitely. 
        """
        if isinstance(chunk, dict):
            chunk = json.dumps(chunk, sort_keys=True)
        self.set_header('Content-Type', 'application/json;charset=utf-8')
        self.set_access_control_headers()
        self.write(chunk)

    def write_error(self, status_code: int, **kwargs: Any) -> None:
        """ Override, format error as json
        """
        message = self._reason

        #if "exc_info" in kwargs:
        #    exception = kwargs['exc_info'][1]
               
        self.logger.error("%s", message)
        response = dict(status="error" if status_code != 200 else "ok",
                        httpcode = status_code,
                        error    = { "message": message })

        self.write_json(response)
        self.finish()

    def proxy_url(self, http_proxy: bool) -> str:
        """ Return the proxy_url
        """
        # Replace the status url with the proxy_url if any
        req = self.request
        if http_proxy:
            # Replacement by static url, use it as base path
            proxy_url = self._cfg.get('proxy_url')
            if proxy_url:
                return f"{proxy_url.rstrip('/')}{req.path}"
        
            # Dynamic proxy url
            proxy_url = req.headers.get('X-Forwarded-Url')
            if proxy_url:
                return f"{proxy_url}"
        
        # No proxy to handle: return the full path
        return f"{req.protocol}://{req.host}{req.path}"



class NotFoundHandler(BaseHandler):
    def prepare(self):  # for all methods
        raise HTTPError(
            status_code=404,
            reason="Invalid resource path."
        )

class ErrorHandler(BaseHandler):
    def initialize(self, status_code: int, reason: Optional[str]=None) -> None:
        super().initialize()
        self.set_status(status_code)
        self.reason = reason

    def prepare(self) -> None:
        raise HTTPError(self._status_code, reason=self.reason)



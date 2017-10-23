""" Basei Request handler 
"""
import os
import tornado.web
import logging
import json
import traceback
from tornado.web import HTTPError

from ..version import __version__
from ..runtime import HTTPError2

LOGGER = logging.getLogger("QGSSRV")


class BaseHandler(tornado.web.RequestHandler):
    """ Base class for HTTP request hanlers
    """
    def initialize(self):
        super(BaseHandler,self).initialize()
        self._links    = []
        self.logger    = LOGGER
        self.connection_closed = False

    def compute_etag(self):
        # Disable etag computation
        pass

    def set_default_headers(self):
        """ Override defaults HTTP headers 
        """
        self.set_header("Server",__version__)

    def on_connection_close(self):
        """ Override, log and set 'connection_closed' to True
        """
        self.connection_closed = True
        self.logger.warning("Connection closed by client: {}".format(self.request.uri))

    def write_json(self, chunk):
        """ Write body as json

            The method will also set CORS implicitely for any origin
            If this a security issue, we should allow it
            explicitely. 
        """
        if isinstance(chunk, dict):
            chunk = json.dumps(chunk, sort_keys=True)
        self.set_header('Content-Type', 'application/json;charset=utf-8')   
        # Allow CORS on all origin
        if self.request.headers.get('Origin'):
            self.set_header('Access-Control-Allow-Origin', '*')
        self.write(chunk)

    def write_error(self, status_code, **kwargs):
        """ Override, format error as json
        """

        message = self._reason

        if "exc_info" in kwargs:
            exception = kwargs['exc_info'][1]
            # Error was caused by a exception
            if isinstance(exception, HTTPError2):
               errid = exception.kwargs.get("id","http_error")
               self.logger.error("%s", message)
            elif isinstance(exception, HTTPError):
               errid = "http_error"
            else:
                errid   = "exception"
                message = message or "{}".format(exception)
        else:
            errid = kwargs.get("id","unknown_error")
               
        response = dict(status="error" if status_code != 200 else "ok",
                        httpcode = status_code,
                        error    = {'id': errid, "message": message })

        self.write_json(response)
        self.finish()



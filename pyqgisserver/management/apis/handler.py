#
# Copyright 2021 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
    Wrapper around more tornado-like request handler for
    implementing Qgis server API
"""
import logging
import sys
import json
import traceback

from qgis.PyQt.QtCore import QRegularExpression, QUrl

from qgis.server import (
    QgsServerOgcApi,
    QgsServerOgcApiHandler,
    QgsServerRequest,
)

from tornado.web import HTTPError # noqa F401
from tornado import httputil

from typing import Any, Optional, Union, Tuple, Type, List

LOGGER = logging.getLogger('SRVLOG')


class RequestHandler:
  
    def __init__(self, context):
        self._context  = context
        self._response = context.response()
        self._request  = context.request()
        self._finished = False

    def prepare(self):
        """
        """

    def public_url(self, path="", rootpath: Optional[str]=None) -> str:
        """ Return the public base url
        """
        url = self._request.originalUrl()
        rootpath = rootpath or self._context.apiRootPath() 
        public_url = f"{url.scheme()}://{url.authority()}{rootpath}{path}"
        return public_url

    def finish(self, chunk: Optional[Union[str, bytes, dict]] = None) -> None:
        """
        """
        if self._finished:
            raise RuntimeError("finish() called twice")

        if chunk is not None:
            self.write(chunk)

        self._finished = True
        self._response.finish()
        
    def write(self, chunk: Union[str, bytes, dict]) -> None: 
        """
        """
        if not isinstance(chunk, (bytes, str, dict)):
            raise TypeError("write() only accepts bytes, unicode, and dict objects")
        if isinstance(chunk, dict):
            chunk = json.dumps(chunk, sort_keys=True)
        self.set_header('Content-Type', 'application/json;charset=utf-8')
        self._response.write(chunk) 

    def set_status(self, status_code: int, reason: Optional[str]=None) -> None:
        """
        """
        self._response.setStatusCode(status_code)
        if reason is not None:
            self._reason = reason
        else:
            self._reason = httputil.responses.get(status_code, "Unknown")

    def send_error(self, status_code: int = 500, **kwargs: Any) -> None:
        """
        """
        self._response.clear()
        reason = kwargs.get("reason")
        if "exc_info" in kwargs:
            exception = kwargs["exc_info"][1]
            if isinstance(exception, HTTPError) and exception.reason:
                reason = exception.reason
        self.set_status(status_code, reason=reason)
        self.write(dict(status="error" if status_code != 200 else "ok",
                        httpcode = status_code,
                        error    = { "message": self._reason }))
        if not self._finished:
            self.finish()
        
    def set_header(self, name: str, value: str) -> None:
        """
        """
        self._response.setHeader(name,value)

    def _unimplemented_method(self, *args: str, **kwargs: str) -> None:
        raise HTTPError(405)

    head   = _unimplemented_method
    get    = _unimplemented_method  
    post   = _unimplemented_method  
    delete = _unimplemented_method  
    patch  = _unimplemented_method 
    put    = _unimplemented_method  

    METHODS = {
        QgsServerRequest.HeadMethod  : 'head',
        QgsServerRequest.PutMethod   : 'put',
        QgsServerRequest.GetMethod   : 'get',
        QgsServerRequest.PostMethod  : 'post',
        QgsServerRequest.PatchMethod : 'patch',
        QgsServerRequest.DeleteMethod: 'delete',
    }

    def _execute(self, values):
        """ Execute the request
        """
        try:
            method = self._request.method()
            if method not in self.METHODS:
                raise HTTPError(405)

            self.prepare()
            if self._finished:
                return

            self.set_status(200)

            method = getattr(self, self.METHODS[method])            
            method( **values )

            if not self._finished:
                self.finish()
        except Exception as e:
            if self._finished:
                # Nothing to send, but log for debugging purpose
                LOGGER.error(traceback.format_exc())
                return
            if isinstance(e, HTTPError):
                self.send_error(e.status_code, exc_info=sys.exc_info())
            else:
                LOGGER.error(traceback.format_exc())
                self.send_error(500, exc_info=sys.exc_info())


class RequestHandlerDelegate(QgsServerOgcApiHandler):
    """ Delegate request to handler
    """

    # XXX We need to preserve instances from garbage
    # collection 
    __instances = []

    def __init__(self, path: str, handler: Type[RequestHandler], 
                 content_types=[QgsServerOgcApi.JSON,]):

        super().__init__()
        if content_types:
            self.setContentTypes(content_types)
        self._path = QRegularExpression(path)
        self._name = handler.__name__
        self._handler = handler

        self.__instances.append(self)

    def path(self):
        return self._path

    def linkType(self):
        return QgsServerOgcApi.data

    def operationId(self):
        return f"PyQgisServer{self._name}Management"

    def summary(self):
        return f"PyQgisServerManagement {self._name}  Service"

    def description(self):
        return f"PyQgisServerManagement {self._name } Service "

    def linkTitle(self):
        return f"PyQgisServerManagement {self._name } Service "

    def templatePath(self, context):
        # No templates!
        return ''

    def parameters(self, context):
        return []

    def handleRequest(self, context):
        """ 
        """
        handler = self._handler(context)
        handler._execute(self.values(context))


class _ServerApi(QgsServerOgcApi):

    __instances = []

    # See above
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

        self.__instances.append(self)

    def accept(self, url: QUrl) -> bool:
        """ Override the api to actually match the rootpath
        """
        return url.path().startswith( self.rootPath() )



def register_handlers(serverIface, rootpath: str, name: str, handlers: List[Tuple[str,Type[RequestHandler]]],
                      descripton: Optional[str]=None,
                      version: Optional[str]=None) -> None:

    api = _ServerApi(serverIface,rootpath, name, descripton, version)
    for (path,handler) in handlers:
        api.registerHandler(RequestHandlerDelegate(path,handler))

    serverIface.serviceRegistry().registerApi(api)




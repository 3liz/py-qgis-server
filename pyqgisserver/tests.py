#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import tornado.platform.asyncio
from tornado.testing import AsyncHTTPTestCase
import lxml.etree
import logging
import json

from typing import Any, Dict, Optional

from .config import load_configuration
from .runtime import (Application, 
                      create_poolserver,
                      create_broker_process,
                      configure_ipc_addresses)

LOGGER = logging.getLogger('SRVLOG')

NAMESPACES = {
    'xlink': "http://www.w3.org/1999/xlink",
    'wms': "http://www.opengis.net/wms",
    'wfs': "http://www.opengis.net/wfs",
    'wcs': "http://www.opengis.net/wcs",
    'wps': "http://www.opengis.net/wps/1.0.0",
    'ows': "http://www.opengis.net/ows/1.1",
    'gml': "http://www.opengis.net/gml",
    'xsi': "http://www.w3.org/2001/XMLSchema-instance"
}

class TestRuntime:

    def __init__(self) -> None:
        self.started = False
           
    def start(self) -> None:
        if self.started:
            return

        workers = 1
        load_configuration()        
        self.ipcaddr = configure_ipc_addresses(workers)
        self._broker = create_broker_process(self.ipcaddr)
        self._pool   = create_poolserver(workers)
        self.started = True

    def stop(self) -> None:
        if not self.started:
            return
        self._pool.terminate()
        self._broker.terminate()
        self._broker.join()

    @classmethod
    def instance(cls) -> 'TestRuntime':
        if not hasattr(cls,'_instance'):
            cls._instance = TestRuntime()
        return cls._instance


class HTTPTestCase(AsyncHTTPTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.logger   = LOGGER
        self.client   = OWSTestClient(self)

    def tearDown(self) -> None:
        self._application.terminate()
        super().tearDown()

    def get_app(self) -> Application:
        ipcaddr = TestRuntime.instance().ipcaddr
        self._application = Application(ipcaddr)
        return self._application
    
    def get_new_ioloop(self) -> tornado.platform.asyncio.AsyncIOLoop:
        """
        Needed to make sure that I can also run asyncio based callbacks in our tests
        """
        # Create a new IO loop et set it as default
        io_loop = tornado.platform.asyncio.AsyncIOLoop()
        asyncio.set_event_loop(io_loop.asyncio_loop)
        return io_loop


class HTTPTestResponse:

    def __init__(self, http_response) -> None:
        self.http_response = http_response
        if self.headers.get('Content-Type','').find('text/xml')==0:
            self.xml = lxml.etree.fromstring(self.content)

    @property
    def content(self) -> Any:
        return self.http_response.body

    @property
    def status_code(self) -> int:
        return self.http_response.code

    @property
    def headers(self):
        return self.http_response.headers

    def xpath(self, path: str) -> 'xpath':
        return self.xml.xpath(path, namespaces=NAMESPACES)

    def xpath_text(self, path: str) -> str:
        return ' '.join(e.text for e in self.xpath(path))

    def json(self) -> Any:
        return json.loads(self.content)


class OWSTestClient:

    def __init__(self, testcase: HTTPTestCase) -> None:
        self._testcase = testcase

    def post(self, data: Any, headers: Optional[Dict]=None, path: str='/ows/') -> HTTPTestResponse:
        return HTTPTestResponse(self._testcase.fetch(path, method='POST', body=data, raise_error=False,
                                headers=headers))

    def get(self, query: str, headers: Optional[Dict]=None, path: str='/ows/') -> HTTPTestResponse:
        return HTTPTestResponse(self._testcase.fetch(path + query, raise_error=False, 
                                headers=headers))

    def put(self, data: Any, headers: Optional[Dict]=None, path:  str='/ows/') -> HTTPTestResponse:
        return HTTPTestResponse(self._testcase.fetch(path, method='PUT', body=data, raise_error=False,
                                headers=headers))

    def post_xml(self, doc: lxml.etree.Element, headers: Optional[Dict]=None, path: str='/ows/') -> HTTPTestResponse:
        return self.post(data=lxml.etree.tostring(doc, pretty_print=True), 
                         headers=headers, path=path)

    def options( self, headers: Optional[Dict]=None, path: str='/ows/') -> HTTPTestResponse:
        return HTTPTestResponse(self._testcase.fetch(path, method='OPTIONS', 
                                headers=headers, raise_error=False))


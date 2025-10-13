#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging

import lxml.etree

from tornado.httpclient import HTTPResponse
from tornado.testing import AsyncHTTPTestCase
from typing_extensions import (
    ClassVar,
    Dict,
    Optional,
    Self,
    Union,
    cast,
)

from .config import load_configuration
from .runtime import (
    Application,
    configure_ipc_addresses,
    create_broker_process,
    create_poolserver,
    initialize_middleware,
)

LOGGER = logging.getLogger('SRVLOG')

NAMESPACES = {
    'xlink': "http://www.w3.org/1999/xlink",
    'wms': "http://www.opengis.net/wms",
    'wfs': "http://www.opengis.net/wfs",
    'wcs': "http://www.opengis.net/wcs",
    'wps': "http://www.opengis.net/wps/1.0.0",
    'ows': "http://www.opengis.net/ows/1.1",
    'gml': "http://www.opengis.net/gml",
    'xsi': "http://www.w3.org/2001/XMLSchema-instance",
}


class TestRuntime:

    _instance: ClassVar[Optional[Self]] = None

    def __init__(self) -> None:
        self.started = False

    def start(self) -> None:
        if self.started:
            return

        workers = 1
        load_configuration()
        self.ipcaddr = configure_ipc_addresses(workers)
        self._broker = create_broker_process(self.ipcaddr)
        self._pool = create_poolserver(workers)
        self.started = True

    def stop(self) -> None:
        if not self.started:
            return
        self._pool.terminate()
        self._broker.terminate()
        self._broker.join()

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cast(Self, cls._instance)


class HTTPTestCase(AsyncHTTPTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.logger = LOGGER
        self.client = OWSTestClient(self)

    def tearDown(self) -> None:
        self._application.terminate()
        super().tearDown()

    def get_app(self) -> Application:
        ipcaddr = TestRuntime.instance().ipcaddr
        self._application = Application(ipcaddr)
        return initialize_middleware(self._application)


class HTTPTestResponse:

    def __init__(self, http_response: HTTPResponse):
        self.http_response = http_response
        if self.headers.get('Content-Type', '').find('text/xml') == 0:
            self.xml = lxml.etree.fromstring(self.content)

    @property
    def content(self) -> Union[bytes, str]:
        return self.http_response.body

    @property
    def status_code(self) -> int:
        return self.http_response.code

    @property
    def headers(self):
        return self.http_response.headers

    def json(self) -> object:
        return json.loads(self.content)


class OWSTestClient:

    def __init__(self, testcase: HTTPTestCase) -> None:
        self._testcase = testcase

    def post(
        self,
        data: Union[bytes, str],
        headers: Optional[Dict] = None,
        path: str = '/ows/',
    ) -> HTTPTestResponse:
        return HTTPTestResponse(
            self._testcase.fetch(
                path, method='POST',
                body=data,
                raise_error=False,
                headers=headers,
            ),
        )

    def get(
        self,
        query: str,
        headers: Optional[Dict] = None,
        path: str = '/ows/',
    ) -> HTTPTestResponse:
        return HTTPTestResponse(
            self._testcase.fetch(
                path + query,
                raise_error=False,
                headers=headers,
            ),
        )

    def put(self,
        data: Union[bytes, str],
        headers: Optional[Dict] = None,
        path: str = '/ows/',
    ) -> HTTPTestResponse:
        return HTTPTestResponse(
            self._testcase.fetch(
                path,
                method='PUT',
                body=data,
                raise_error=False,
                headers=headers,
            ),
        )

    def post_xml(
        self,
        doc: lxml.etree._Element,
        headers: Optional[Dict] = None,
        path: str = '/ows/',
    ) -> HTTPTestResponse:
        return self.post(
            data=lxml.etree.tostring(doc, pretty_print=True),
            headers=headers,
            path=path,
        )

    def options(
        self,
        headers: Optional[Dict] = None,
        path: str = '/ows/',
    ) -> HTTPTestResponse:
        return HTTPTestResponse(
            self._testcase.fetch(
                path, method='OPTIONS',
                headers=headers,
                raise_error=False,
            ),
        )

    def head(
        self,
        query: str,
        headers: Optional[Dict] = None,
        path: str = '/ows/',
    ) -> HTTPTestResponse:
        return HTTPTestResponse(
            self._testcase.fetch(
                path + query,
                method='HEAD',
                headers=headers,
                raise_error=False,
            ),
        )

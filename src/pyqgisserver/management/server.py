#
# Copyright 2021 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
    Server management
"""
import logging
import os

from typing import Dict, Optional, cast
from urllib.parse import quote_plus

import tornado.web

from tornado.httpserver import HTTPRequest
from tornado.routing import _RuleList

from ..config import confservice
from ..handlers import BaseHandler, NotFoundHandler, StatusHandler
from ..handlers import OAPIHandler as QgisHandler
from ..logger import log_request
from ..qgscache.observer import Server as ObserverServer
from ..qgspool import WorkerPoolServer
from ..stats import Stats
from ..zeromq import client

LOGGER = logging.getLogger('SRVLOG')


class _PoolHandler(BaseHandler):

    def initialize(self, poolserver: WorkerPoolServer):  # type: ignore [override]
        super().initialize()
        self._poolserver = poolserver

    def options(self):
        """ Implement OPTION for validating CORS
        """
        self.set_option_headers()


class _RestartHandler(_PoolHandler):

    def post(self, action: str):
        """ Handle POST method
        """
        # Broadcast 'restart' to workers
        if action == 'restart':
            # Restart workers
            self._poolserver.restart()

        self.write_json({'status': 'ok'})


def _get_cache_link(key: str, req: HTTPRequest) -> str:
    """ Build cache link

        Take care of absolute path
        See https://github.com/3liz/py-qgis-server/issues/40
    """
    if key.startswith('/'):
        # Use MAP parameter
        return f"{req.protocol}://{req.host}/cache/content/?MAP={quote_plus(key)}"
    else:
        return f"{req.protocol}://{req.host}/cache/content/{quote_plus(key)}"


class _ReportHandler(_PoolHandler):

    async def get(self):
        """ Return worker reports
        """
        req = self.request
        reports = await self._poolserver.get_reports()
        for w in reports:
            for entry in w['cache']:
                entry.update(link=_get_cache_link(entry['key'], req))
        self.write_json({'workers': reports, 'num_workers': self._poolserver.num_workers})


class _RootHandler(BaseHandler):

    def get(self):
        """ Return links to default api entries
        """
        req = self.request

        def _link(path: str, title: str) -> Dict[str, str]:
            return {
                'href': f"{req.protocol}://{req.host}{path}",
                'title': title,
                'type': "application/json",
            }

        data = dict(
            links=[
                _link("/status", "Server status and configuration"),
                _link("/plugins", "Plugins managment"),
                _link("/cache", "Projects cache managment"),
                _link("/pool", "Workers pool status"),
            ],
        )
        self.write(data)

    def options(self):
        """ Implement OPTION for validating CORS
        """
        self.set_option_headers()


class _CacheHandler(QgisHandler):

    async def get(self, key: Optional[str] = None):
        """ Return project cache info
        """
        if not key:
            # Try to get key from param
            key = self.get_argument('MAP', default=None)

        cache_observer = cast(_Management, self.application).cache_observer
        if not key:
            """ Send the collection of cached objects
            """
            req = self.request

            def _link(key, item):
                return dict(
                    name=key,
                    last_modified=item.modified_time.astimezone().isoformat(),
                    link=_get_cache_link(key, req),
                )
            cached = [_link(key, item) for key, item in cache_observer.items()]
            self.write_json({'cached': cached})
            return
        else:
            if not cache_observer.find(key):
                self.send_error(404, reason=f"Project '{key}' not in cache")
                return

        # Delegate to server api
        await super().handle_request('GET')


def configure_handlers(
    poolserver: WorkerPoolServer,
    client: client.AsyncClient,
) -> _RuleList:
    """
    """
    kwargs = {
        'client': client,
        'timeout': confservice['server'].getint('timeout'),
        'service': 'Managment',
    }

    handlers: _RuleList = [
        (r"/", _RootHandler),
        (r"/status/?.*", StatusHandler),
        (r"/pool/(restart)", _RestartHandler, {'poolserver': poolserver}),
        (r"/pool/?", _ReportHandler, {'poolserver': poolserver}),
        (r"/cache/content/(?P<key>.+)", _CacheHandler, kwargs),
        (r"/cache/?", _CacheHandler, kwargs),
        # Forward to Qgis api handlers
        (r"/.+", QgisHandler, kwargs),
    ]
    return handlers


class _Management(tornado.web.Application):

    stats: Stats
    cache_observer: ObserverServer

    def __init__(self, poolserver: WorkerPoolServer, router: str):
        """
        """
        identity = bytes(f"MANAGEMENT-{os.getpid()}".encode('ascii'))
        self._broker_client = client.AsyncClient(router, identity)
        super().__init__(configure_handlers(poolserver, self._broker_client),
                         default_handler_class=NotFoundHandler)

        self.http_proxy = confservice.getboolean('server', 'http_proxy')

    def log_request(self, handler: tornado.web.RequestHandler):
        """ Write HTTP requet to the logs
        """
        log_request(handler)

    def terminate(self):
        self._broker_client.terminate()


def create_ssl_context(conf):
    import ssl
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(conf['ssl_cert'], conf['ssl_key'])
    return ssl_ctx


def start_management_server(poolserver: WorkerPoolServer, router: str) -> _Management:
    """ Start management server,
    """
    conf = confservice['management']

    port = conf.getint('port')
    address = conf['interfaces']

    LOGGER.info("MANAGEMENT: running server on %s:%s", address, port)

    kwargs = {}
    if conf.getboolean('ssl'):
        LOGGER.info("MANAGEMENT: SSL enabled")
        kwargs['ssl_options'] = create_ssl_context(conf)

    app = _Management(poolserver, router)
    app.listen(port, address=address, xheaders=True, **kwargs)

    return app

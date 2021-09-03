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
import os
import tornado.web
import logging

from ..logger import log_request
from ..config import confservice
from ..handlers import (BaseHandler, StatusHandler, OwsApiHandler as QgisHandler, NotFoundHandler)
from ..zeromq import client

from typing import Awaitable


LOGGER=logging.getLogger('SRVLOG')


class _PoolHandler(BaseHandler):

    def initialize(self, poolserver ) -> None:
        super().initialize()
        self._poolserver = poolserver

    def options(self) -> None:
        """ Implement OPTION for validating CORS
        """
        self.set_option_headers()


class _RestartHandler(_PoolHandler):

    def post(self, action) -> None:
        """ Handle POST method
        """
        # Broadcast 'restart' to workers
        if action == 'restart':
            # Restart workers
            self._poolserver.restart()

        self.write_json({ 'status': 'ok' }) 


class _ReportHandler(_PoolHandler):

    async def get(self) -> Awaitable[None]:
        """ Return worker reports
        """
        # Broadcast 'restart' to workers
        req = self.request
        reports = await self._poolserver.get_reports()
        for w in reports:
            for entry in w['cache']:
                entry.update(link=f"{req.protocol}://{req.host}/cache/{entry['key']}")

        self.write_json({'workers': reports, 'num_workers': self._poolserver.num_workers }) 

class _RootHandler(BaseHandler):

    def get(self) -> None:
        """ Return links to default api entries
        """
        req = self.request
        def _link( path: str, title: str ):
            return {
                'href' : f"{req.protocol}://{req.host}{path}",
                'title': title,
                'type' : "application/json",
            }

        data = dict(
            links=[
                _link("/status" , "Server status and configuration"),
                _link("/plugins", "Plugins managment"),
                _link("/cache"  , "Projects cache managment"),
                _link("/pool"   , "Workers pool status"),
            ]
        )
        self.write(data) 


    def options(self) -> None:
        """ Implement OPTION for validating CORS
        """
        self.set_option_headers()



def configure_handlers( poolserver, client: client.AsyncClient ) -> [tornado.web.RequestHandler]:
    """
    """
    kwargs =  {
        'client': client, 
        'timeout': confservice['server'].getint('timeout')
    }

    handlers = [
        (r"/"      , _RootHandler),
        (r"/status", StatusHandler),
        (r"/pool/(restart)", _RestartHandler, {'poolserver': poolserver}),
        (r"/pool/?"         ,_ReportHandler,  {'poolserver': poolserver}),
        # Forward to Qgis api handlers
        (r"/.+"             , QgisHandler, kwargs),
    ]
    return handlers


class _Management(tornado.web.Application):


    def __init__(self, poolserver, router: str) -> None:
        """
        """
        identity = bytes(f"MANAGEMENT-{os.getpid()}".encode('ascii'))
        self._broker_client = client.AsyncClient(router, identity)
        super().__init__(configure_handlers(poolserver, self._broker_client),
                         default_handler_class=NotFoundHandler)


    def log_request(self, handler: tornado.web.RequestHandler ) -> None:
        """ Write HTTP requet to the logs
        """
        log_request(handler)

    def terminate(self) -> None:
        self._broker_client.terminate()


def create_ssl_context( conf ):
    import ssl
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(conf['ssl_cert'],conf['ssl_key'])
    return ssl_ctx


def start_management_server( poolserver, router: str ) -> _Management:
    """ Start management server,
    """
    conf = confservice['management']

    port    = conf.getint('port')
    address = conf['interfaces']

    LOGGER.info("MANAGEMENT: running server on %s:%s",address,port)

    kwargs = {}
    if conf.getboolean('ssl'):
        LOGGER.info("MANAGEMENT: SSL enabled")
        kwargs['ssl_options'] = create_ssl_context(conf)

    app = _Management(poolserver, router)
    app.listen(port, address=address, xheaders=True, **kwargs)

    return app


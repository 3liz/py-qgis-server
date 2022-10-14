#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import asyncio
import logging
import signal

import tornado.web
import tornado.platform.asyncio

from tornado.web import RedirectHandler

from multiprocessing import Process

from .logger import log_request
from .config import confservice, qgis_api_endpoints

from .handlers import (StatusHandler, 
                       OwsHandler, 
                       OAPIHandler,
                       PingHandler, 
                       LandingPage,
                       NotFoundHandler)

from .zeromq import client, broker

from .qgspool import create_poolserver

from .monitor import Monitor
from .stats import Stats
from .qgscache.observer import declare_cache_observers, start_cache_observer


LOGGER=logging.getLogger('SRVLOG')


def configure_handlers( client: client.AsyncClient ) -> [tornado.web.RequestHandler]:
    """ Configure request handlers
    """
    cfg = confservice['server']

    monitor = Monitor.instance()

    ows_kwargs = dict(
        client       = client,
        monitor      = monitor,
        timeout      = cfg.getint('timeout'),
        allowed_hdrs = tuple(k.upper() for k in cfg.get('allow_headers').split(','))
    )

    end = r"(?:\.html|\.json|/?)"

    handlers = [
        (r"/", LandingPage),
        (r"/ping", PingHandler),
    ]

    def add_handler( path, handler, kwargs ):
        handlers.append( (path, handler, kwargs) )

    # Server status page
    if cfg.getboolean('status_page'):
        handlers.append( ("/status/?.*", StatusHandler) )

    def _ows_args( *args, **kwargs ):
        rv = ows_kwargs.copy()
        rv.update( *args, **kwargs )
        return rv

    add_handler(r"/ows/?", OwsHandler, _ows_args(getfeaturelimit=cfg.getint('getfeaturelimit')))

    wfs3_api_endpoints = [
        rf"{end}",
        rf"/collections(?:/[^/]+(?:/items)?)?{end}",
        rf"/conformance{end}",
        rf"/api{end}",
        r"/static/.*",
    ] 

    # XXX DEPRECATED (to be removed in 1.9)
    handlers.append((rf"/ows/wfs3({end}.*)", RedirectHandler, {'url': "/wfs3{0}" }))

    # New scheme
    kw = _ows_args(service='WFS3')
    for endpoint in wfs3_api_endpoints:
        handlers.append((rf"/wfs3{endpoint}", OAPIHandler, kw) )

    #
    # Add qgis api endpoints
    #
    for name, endpoint in qgis_api_endpoints():
        kw = _ows_args(service=name)
        LOGGER.debug("*** Adding API handler for: %s: %s", name, endpoint)        
        handlers.append( (rf"/{endpoint.strip('/')}/.*", OAPIHandler, kw) )

    return handlers


class Application(tornado.web.Application):

    def __init__(self, router: str) -> None:
        """
        """
        identity = confservice['zmq']['identity']
        identity = "{}-{}".format(identity,os.getpid())

        self._broker_client = client.AsyncClient(router, bytes(identity.encode('ascii')))
        self.stats = Stats()

        self.http_proxy = confservice.getboolean('server','http_proxy')

        super().__init__(configure_handlers(self._broker_client),
                         default_handler_class=NotFoundHandler)

    def log_request(self, handler: tornado.web.RequestHandler ) -> None:
        """ Write HTTP requet to the logs
        """
        log_request(handler)        

    def terminate(self) -> None:
        self._broker_client.terminate()


def setuid( username: str) -> None:
    """ setuid to username uid """
    from pwd import getpwnam, getpwuid
    pw = getpwnam(username)
    os.setgid(pw.pw_gid)
    os.setuid(pw.pw_uid)
    LOGGER.info("Setuid to user {} ({}:{})".format(getpwuid(os.getuid()).pw_name, os.getuid(), os.getgid()))


def create_broker_process( ipcaddr: str ) -> Process:
    """ Create a brker process
    """
    cfg = confservice['zmq']

    LOGGER.info("Starting broker process")
    p = Process(target=broker.run_broker, kwargs=dict(
                inaddr   = ipcaddr,
                outaddr  = cfg['bindaddr'],
                maxqueue = cfg.getint('maxqueue'),
                timeout  = cfg.getint('timeout')))
    p.start()
    return p


def configure_ipc_addresses(workers: int) -> str:
    """ Create ipc socket path
    """
    pid = os.getpid()
    ipc_path = f"/tmp/qgssrv/broker/{pid}/"
    os.makedirs(os.path.dirname(ipc_path), exist_ok=True)
    ipcaddr = f"ipc://{ipc_path}0"
    # Use ipc sockets for managed workers
    confservice.set('zmq','ipcpath', ipc_path)
    if workers > 0:
        confservice.set('zmq','bindaddr'     , f"ipc://{ipc_path}pool0")
        confservice.set('zmq','broadcastaddr', f"ipc://{ipc_path}broadcast0")

    return ipcaddr


def create_ssl_options():
    """ Create an ssl context
    """
    import ssl
    cfg = confservice['server']
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(cfg['ssl_cert'],cfg['ssl_key'])
    return ssl_ctx


def initialize_middleware( app ): 
    """ Initialize the middleware
    """
    if confservice.getboolean('server','enable_filters'):
        from .middleware import MiddleWareRouter
        router = MiddleWareRouter(app)
    else:
        router = app

    return router


def run_server( port: int, address: str="", user: str=None, workers: int=0) -> None:
    """ Run the server

        :param port: port number
        :param address: interface address to bind to (default to any)
        :user: User to setuid after opening ports (default no setuid)
    """
    import traceback
    from tornado.netutil import bind_sockets
    from tornado.httpserver import HTTPServer

    kwargs = {}

    ipcaddr = configure_ipc_addresses(workers)

    application = None
    server = None

    if user:
        setuid(user)

    worker_pool = None
    broker_pr = None
    cache_observer = None
    management = None

    # Setup ssl config
    if confservice.getboolean('server','ssl'):
        LOGGER.info("SSL enabled")
        kwargs['ssl_options'] = create_ssl_options()

    if confservice.getboolean('server','http_proxy'):
        LOGGER.info("Proxy configuration enabled")
        kwargs['xheaders'] = True

    # Check for declared cache observers
    declare_cache_observers()

    try:
        broker_pr   = create_broker_process(ipcaddr)
        worker_pool = create_poolserver(workers) if workers>0 else None

        # Since python 3.10 and deprecation of `get_event_loop()` 
        # This is now the preferred way to start tornado application
        # See https://www.tornadoweb.org/en/stable/guide/running.html
        async def _main():
            sockets = bind_sockets(port, address=address)

            LOGGER.info("Running server on port %s:%s", address, port)

            nonlocal application
            application = Application(ipcaddr)

            # Init HTTP server
            nonlocal server
            server = HTTPServer(initialize_middleware(application), **kwargs)
            server.add_sockets(sockets)

            # Activate management
            nonlocal management
            if confservice['management'].getboolean('enabled'):
                from .management.server import start_management_server
                management = start_management_server(worker_pool,ipcaddr)
                management.stats = application.stats

            # Initialize pool supervisor
            if worker_pool:
                worker_pool.start_supervisor()

            # Start cache observer
            nonlocal cache_observer
            cache_observer = start_cache_observer()

            if management:
                management.cache_observer = cache_observer

            event = asyncio.Event()

            loop = asyncio.get_running_loop()
            loop.add_signal_handler(signal.SIGTERM, event.set)
            
            LOGGER.info("Starting processing requests")
            # Wait forever until signal is set 
            # see https://www.tornadoweb.org/en/stable/guide/running.html
            await event.wait()

        # XXX This trigger a deprecation warning in python 3.10
        # but there is no clear alternative with tornado atm
        # See https://github.com/tornadoweb/tornado/issues/3033
        asyncio.run(_main())
    except Exception:
        print("Server exited from exception")
        traceback.print_exc()
        exit_code = 1
    except KeyboardInterrupt:
        print("Keyboard Interrupt", flush=True)
        exit_code = 15
    except SystemExit as exc:
        print("Exiting with code:", exc.code, flush=True)
        exit_code = exc.code
    else:
        exit_code = 0

    # Teardown
    if server is not None:
        server.stop()
    if management is not None:
        management.terminate()
        management = None
    if application is not None:
        application.terminate()
        application = None
        print("PID {}: Server instance stopped".format(os.getpid()), flush=True)
    if cache_observer:
        cache_observer.stop()
    if worker_pool:
        print("Stopping workers", flush=True)
        worker_pool.terminate()
    if broker_pr:
        print("Stopping broker", flush=True)
        broker_pr.terminate()
        broker_pr.join()

    print("Server shutdown", flush=True)
    sys.exit(exit_code)


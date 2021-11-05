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

from multiprocessing import Process

from typing import Optional, Mapping, List

from .logger import log_request
from .config import confservice, qgis_api_endpoints

from .handlers import (StatusHandler, 
                       OwsHandler, 
                       OwsFilterHandler, 
                       OwsApiHandler,
                       OwsApiFilterHandler,
                       PingHandler, 
                       NotFoundHandler)

from .zeromq import client, broker

from .utils import process
from .qgspool import create_poolserver

from .monitor import Monitor
from .stats import Stats

from pyqgisservercontrib.core.filters import ServerFilter

LOGGER=logging.getLogger('SRVLOG')


def load_access_policies() -> Optional[Mapping[str,List[ServerFilter]]]:
    """ Create filter list
    """
    if not confservice.getboolean('server','enable_filters'):
        return None

    confservice.set('server','access_policy_version','2')

    import pyqgisservercontrib.core.componentmanager as cm

    collection = []
    cm.register_entrypoints('qgssrv_contrib_access_policy', collection) 

    if not collection:
        return None

    # Retrieve filters
    filters = { "": [] }
    for filt in collection:
        uri = filt.uri or ""
        fls = filters.get(uri,[])
        fls.append(filt)
        filters[uri] = fls
    # Sort filters
    for flist in filters.values():
        flist.sort(key=lambda f: f.pri, reverse=True)
    return filters


def configure_handlers( client: client.AsyncClient ) -> [tornado.web.RequestHandler]:
    """ Configure request handlers
    """
    cfg = confservice['server']

    monitor = Monitor.initialize()

    root = r"/ows"

    ows_kwargs = {
        'client'      : client,
        'monitor'     : monitor,
        'timeout'     : cfg.getint('timeout'),
        'http_proxy'  : cfg.getboolean('http_proxy'),
        'allowed_hdrs': tuple(k.upper() for k in cfg.get('allow_headers').split(','))
    }

    end = r"(?:\.html|\.json|/?)"

    ows_api_endpoints = [
        rf"/wfs3{end}",
        rf"/wfs3/collections(?:/[^/]+(?:/items)?)?{end}",
        rf"/wfs3/conformance{end}",
        rf"/wfs3/api{end}",
        r"/wfs3/static/.*",
    ] 

    handlers = [
        (r"/ping", PingHandler),
    ]

    def add_handler( path, handler, kwargs ):
        LOGGER.debug("*** Adding handler for: %s", path)        
        handlers.append( (path, handler, kwargs) )

    # Server status page
    if cfg.getboolean('status_page'):
        handlers.append( ("/status/?", StatusHandler) )

    # Load filters
    filters = load_access_policies()
    if filters:
        for uri,fltrs in filters.items():
            kw = ows_kwargs.copy()
            kw.update( filters = fltrs)
            # Add ow endpoint
            path = f"{root}/{uri.strip('/')}" if uri else root
            # Add service endpoint
            add_handler( f"{path}(?P<endpoint>/?)", OwsFilterHandler, kw )
            for endp in ows_api_endpoints:
                add_handler( rf"{path}(?P<endpoint>{endp})", OwsApiFilterHandler, kw )
    else:
        add_handler( rf"{root}(?P<endpoint>/?)", OwsHandler, ows_kwargs)
        for endp in ows_api_endpoints:
            add_handler( rf"{root}(?P<endpoint>{endp})", OwsApiHandler, ows_kwargs )

    #
    # Add qgis api endpoints
    #
    for name,endpoint in qgis_api_endpoints():
        add_handler( rf"(?P<endpoint>/{endpoint.strip('/')}/.*)", OwsApiHandler, ows_kwargs )

    return handlers


class Application(tornado.web.Application):

    def __init__(self, router: str) -> None:
        """
        """
        identity = confservice['zmq']['identity']
        identity = "{}-{}".format(identity,os.getpid())

        self._broker_client = client.AsyncClient(router, bytes(identity.encode('ascii')))
        self.stats = Stats()

        super().__init__(configure_handlers(self._broker_client),
                         default_handler_class=NotFoundHandler)

    def log_request(self, handler: tornado.web.RequestHandler ) -> None:
        """ Write HTTP requet to the logs
        """
        log_request(handler)        

    def terminate(self) -> None:
        self._broker_client.terminate()


def terminate_handler( signum: int, frame ) -> None:
    if signum == signal.SIGTERM:
        if process.task_id() is None:
            sys.stderr.write("Terminating child processes.\n")
            process.terminate_childs()


def set_signal_handlers() -> None:
    signal.signal(signal.SIGTERM, terminate_handler)
    signal.signal(signal.SIGINT , terminate_handler)


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


def run_server( port: int, address: str="", jobs: int=1,  user: str=None, workers: int=0) -> None:
    """ Run the server

        :param port: port number
        :param address: interface address to bind to (default to any)
        :param jobs: Number of jobs to fork (default to 1: i.e no fork)
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

    worker_pool   = None
    broker_pr     = None

    # Setup ssl config
    if confservice.getboolean('server','ssl'):
        LOGGER.info("SSL enabled")
        kwargs['ssl_options'] = create_ssl_options()

    if confservice.getboolean('server','http_proxy'):
        LOGGER.info("Proxy configuration enabled")
        kwargs['xheaders'] = True

    # Run
    try:
        # Fork processes
        # This is a *DEPRECATED* feature
        if jobs > 1:

            def close_sockets(sockets):
                for sock in sockets:
                    sock.close()

            print(("DEPRECATION WARNING: "
                   "the 'jobs' option is deprecated "
                   "and will be removed in near future"),
                  file=sys.stderr, flush=True)

            sockets = bind_sockets(port, address=address)
            if  process.fork_processes(jobs) is None: # We are in the main process
                close_sockets(sockets)
                broker_pr   = create_broker_process(ipcaddr)
                worker_pool = create_poolserver(workers) if workers>0 else None
                set_signal_handlers()

                # Note that manage_processes(...) never return in main process 
                # and call exit(0) which will be caught by SystemExit exception
                process.manage_processes(max_restarts=5, logger=LOGGER)

                assert False, "Not Reached"
        else:
            broker_pr   = create_broker_process(ipcaddr)
            worker_pool = create_poolserver(workers) if workers>0 else None
            sockets = bind_sockets(port, address=address)

        LOGGER.info("Running server on port %s:%s", address, port)

        application = Application(ipcaddr)

        # Init HTTP server
        server = HTTPServer(application, **kwargs)
        server.add_sockets(sockets)

        management = None
        # Activate management
        if confservice['management'].getboolean('enabled'):
            from .management.server import start_management_server
            management = start_management_server(worker_pool,ipcaddr)
            management.stats = application.stats

        # Initialize pool supervisor
        worker_pool.start_supervisor()

        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGTERM, lambda: loop.stop())
        LOGGER.info("Starting processing requests")
        loop.run_forever()
    except Exception:
        traceback.print_exc()
        if process.task_id() is not None:
            # Let a chance to the child process to 
            # restart
            raise
        else: 
            # Make sure that child processes are terminated
            print("Terminating child processes", file=sys.stderr)
            process.terminate_childs()
    except KeyboardInterrupt:
        print("Keyboard Interrupt", file=sys.stderr)
    except SystemExit as exc:
        print(exc, file=sys.stderr )

    # Teardown
    if server is not None:
        server.stop()
    if management is not None:
        management.terminate()
        management = None
    if application is not None:
        application.terminate()
        application = None
        print("{}: Server instance stopped".format(os.getpid()), file=sys.stderr)
    if process.task_id() is None:
        if worker_pool:
            print("Stopping workers")
            worker_pool.terminate()
        if broker_pr:
            print("Stopping broker")
            broker_pr.terminate()
            broker_pr.join()


    print("Server shutdown", file=sys.stderr)

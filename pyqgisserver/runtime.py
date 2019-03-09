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
import traceback
import time

import tornado.web
import tornado.platform.asyncio

from multiprocessing import Process

from .logger import log_request
from .config import get_config, set_config, load_configuration

from .handlers import (RootHandler, OwsHandler)
from .zeromq import client, broker

from .utils import process

from .monitor import Monitor
from .profiles import ProfileMngr
from .broadcast import Broadcast

LOGGER=logging.getLogger('QGSRV')

def configure_handlers( client: client.AsyncClient ) -> [tornado.web.RequestHandler]:
    """
    """
    cfg = get_config('server')

    monitor = Monitor.initialize()

    ows_kwargs = {
        'client'     : client,
        'monitor'    : monitor,
        'timeout'    : cfg.getint('timeout'),
        'map_rewrite': cfg.get('map_rewrite'),
        'http_proxy'  : cfg.get('http_proxy') == 'yes', 
    }

    # Load profiles
    with_profiles = cfg.get('profiles')
    if with_profiles:
        ows_kwargs['profiles'] = ProfileMngr.initialize(with_profiles)

    handlers =[
        (r"/"          , RootHandler),
        (r"/ows/p/(.*)", OwsHandler, ows_kwargs),
        (r"/ows/"      , OwsHandler, ows_kwargs),
    ]

    return handlers


class Application(tornado.web.Application):

    def __init__(self, router, sockets):
        from tornado.httpserver import HTTPServer
        # Create 0MQ client
        identity = get_config('zmq')['identity']
        identity = "{}-{}".format(identity,os.getpid())

        self._zmq_client = client.AsyncClient(router, bytes(identity.encode('ascii')))

        super().__init__(configure_handlers(self._zmq_client))
                
        # Init HTTP server
        server = HTTPServer(self)
        server.add_sockets(sockets)
        self._http_server = server

        self._broadcast = Broadcast()
        self._broadcast.init()

    def log_request(self, handler: tornado.web.RequestHandler ) -> None:
        """ Write HTTP requet to the logs
        """
        log_request(handler)        

    def terminate(self) -> None:
        self._http_server.stop()
        self._http_server = None
        self._zmq_client.terminate()
        self._broadcast.close()

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
    cfg = get_config('zmq')

    LOGGER.info("Starting broker process")
    p = Process(target=broker.run_broker, kwargs=dict(
            inaddr   = ipcaddr,
            outaddr  = cfg['bindaddr'],
            maxqueue = cfg.getint('maxqueue'),
            timeout  = cfg.getint('timeout')
    ))
    p.start()
    return p


def create_worker_pool( workers: int ) -> Process:
    """ Run workers pool in its own process

        This ensure that sub-processes all always forked from
        the same parent context
 
        This will prevent forking zmq context.
        If we do not do this, forked workers cannot
        reconnect when forked from running ZMQ context.
    """
    p = Process(target=run_worker_pool,args=(workers,))
    p.start()
    return p

def run_worker_pool(workers: int) -> None:
    """ Run a qgis worker pool
    """
    from .qgspool import Pool

    # Try to exit gracefully
    def term_signal(signum,frames):
        print("Caught signal: %s" % signum, file=sys.stderr)
        raise SystemExit()

    # Handle critical failure by sending ABORT to
    # parent process
    def abrt_signal(signum,frames):
        print("Server aborting prematurely !", file=sys.stderr)
        os.kill(os.getppid(), signal.SIGABRT)

    signal.signal(signal.SIGTERM,term_signal)
    signal.signal(signal.SIGABRT,abrt_signal)

    LOGGER.info("Starting worker pool")
    router        = get_config('zmq')['bindaddr'] 
    broadcastaddr = get_config('zmq')['broadcastaddr']
    pool = Pool(router, workers, broadcastaddr=broadcastaddr)
    try:
        while True:
            time.sleep(20)
    except (KeyboardInterrupt,SystemExit):
        LOGGER.warning("Pool Interrupted")
    finally:
        pool.terminate()

    

def run_server( port: int, address: str="", jobs: int=1,  user: str=None, workers: int=0) -> None:
    """ Run the server

        :param port: port number
        :param address: interface address to bind to (default to any)
        :param jobs: Number of jobs to fork (default to 1: i.e no fork)
        :user: User to setuid after opening ports (default no setuid)
    """
    import traceback
    from tornado.netutil import bind_sockets

    # Create ipc socket path 
    ipc_path = '/tmp/qgssrv/broker/'
    os.makedirs(os.path.dirname(ipc_path), exist_ok=True)
    ipcaddr = 'ipc://'+ipc_path+'0'
    # Use ipc sockets for managed workers
    if workers > 0:
        set_config('zmq','bindaddr'     , 'ipc://'+ipc_path+'pool0')
        set_config('zmq','broadcastaddr', 'ipc://'+ipc_path+'broadcast0')

    application = None

    if user:
       setuid(user)

    def close_sockets(sockets):
        for sock in sockets:
            sock.close()

    worker_pool = None
    broker_pr   = None

    # Run
    try:
        # Fork processes
        if jobs > 1:
            sockets = bind_sockets(port, address=address)
            if  process.fork_processes(jobs) is None: # We are in the main process
                close_sockets(sockets)
                broker_pr   = create_broker_process(ipcaddr)
                worker_pool = run_worker_pool(workers) if workers>0 else None
                set_signal_handlers()

                # Note that manage_processes(...) never return in main process 
                # and call exit(0) which will be caught by SystemExit exception
                task_id = process.manage_processes(max_restarts=5, logger=LOGGER)

                assert False, "Not Reached"
        else:
            broker_pr   = create_broker_process(ipcaddr)
            worker_pool = create_worker_pool(workers) if workers>0 else None
            sockets = bind_sockets(port, address=address)

        # Install asyncio event loop after forking
        # This is why we do not use server.bind/server.start
        tornado.platform.asyncio.AsyncIOMainLoop().install()

        LOGGER.info("Running server on port %s:%s", address, port)
        # Run the server
        application = Application(ipcaddr, sockets)
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGTERM, lambda: loop.stop())
        asyncio.get_event_loop().run_forever()
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
    except (KeyboardInterrupt, SystemExit) as e:
        pass

    # Teardown
    if application is not None:
        application.terminate()
        application = None
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            loop.close()
        print("{}: Server instance stopped".format(os.getpid()), file=sys.stderr)

    if process.task_id() is None:
        if worker_pool:
            print("Stopping workers")
            worker_pool.terminate()
            worker_pool.join()
        if broker_pr:
            print("Stopping broker")
            broker_pr.terminate()
            broker_pr.join()
        print("Server shutdown", file=sys.stderr)

   


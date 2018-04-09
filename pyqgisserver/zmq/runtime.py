# -*- encoding=utf-8 -*-
import os
import sys
import asyncio
import logging
import signal
import traceback

import tornado.web
import tornado.process


from ..logger import log_request
from ..config import get_config, load_configuration

from .handlers import (RootHandler, OwsServerHandler)
from .client import AsyncClient

LOGGER=logging.getLogger('QGSRV')


def configure_handlers( client ):
    """
    """
    handlers = []
    handlers.extend([
        (r"/"    , RootHandler),
        (r"/ows/", OwsServerHandler, {'client': client})
    ])

    return handlers


class Application(tornado.web.Application):

    def __init__(self, router, sockets):
        from tornado.httpserver import HTTPServer
        # Create 0MQ client
        identity = get_config('zmq')['identity']
        identity = "{}-{}".format(identity,os.getpid())

        self._zmq_client = AsyncClient(router, bytes(identity.encode('ascii')))

        super().__init__(configure_handlers(self._zmq_client))
                
        # Init HTTP server
        server = HTTPServer(self)
        server.add_sockets(sockets)
        self._http_server = server 

    def log_request(self, handler):
        """ Write HTTP requet to the logs
        """
        log_request(handler)        

    def terminate(self):
        self._http_server.stop()
        self._http_server = None
        self._zmq_client.terminate()


def terminate_handler(signum, frame):
    """ Terminate child processes """
    if 'children' in frame.f_locals and signum == signal.SIGTERM:
        sys.stderr.write("Terminating child processes.\n")
        for p in frame.f_locals['children']:
            os.kill(p, signal.SIGTERM)

    raise SystemExit("caught signal %s", signum)


def set_signal_handlers():
    signal.signal(signal.SIGTERM, terminate_handler)


def clear_signal_handlers():
    signal.signal(signal.SIGTERM, signal.SIG_DFL)


def setuid(username):
    """ setuid to username uid """
    from pwd import getpwnam, getpwuid
    pw = getpwnam(username)
    os.setgid(pw.pw_gid)
    os.setuid(pw.pw_uid)
    LOGGER.info("Setuid to user {} ({}:{})".format(getpwuid(os.getuid()).pw_name, os.getuid(), os.getgid()))


def create_broker_process( ipcaddr ):
    """ Create a brker process
    """
    from multiprocessing import Process
    from .broker import run_broker

    cfg = get_config('zmq')

    LOGGER.info("Starting broker process")
    os.makedirs('/tmp/qgssrv/broker', exist_ok=True)
    p = Process(target=run_broker, kwargs=dict(
            inaddr   = ipcaddr,
            outaddr  = cfg['bindaddr'],
            maxqueue = cfg.getint('maxqueue'),
            timeout  = cfg.getint('timeout')
    ))
    p.start()
    return p

def run_server( port, address="", jobs=1,  user=None):
    """ Run the server

        :param port: port number
        :param address: interface address to bind to (default to any)
        :param jobs: Number of jobs to fork (default to 1: i.e no fork)
        :user: User to setuid after opening ports (default no setuid)
    """
    import traceback
    from tornado.netutil import bind_sockets

    ipcaddr = "ipc:///tmp/qgssrv/broker/0"

    broker_pr = create_broker_process(ipcaddr)

    sockets = bind_sockets(port, address=address)

    application = None
    ppid = os.getpid()

    if user:
       setuid(user)

    set_signal_handlers()

    # Fork processes
    if jobs > 1:
        import tornado.process
        tornado.process.fork_processes(jobs, max_restarts=5)
        task_id = tornado.process.task_id()
    else:
        task_id = ppid

    # Install asyncio event loop after forking
    # This is why we do not use server.bind/server.start
    import tornado.platform.asyncio
    tornado.platform.asyncio.AsyncIOMainLoop().install()

    # Run
    try:
        clear_signal_handlers()
        LOGGER.info("Running server on port %s:%s", address, port)
        try:
            if task_id is not None:
                # Run the server
                application = Application(ipcaddr, sockets)
                loop = asyncio.get_event_loop()
                loop.add_signal_handler(signal.SIGTERM, lambda: loop.stop())
                asyncio.get_event_loop().run_forever()
        except Exception:
            traceback.print_exc()
    except (KeyboardInterrupt, SystemExit) as e:
        print("%s" % e, file=sys.stderr)

    # Teardown
    pid = os.getpid()
    if application is not None:
        application.terminate()
        application = None
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            loop.close()
        print("{}: Worker stopped".format(pid), file=sys.stderr)

    if ppid == pid:
        print("Stopping broker")
        broker_pr.terminate()
        broker_pr.join()
        print("Server shutdown", file=sys.stderr)

   


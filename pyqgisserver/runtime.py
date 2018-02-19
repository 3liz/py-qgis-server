# -*- encoding=utf-8 -*-
import os
import sys
import asyncio
import logging
import signal
import traceback

import tornado.web
import tornado.process

from .logger import log_request
from .config import get_config, load_configuration
from .handlers import (RootHandler, QgsServerHandler)
from .utils.qgis import init_qgis_server

LOGGER=logging.getLogger('QGSRV')


def configure_handlers():
    """
    """

    handlers = []

    handlers.extend([
        (r"/"    , RootHandler),
        (r"/ows/", QgsServerHandler)
    ])

    return handlers


class Application(tornado.web.Application):
    
    def __init__(self, qgsserver):
        super().__init__(configure_handlers(), qgsserver=qgsserver)

    def log_request(self, handler):
        """ Write HTTP requet to the logs
        """
        log_request(handler)        

  

def terminate_handler(signum, frame):
    """ Terminate child processes """
    if 'children' in frame.f_locals and signum == signal.SIGTERM:
        sys.stderr.write("Terminating child processes.\n")
        for p in frame.f_locals['children']:
            os.kill(p, signal.SIGTERM)

    raise SystemExit(u"{}: Caught signal {}".format(os.getpid(), signum))


def setuid(username):
    """ setuid to username uid """
    from pwd import getpwnam, getpwuid
    pw = getpwnam(username)
    os.setgid(pw.pw_gid)
    os.setuid(pw.pw_uid)
    LOGGER.info("Setuid to user {} ({}:{})".format(getpwuid(os.getuid()).pw_name, os.getuid(), os.getgid()))


def set_signal_handlers():
    signal.signal(signal.SIGTERM, terminate_handler)
    signal.signal(signal.SIGINT,  terminate_handler)


def run_server( port, address="", jobs=1,  user=None):
    """ Run the server

        :param port: port number
        :param address: interface address to bind to (default to any)
        :param jobs: Number of jobs to fork (default to 1: i.e no fork)
        :user: User to setuid after opening ports (default no setuid)
    """
    import traceback
    from tornado.netutil import bind_sockets
    from tornado.httpserver import HTTPServer

    sockets = bind_sockets(port, address=address)

    server = None

    ppid = os.getpid()

    if user:
       setuid(user)
    # Fork processes
    if jobs > 1:
        import tornado.process
        tornado.process.fork_processes(jobs, max_restarts=10)
        task_id = tornado.process.task_id()
    else:
        task_id = ppid

    # Install asyncio event loop after forking
    # This is why we do not use server.bind/server.start
    import tornado.platform.asyncio
    tornado.platform.asyncio.AsyncIOMainLoop().install()

    # Run
    try:
        set_signal_handlers()
        LOGGER.info("Running server on port %s:%s", address, port)
        try:
            if task_id is not None:
                LOGGER.debug("Initializing qgis server")
                qgis_conf = get_config('qgis')
                qgsserver = init_qgis_server( network_timeout=qgis_conf.getint('network_timeout'), 
                                enable_processing=False, logger=LOGGER, verbose=LOGGER.level<=logging.DEBUG)
                # Run the server
                server = HTTPServer(Application(qgsserver))
                server.add_sockets(sockets)
                LOGGER.info("QGIS Server ready")
                asyncio.get_event_loop().run_forever()
        except Exception:
            traceback.print_exc()

    except SystemExit as e:
        print("%s" % e, file=sys.stderr)

    # Teardown
    pid = os.getpid()
    if server is not None:
        server.stop()
        server = None
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            loop.close()
        print("{}: Worker stopped".format(pid), file=sys.stderr)
    
    if ppid == pid:
        print("Server shutdown", file=sys.stderr)

   


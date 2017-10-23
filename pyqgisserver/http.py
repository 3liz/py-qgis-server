# -*- encoding=utf-8 -*-
import os
import sys
import tornado.web
import tornado.process
import tornado.ioloop
import logging
import signal
from tornado import gen
from tornado.httpclient import AsyncHTTPClient
from contextlib import contextmanager

from .logger import log_request, log_rrequest
from .config import read_configuration


class HTTPError2(tornado.web.HTTPError):
    def __init__(self, status_code=500, log_message=None, *args, **kwargs):
        super(HTTPError2,self).__init__(status_code=status_code,
                                        log_message=log_message,
                                        *args,**kwargs)
        self.kwargs = kwargs



@gen.coroutine
def wget(url, **kwargs):
    """ Return an async request
    """
    http_client = AsyncHTTPClient()
    response = yield http_client.fetch(url, raise_error=False, **kwargs)
    log_rrequest(response)
    links = [{"href": url}]
    if response.code == 599:
        raise HTTPError2(504, id="backend_timeout", links=links)  
    elif response.code != 200:
       raise HTTPError2(502, id="backend_error", links=links)

    raise gen.Return(response)


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
    logging.info("Setuid to user {} ({}:{})".format(getpwuid(os.getuid()).pw_name, os.getuid(), os.getgid()))


def set_signal_handlers():
    signal.signal(signal.SIGTERM, terminate_handler)
    signal.signal(signal.SIGINT,  terminate_handler)


class Application(tornado.web.Application):
    
    def bind(self, port, address="", jobs=1, user=None):
        """ Bind sockets and fork process

            :param port: port number
            :param address: interface address to bind to (default to any)
            :param jobs: Number of jobs to fork (default to 1: i.e no fork)
            :user: User to setuid after opening ports (default no setuid)

            :return task_id if in forked process, otherwise None. 
        """
        from tornado.netutil import bind_sockets
        from tornado.httpserver import HTTPServer
        sockets = bind_sockets(port, address=address)
        if user is not None:
            setuid(user)
        # Fork processes
        if jobs > 1:
            import tornado.process
            tornado.process.fork_processes(jobs, max_restarts=3)
            task_id = tornado.process.task_id()
        else:
            task_id = os.getpid()
        if task_id is not None:
            server = HTTPServer(self)
            server.add_sockets(sockets)
        return task_id

    def log_request(self, handler):
        """ Write HTTP requet to the logs
        """
        log_request(handler)        


@contextmanager
def run_application_context( handlers, config, **settings ):
    """ Start application and run io_loop

        All code inside the context is executed at post-fork time and before
        running ioloop.
    """
    import traceback
    task_id = None
    app = Application(handlers, config=config,  **settings)
    try:
        set_signal_handlers()
        task_id = app.bind(config.getint("port"), address=config.interfaces, jobs=config.getint("workers"),
                           user=config.setuid)
        if task_id is not None:
            yield task_id
            try:
                ioloop = tornado.ioloop.IOLoop.current()
                ioloop.start()
            except Exception:
                traceback.print_exc()
    except SystemExit as e: 
        sys.stderr.write(e.message+"\n")
   
    if task_id is not None:
        sys.stderr.write("[{}] Worker stopped\n".format(os.getpid()))
    else:
        yield None
        sys.stderr.write("Server shutdown\n")
        
   


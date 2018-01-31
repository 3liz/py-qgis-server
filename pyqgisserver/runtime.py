# -*- encoding=utf-8 -*-
import os
import sys

import asyncio

import tornado.web
import tornado.process

import logging
import signal

from contextlib import contextmanager
from .logger import log_request, setup_log_handler
from .config import get_config, load_configuration, read_config_file, read_config_dict

LOGGER=logging.getLogger('QGSRV')


def print_version():
    from .version import __version__
    program = os.path.basename(sys.argv[0])
    print("{name} {version}".format(name=program, version=__version__,file=sys.stderr))


def read_configuration(args=None, cli_parser=None):
    """ Parse command line and read configuration file
    """
    if args is None:
        args = sys.argv

    config_file = None

    load_configuration()

    if cli_parser:
        conf  = get_config('server')
        cli_parser.add_argument('--logging', choices=['debug', 'info', 'warning', 'error'], 
                default=get_config('logging')['level'].lower(), help="set log level")
        cli_parser.add_argument('-c','--config', metavar='PATH', nargs='?', dest='config',
                default=None, help="Configuration file")
        cli_parser.add_argument('--version', action='store_true', 
                default=False, help="Return version number and exit")
        cli_parser.add_argument('-p','--port'    , type=int, help="http port", dest='port', default=conf['port'])
        cli_parser.add_argument('-b','--bind'    , metavar='IP',  default=conf['interfaces'], help="Interface to bind to", dest='interface')
        cli_parser.add_argument('-w','--workers' , metavar='NUM', default=conf.getint('workers'), help="Num workers", dest='workers')
        cli_parser.add_argument('-u','--setuid'  , default='', help="uid to switch to", dest='setuid')

        args = cli_parser.parse_args()

        if args.version:
            print_version()
            sys.exit(1)

        log_level = args.logging
        if args.config:
            read_config_file(args.config)

        cli_config = {
            'server':{
                'port': str(args.port),
                'interfaces': str(args.interface),
                'workers'   : str(args.workers),
                'setuid'    : args.setuid,
            },
            'logging':{
                'level': args.logging.upper()
            }
        }

        # read configuration dict
        read_config_dict(cli_config)

    print_version()

    # set log level
    setup_log_handler(log_level)
    print("Log level set to {}\n".format(logging.getLevelName(LOGGER.level)), file=sys.stderr)

    return args
    

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

        LOGGER.info('Binding on port %s:%s' % (address or '*', port))
        sockets = bind_sockets(port, address=address)
        
        self.server = None

        if user:
            setuid(user)
        # Fork processes
        if jobs > 1:
            import tornado.process
            tornado.process.fork_processes(jobs, max_restarts=3)
            task_id = tornado.process.task_id()
        else:
            task_id = 0

        # Install asyncio event loop
        import tornado.platform.asyncio
        tornado.platform.asyncio.AsyncIOMainLoop().install()

        # Return a kickstart callable
        # that must be started after fork
        if task_id is not None:
            def kickstart():
                self.server = HTTPServer(self)
                self.server.add_sockets(sockets)
                asyncio.get_event_loop().run_forever()

            kickstart.task_id = task_id
            return kickstart

    def log_request(self, handler):
        """ Write HTTP requet to the logs
        """
        log_request(handler)        

    def teardown(self):
        """ Release resources
        """
        # Close sockets
        if self.server is not None:
            self.server.stop()
            self.server = None

        # Close event loop
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            loop.close()


@contextmanager
def run_application_context( handlers, **settings ):
    """ Start application and run io_loop

        All code inside the context is executed at post-fork time and before
        running ioloop.

        :return: A pid of the current (forked) worker process
    """
    import traceback

    app = Application(handlers, **settings)
    config = get_config('server')

    run = None
    try:
        set_signal_handlers()
        run = app.bind(port=config.getint('port'), address=config['interfaces'], jobs=config.getint('workers'),
                       user=config.get('setuid'))

        if run is not None:
            yield run.task_id
            try:
                run()
            except Exception:
                traceback.print_exc()
   
    except SystemExit as e:
        sys.stderr.write("%s\n" % e)

    app.teardown()

    if run is not None:
        sys.stderr.write("{}: Worker {} stopped\n".format(os.getpid(), run.task_id))
    else:
        yield None
        sys.stderr.write("Server shutdown\n")
        
   


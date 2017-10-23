# -*- encoding=utf-8 -*-
#
# Copyrights 2106 3Liz  
# Author: David Marteau (dmarteau@3liz.com)
#
"""
    WMS Qgis server with AMQP support.

    Run a synchronous AMQP worker and handle WMS/WFS requests 
    to qgis server
"""
from __future__ import print_function
import sys
import os
import logging
import signal
import traceback

from tornado.ioloop import IOLoop
from tornado import gen

from ..amqp.concurrent import AsyncConnection, AsyncRPCWorker, AsyncSubscriber
from ..amqp.logger import Handler as LogChannel 
from .config import read_configuration

import service


def terminate_handler(signum, frame):
    raise SystemExit(u"{}: Caught signal {}".format(os.getpid(), signum))


def set_signal_handler():
    signal.signal(signal.SIGTERM, terminate_handler)
    signal.signal(signal.SIGINT , terminate_handler)


def create_amqp_logger(config, connection):
    """ Create amqp logger channel 
    """
    channel = LogChannel(connection=connection, 
                         exchange=config['logger_exchange'],
                         routing_key='.'.join(('log',config['workspace'],'%(levelname)s')))

    logger = logging.getLogger('qgis_logger')  
    logger.addHandler(channel)
    logger.setLevel(getattr(logging, config.loglevel.upper())) 

    # Propagate only to ancestor in debug mode
    logger.propagate = (config.loglevel == 'debug')

    return logger


def run_worker():
    """ Run worker loop """
    config = read_configuration()

    # Set handlers 
    set_signal_handler()

    try:
        # Create connection
        connection = AsyncConnection(host=config['amqp_host'])

        # Create amqp_logger
        create_amqp_logger(config, connection)

        @gen.coroutine
        def connect():
            worker = AsyncRPCWorker(connection=connection)
            yield worker.connect(service.app, routing_key=config["worker_key"])

            subscr = AsyncSubscriber(connection=connection)
            yield subscr.connect(exchange=config['notify_exchange'],
                                 routing_keys=config['notify_key'],
                                 exchange_type='direct',
                                 handler=service.notify)

            logging.info("Worker ready")
           
        def handle_exception(f):
            exc_info = f.exc_info()
            if exc_info is not None:
                traceback.print_exception(*exc_info)
                sys.exit(20)

        # Setup qgis service
        service.setup(config)
        
        ioloop = IOLoop.current()
        ioloop.add_future(connect(),handle_exception) 
        ioloop.start()
    except SystemExit as e:
        print(e.message, file=sys.stderr) 
        # Exit nicely
        connection.close()


def run_logger():
    """ Client to amqp logger

        Dump log to stdout
    """
    import argparse
    from .config import default_config
    from ..config import read_configuration

    # Set handlers 
    set_signal_handler()

    parser = argparse.ArgumentParser(description="AMQP log client")
    parser.add_argument("--key",nargs='?', default="log.*.*", help="Routing key")
    parser.add_argument("--noop",action='store_true', default=False, help="Dump config")

    config, args = read_configuration(cli_parser=parser, default_config=default_config)    

    if args.noop:
        print("\n#### Configuration:\n")
        print(config.dumps())
        sys.exit(1)

    client = AsyncSubscriber(host=config['amqp_host'])

    def handle_exception(f):
        exc_info = f.exc_info()
        if exc_info is not None:
            traceback.print_exception(*exc_info)
            sys.exit(20)

    ioloop = IOLoop.current()
    ioloop.add_future(client.connect(exchange=config['logger_exchange'], 
                                    exchange_type=None,
                                    routing_keys=[args.key],
                                    handler=lambda r: print(r.body)),
                                    handle_exception)
    try:
         ioloop.start()
    except SystemExit as e:
        print(e.message, file=sys.stderr) 
        # Exit nicely
        client.close()




""" Load balancer/proxy to morker processes

    Implement ZMQ ROUTER/ROUTER broker for connecting client DEALER 
    to workers DEALER
"""

import sys
import asyncio
import zmq
import logging
import traceback

from time import sleep
from collections import deque

from .messages import WORKER_READY

from ..version import __description__, __version__
from ..logger import setup_log_handler

LOGGER=logging.getLogger('QGSRV')


def run_broker( inaddr, outaddr, maxqueue=100):
    """ Create a ROUTER-ROUTER broker

        :param inaddr: frontend address to bind to
        :param outaddr: backend address to bind to

        If the max number of waiting request is reached: extra incoming requests will
    """
 
    context  = zmq.Context.instance()

    LOGGER.info("Binding frontend to %s", inaddr)
    frontend = context.socket(zmq.ROUTER)
    frontend.setsockopt(zmq.LINGER, 500)
    frontend.setsockopt(zmq.ROUTER_MANDATORY,1)
    frontend.bind(inaddr)

    LOGGER.info("Binding backend to %s", outaddr)
    backend = context.socket(zmq.ROUTER)
    backend.setsockopt(zmq.LINGER, 500)
    backend.setsockopt(zmq.ROUTER_MANDATORY,1)
    backend.bind(outaddr)

    poller = zmq.Poller()    

    # Only poll for requests from backend until workers are available
    poller.register(backend,  zmq.POLLIN)
    poller.register(frontend, zmq.POLLIN)
   
    workers = set() # Workers available
    waiting = deque() # Client waiting

    LOGGER.info("Starting ZMQ broker loop")

    try:
        while True:
            # Poll incoming requests
            sockets = dict(poller.poll())    

            # Handle worker activity on the backends
            if backend in sockets:
                try:
                    worker_id, client_id, *rest = backend.recv_multipart()
                    if client_id == WORKER_READY:
                        # Worker is available on new connection
                        # Mark worker as available
                        if not worker_id in workers:
                            LOGGER.debug("### Worker ready: %s", worker_id)
                            workers.add(worker_id)
                    else:
                        msgid, data = rest
                        try:
                            frontend.send_multipart([client_id, msgid, data])
                            LOGGER.debug("SND %s -> %s : %s", worker_id, client_id, msgid)
                        except zmq.ZMQError as err:
                            # ZMQ Will raise error if no client_id connected
                            LOGGER.error("Failed to send message from worker '%s' to client '%s', errno %s", 
                                         worker_id, client_id, err.errno)
                except Exception as err:
                    LOGGER.error("%s", traceback.format_exc())

            # Handle incoming client requests
            if frontend in sockets:
                try:
                    client_id, msgid, data = frontend.recv_multipart()
                    LOGGER.debug("REQUEST %s %s", client_id, msgid)
                    # Push on waiting queue
                    if len(waiting) >= maxqueue:
                        LOGGER.error("Max waiting requests reached (max %d)", maxqueue)
                        try:
                            frontend.send_multipart([client_id, msgid, b"ERR", b"509"])
                        except zmq.ZMQError as err:
                            LOGGER.error("Failed to return message to client: %s, errno %s", client_id, err.errno)
                    else:
                        waiting.appendleft((client_id, msgid, data))
                except Exception as err:
                    LOGGER.error("%s", traceback.format_exc())

            # Handle waiting requests
            # Unavailable workers will be automatically removed from the list
            while workers and waiting:
                client_id, msgid, data = waiting.pop()
                while workers:
                    worker_id = workers.pop()
                    try:
                        backend.send_multipart([worker_id, client_id, msgid, data])
                        LOGGER.debug("SND %s -> %s : %s", client_id, worker_id, msgid)
                        break # Handle next request
                    except zmq.ZMQError as err:
                        LOGGER.error("Failed to send request from client '%s' to worker: '%s', errno %s", 
                                 client_id, worker_id, err.errno)
                        if not workers: 
                            # No more workers available
                            # push back the request on the queue
                            waiting.append((client_id, msgid, data))
                        
    except (KeyboardInterrupt,SystemExit):
        LOGGER.warning("Interrupted") 
    finally:
        backend.close()
        frontend.close()
        context.term()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Test worker')
    parser.add_argument('--iface', metavar="host", default="tcp://127.0.0.1", help="Interface to bind to")
    parser.add_argument('--in'   , dest='inaddr' , metavar='address', default='{iface}:8880', help="frontend address")
    parser.add_argument('--out'  , dest='outaddr', metavar='address', default='{iface}:8881', help="backend address")
    parser.add_argument('--logging', choices=['debug', 'info', 'warning', 'error'], default='info', help="set log level")
    parser.add_argument('--maxqueue', metavar='NUM', type=int, default=100, help="Max waiting queue")

    args = parser.parse_args()

    setup_log_handler(args.logging)
    print("Log level set to {}\n".format(logging.getLevelName(LOGGER.level)), file=sys.stderr)

    LOGGER.setLevel(getattr(logging, args.logging.upper()))

    run_broker(args.inaddr.format(iface=args.iface), 
               args.outaddr.format(iface=args.iface),
               maxqueue=args.maxqueue)
    print("DONE", file=sys.stderr)


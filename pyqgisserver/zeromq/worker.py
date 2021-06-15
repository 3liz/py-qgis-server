#
# Copyright 2018 3liz
# Author: David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Define Qgis Worker

    We define QGis workers as DEALER configuration: it will enables
    us to forward streamed response as chunked transfer.  

    1. Start qgis application
    2. Connect a REQ zmq socket to endpoint
    3. Return qgis server responses
"""
import os
import sys
import logging
import traceback
import zmq
import pickle
import uuid

from typing import TypeVar, Optional, Type

from ..logger import setup_log_handler
from ..utils import stats

from .messages import (WORKER_READY, ReplyMessage)
from .supervisor import Client as SupervisorClient



LOGGER=logging.getLogger('SRVLOG')

# Define an abstract type for HTTPRequest
HTTPRequest = TypeVar('HTTPRequest')


class RequestHandler:

    def __init__(self, socket: zmq.Socket, client_id: bytes, correlation_id: bytes, request: HTTPRequest) -> None:
        """ Handle requests and 
        
            Handle reply message contruction and pass message correlation_id to 
            reply.

            :param request: An HTTP request handler
            :param socket: the zmq socket
        """
        self.headers = {}
        self.status_code = 200
        self.request = request
        self.header_written = False

        self._correlation_id = correlation_id
        self._socket    = socket
        self._client_id = client_id

    def _write( self, data: bytes ) -> None:
        """ Send data back to client
        """
        self._socket.send_multipart([
            self._client_id,
            self._correlation_id,
            data])

    def send( self, data: bytes, send_more: bool=False ) -> None:
        """ Send data
        """
        if not self.header_written:
            # We let the client know that there is more 
            # data by setting the 206 code (partial response)
            if send_more and self.status_code==200:
                self.status_code = 206
            # Create a Header Message
            message = pickle.dumps(ReplyMessage(self.status_code, headers=self.headers, data=data),-1)
            self._write( message ) 
            self.header_written = True
        elif self.status_code == 206:
            self._write( data )
            if not send_more:
                self.status_code = 200

    @property
    def msgid(self):
        """ Return the message correlation id
        """
        return self._correlation_id

    @property
    def identity(self) -> bytes:
        return self._socket.identity

    def handle_message(self) -> None:
        """ Override this method to handle_messages
        """
        print("Received", self.request.data, "from", self._client_id)
        self.send(b"Hello %s" % self._client_id, True)
        self.send(b"Chunk 1", True)
        self.send(b"Chunk 2", True)
        self.send(b"", False)

    @classmethod
    def get_report(cls):
        data = stats.stats()
        data.update(pid=os.getpid())
        return data


def dealer_socket( ctx: zmq.Context, address: str, identity: Optional[bytes]=None ) -> zmq.Socket:
    """ Socket for receiving incoming messages
    """
    LOGGER.debug("Connecting to %s", address)
    sock = ctx.socket(zmq.DEALER)
    sock.setsockopt(zmq.LINGER, 500)    # Needed for socket no to wait on close
    sock.setsockopt(zmq.SNDHWM, 1)      # Max 1 item on send queue
    sock.setsockopt(zmq.IMMEDIATE, 1)   # Do not queue if no peer, will block on send
    sock.setsockopt(zmq.RCVTIMEO, 1000) # Heartbeat
    sock.identity = identity or uuid.uuid1().bytes
    LOGGER.debug("Identity set to %s", sock.identity)
    sock.connect(address)
    return sock


def broadcast_socket( ctx: zmq.Context, broadcastaddr: str ) -> zmq.Socket:
    """ Socket for receiving broadcast message notifications
    """
    LOGGER.debug("Enabling broadcast notification")
    ctx = zmq.Context.instance()
    sub = ctx.socket(zmq.SUB)
    sub.setsockopt(zmq.LINGER, 500)    # Needed for socket no to wait on close
    sub.setsockopt(zmq.SUBSCRIBE, b'RESTART')
    sub.setsockopt(zmq.SUBSCRIBE, b'REPORT')
    sub.connect(broadcastaddr)
    return sub


def run_worker(address: str, handler_factory: Type[RequestHandler], 
               identity: Optional[bytes]=None, broadcastaddr: Optional[str]=None,
               maxcycles: Optional[int]=None) -> None:
    """ Enter the message loop
    """
    ctx = zmq.Context.instance()

    sock = dealer_socket( ctx, address, identity )
    if broadcastaddr:
        sub = broadcast_socket( ctx, broadcastaddr )

    # Initialize supervisor client
    supervisor = SupervisorClient()

    def get():
        client_id, corr_id, request = sock.recv_multipart()
        LOGGER.debug("RCV %s: %s", client_id, corr_id)
        return client_id, corr_id, pickle.loads(request)

    try:
        LOGGER.info("Starting ZMQ worker loop")
        completed = 0
        while maxcycles is None or (maxcycles and completed < maxcycles):
            sock.send(WORKER_READY)
            try:
                client_id, corr_id, request = get()
                supervisor.notify_busy()
                handler = handler_factory(sock, client_id, corr_id, request)
                handler.handle_message()
                completed += 1
            except zmq.error.Again:
                pass
            except zmq.ZMQError as err:
                LOGGER.error("Worker Error %d: %s", err.errno, zmq.strerror(err.errno))
            except Exception as exc:
                LOGGER.error("Worker Error %s\n%s", exc, traceback.format_exc())
                if not handler.header_written:
                    handler.status_code = 500
                    handler.send(bytes("Worker internal error".encode('ascii')))
                    # Got error 500, do not presume worker state
                    break
            finally:
                supervisor.notify_done()

            # Handle broadcast notifications
            try:
                if broadcastaddr:
                    msg = sub.recv(flags=zmq.NOBLOCK)
                    if msg==b'RESTART':
                        # There is no really way to restart
                        # so exit and let the framework restart a new worker
                        LOGGER.info("Exiting on RESTART notification")
                        break
                    elif msg==b'REPORT':
                        # Reporting asked
                        supervisor.send_report(handler_factory.get_report())
            except zmq.error.Again:
                pass
    except (KeyboardInterrupt, SystemExit):
        pass

    if broadcastaddr:
        sub.close()
    sock.close()
    LOGGER.info("Terminating Worker")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Test worker')
    parser.add_argument('--host'    , metavar="host"   , default='tcp://localhost', help="router host")   
    parser.add_argument('--router'  , metavar='address', default='{host}:8881', help="router address")
    parser.add_argument('--logging' , choices=['debug', 'info', 'warning', 'error'], default='info', help="set log level")
    parser.add_argument('--identity', default="", help="Set worker identity")

    args = parser.parse_args()

    setup_log_handler(args.logging)
    print("Log level set to {}\n".format(logging.getLevelName(LOGGER.level)), file=sys.stderr)

    LOGGER.setLevel(getattr(logging, args.logging.upper()))

    run_worker(args.router.format(host=args.host), RequestHandler, 
               identity=bytes(args.identity.encode('ascii')))
    print("DONE", file=sys.stderr)


""" Define Qgis Worker

    We define QGis workers as REQ since we want to do load-balancing with an 
    intermediate ROUTER-ROUTER broker.

    Our workers are totally synchronous, so a REQ is appropriate here

    1. Start qgis application
    2. Connect a REQ zmq socket to endpoint
    3. Return qgis server responses
"""
import sys
import os
import logging
import traceback
import zmq
import pickle
import signal
import uuid

from ..version import __description__, __version__
from ..logger import setup_log_handler

LOGGER=logging.getLogger('QGSRV')

from .messages import (WORKER_READY, ReplyMessage)


class RequestHandler:

    def __init__(self, socket, client_id, correlation_id, request):
        """ Handle requests and 
        
            Handle reply message contruction and pass message correlation_id to 
            reply.

            :param request: the input message
            :param socket: the zmq socket
        """
        self.headers = {}
        self.status_code = 200
        self.request = request
        self.header_written = False

        self._correlation_id = correlation_id
        self._socket  = socket
        self._client_id = client_id

    def _write( self, data ):
        """ Send data back to client
        """
        self._socket.send_multipart([
            self._client_id,
            self._correlation_id,
            data])

    def send( self, data, send_more=False ):
        """ Send data
        """
        if not self.header_written:
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
    def identity(self):
        return self._socket.identity

    def handle_message(self):
        """ Override this method to handle_messages
        """
        print("Received", self.request.data, "from", self._client_id)
        self.send(b"Hello %s" % self._client_id, True)
        self.send(b"Chunk 1", True)
        self.send(b"Chunk 2", True)
        self.send(b"", False)


def run_worker(address, handler_factory, identity=None, timeout=1000):
    """ Enter the message loop
    """
    ctx = zmq.Context.instance()

    # Send our "ready" message
    LOGGER.info("Connecting to %s", address)
    sock = ctx.socket(zmq.DEALER)
    sock.setsockopt(zmq.LINGER, 500)    # Needed for socket no to wait on close
    sock.setsockopt(zmq.SNDHWM, 1)      # Max 1 item on send queue
    sock.setsockopt(zmq.IMMEDIATE, 1)   # Do not queue if no peer
    sock.identity = identity or uuid.uuid1().bytes
    LOGGER.info("Identity set to %s", sock.identity)
    sock.connect(address)

    try:
        LOGGER.info("Starting ZMQ worker loop")
        while True:
            try:
                sock.send(WORKER_READY)
                client_id, corr_id, request = sock.recv_multipart()
                LOGGER.debug("RCV %s: %s", client_id, corr_id)
                request = pickle.loads(request)
                handler = handler_factory(sock, client_id, corr_id, request)
                handler.handle_message()
            except Exception as exc:
                LOGGER.error("Worker Error %s\n%s", exc, traceback.format_exc())
    except (KeyboardInterrupt, SystemExit):
            print("Interrupted", file=sys.stderr)
   # Terminate context
    print("Terminating context", file=sys.stderr)
    sock.close()
    ctx.term()
    

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


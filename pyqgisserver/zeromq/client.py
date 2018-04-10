""" Zmq asynchrone client

    Require python 3.6
"""

import sys
import asyncio
import zmq
import zmq.asyncio
import weakref
import time
import pickle
import logging
import uuid
import traceback

from collections import namedtuple

from .messages import RequestMessage

from ..version import __description__, __version__
from ..logger import setup_log_handler

LOGGER=logging.getLogger('QGSRV')


class RequestTimeoutError(Exception):
    pass

class RequestGatewayError(Exception):
    pass

class RequestProxyError(Exception):
    pass


class AsyncResponseHandler:
    def __init__(self, correlation_id, loop):
        self.correlation_id = correlation_id
        self.headers = None
        # Create a future for sending the result
        self._future = loop.create_future()
        self._loop   = loop
        self._chunks = None
        self._has_more = False
        self.data = None
    
    def _set_exception(self, exc):
        self._has_more = False
        self._future.set_exception(exc)

    def _set_result(self, data):
        if self.headers is None:
            status, hdrs, body = pickle.loads(data)
            self.headers = hdrs
            self.data    = body
            self.status  = status
            # We are waiting for more data
            # Create a queue to collect the remaining chunks
            if self.status == 206:
                self._has_more = True
                self.status = 200
                self._chunks = asyncio.Queue(loop=self._loop)
            # Send the result
            self._future.set_result(self)
        elif self._has_more:
            self._chunks.put_nowait(data)
            self._has_more = (data != b"")

    def _done(self):
        """ Check if there is more data to come
        """
        return not self._has_more and self._future.done()

    async def _get(self, timeout):
        """ wait for result
        """
        try:
            return await asyncio.wait_for(self._future, timeout)
        except asyncio.TimeoutError:
            self._has_more = False
            raise RequestTimeoutError()

    async def _next_chunk(self, timeout):
        """ Get next chunk
        """
        try:
            if self._chunks:
                return await asyncio.wait_for(self._chunks.get(), timeout)
        except asyncio.TimeoutError:
            self._has_more = False
            raise RequestTimeoutError()
        return b""


class AsyncClient:
    """ Async DEALER ZMQ client
    """
    def __init__(self, address, identity=None, context=None, loop=None):
        self._context = context or zmq.asyncio.Context.instance()
        if not context:
            self._own_context = True

        self.identity = identity or uuid.uuid1().bytes

        sock = self._context.socket(zmq.DEALER)
        sock.setsockopt(zmq.LINGER, 500)    # Needed for socket no to wait on close
        sock.setsockopt(zmq.IMMEDIATE, 1)   # Do not queue if there is no connection
        sock.identity = self.identity
        sock.connect(address)

        self._loop = loop or asyncio.get_event_loop() 

        self._running = False
        self._handlers = {}
        self._socket   = sock
        self._polling  = False
        LOGGER.info("Starting client %s", self.identity)

    async def _poll(self):
        """ Handle incoming messages
        """
        self._polling = True
        while self._handlers:
            try:
                correlation_id, data, *rest = await self._socket.recv_multipart()
                # Get if there is a future pending for that message
                try:
                    handler = self._handlers[correlation_id]
                    if rest and data == b'ERR':
                        handler._set_exception(RequestProxyError(rest[0]))
                    else:
                        handler._set_result(data)
                    # Remove handlers from the heap if we are done
                    if handler._done():
                        self._handlers.pop(correlation_id,None)
                except KeyError:
                    LOGGER.warning("%s: No pending future found for message %s",self.identity, correlation_id)
            except zmq.ZMQError as err:
                LOGGER.error("%s error:  zmq error: %s (%s)", self.identity, zmq.strerror(err.errno),err.errno)
            except Exception as err:
                LOGGER.error("%s exception %s\n%s", self.identity, err, traceback.format_exc())
        self._polling = False

    async def fetch( self, query, method='GET', headers={}, data=None, timeout=5):
        """ Send a request message to the worker
        """
        # Send request
        request = pickle.dumps(RequestMessage(query,headers=headers,method=method,data=data),-1)
        correlation_id = id(request).to_bytes(8,byteorder='big')
        try:
            await self._socket.send_multipart([correlation_id, request], flags=zmq.DONTWAIT)
        except zmq.ZMQError as err:
            LOGGER.error("%s (%s)", zmq.strerror(err.errno), err.errno)
            raise RequestGatewayError()
        
        # Create response handler and register it
        handler = AsyncResponseHandler(correlation_id, self._loop)
        self._handlers[correlation_id] = handler
        # Run poller if needed
        if not self._polling:
            asyncio.ensure_future(self._poll())

        # Wait for response
        try:
            return await handler._get(timeout)
        except:
            self._handlers.pop(correlation_id,None)
            raise

    async def fetch_more( self, response, timeout=5 ):
        try:
            data = await response._next_chunk(timeout)
            if data == b"": 
                return None
            else:
                return data
        except:
            self._handlers.pop(response.correlation_id,None)
            raise

    ## Cannot use generator with python 3.5
    #async def fetch_more( self, response, timeout=5 ):
    #    """ Request next chunk
    #    """
    #    try:
    #        while True:
    #            data = await response._next_chunk(timeout) 
    #            if data == b"": break
    #            yield  data
    #    except:
    #        self._handlers.pop(response.correlation_id,None)
    #        raise

    def terminate(self):
        LOGGER.info("Terminating client %s", self.identity)
        self._running = False
        self._futures = {}
        self._socket.close()
        if self._own_context:
            self._context.term()
    

if __name__ == '__main__':
    import signal
    import argparse
    from time import sleep

    parser = argparse.ArgumentParser(description='Test Client')
    parser.add_argument('--host'      , metavar="host"   , default='tcp://localhost', help="router host")
    parser.add_argument('--router'    , metavar='address', default='{host}:8880', help="router address")
    parser.add_argument('--logging'   , choices=['debug', 'info', 'warning', 'error'], default='info', help="set log level")
    parser.add_argument('--identity'  , default='', help="Set worker identity")
    parser.add_argument('--count'     , default=1, type=int, help="Number of requests")

    args = parser.parse_args()

    setup_log_handler(args.logging)
    print("Log level set to {}\n".format(logging.getLevelName(LOGGER.level)), file=sys.stderr)

    LOGGER.setLevel(getattr(logging, args.logging.upper()))

    client = AsyncClient(args.router.format(host=args.host),bytes(args.identity.encode('ascii')))
    sleep(1) # Give some time to connection to establish
    async def fetch(index):
        try:
            response = await client.fetch(query="?service=WMS", data=b"Hello world from %d" % index)
            print("%d -> response = %s" % (index,response.data))
            chunk = await client.fetch_more(response)
            while chunk:
                print("%d -> chunk = %s" % (index,chunk))
                chunk = await client.fetch_more(response)
        except RequestTimeoutError:
            LOGGER.error("%d -> TIMEOUT", index)
        except RequestGatewayError:
            LOGGER.error("%d -> GATEWAY ERROR", index)

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, loop.stop)
    loop.run_until_complete(asyncio.wait([fetch(i+1) for i in range(args.count)]))
    
    client.terminate()

    print("DONE", file=sys.stderr)


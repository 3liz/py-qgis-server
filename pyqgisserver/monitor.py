""" AMQP monitor for qgis requests
"""
import asyncio
import logging
import traceback
import json
import os

from typing import Union, Mapping

LOGGER = logging.getLogger('QGSRV')

def _decode( b: Union[str,bytes] ) -> str:
    if not isinstance(b,str):
        return b.decode('utf-8')
    return b


class Monitor:

    def __init__(self, amqp_client ) -> None:
        """ Init AMQP monitor
        """
        self._client = amqp_client
        self._routing_key = os.environ['AMQP_ROUTING']

    def emit( self, status:int, arguments: Mapping[str,str], delta: float ) -> None:
        """ Publish monitor data
        """
        params = { k:_decode(v[0]) for k,v in arguments.items() }
        # Send all params to our logger
        ms = int(delta * 1000.0)
        params.update(RESPONSE_TIME=ms,
                      RESPONSE_STATUS=status,
                      ROUTING_KEY=self._routing_key)
        log_msg = json.dumps(params)
        self._client.publish( log_msg ,
                routing_key  = self._routing_key,
                expiration   = 3000,
                content_type = 'application/json',
                content_encoding ='utf-8')

    @classmethod
    def initialize(cls) -> 'Monitor':
        """ Register an instance of Monitor client
        """
        if os.environ.get('AMQP_ROUTING') is None:
            return

        try:
            from amqpclient.concurrent import AsyncPublisher
        except ImportError:
            LOGGER.warning("Cannot import 'amqpclient', AMQP logging will not be available")
            return None

        vhost = os.environ.get('AMQP_VHOST','/')
        port  = os.environ.get('AMQP_PORT','5672')
        hosts = os.environ['AMQP_HOST']

        exchange = os.environ.get('AMQP_EXCHANGE','qgis_log')

        client = AsyncPublisher(host=hosts,port=int(port),virtual_host=vhost,
                                reconnect_delay=0.001,
                                logger=LOGGER)

        # Catch exception in connection
        async def connect():
            try:
                await client.connect(exchange=exchange,exchange_type='topic')
                LOGGER.info("AMQP logger initialized.")
            except Exception as e:
                traceback.print_exception(*exc_info)
                LOGGER.error("Failed to initialize AMQP logger")

        asyncio.ensure_future( connect() )

        inst = cls(client)
        setattr(cls,'_instance', inst)
        return inst


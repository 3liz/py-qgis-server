""" AMQP monitor for qgis requests
"""
import asyncio
import logging
import traceback
import json
import os

from typing import Union, Mapping

LOGGER = logging.getLogger('SRVLOG')

def _decode( b: Union[str,bytes] ) -> str:
    if not isinstance(b,str):
        return b.decode('utf-8')
    return b

TAG_PREFIX = 'AMQP_GLOBAL_TAG_' 


def _read_credentials( vhost: str, kwargs: Mapping[str,str] ) -> None:
    """ Read credentials from passfile
    """
    credential_file = os.getenv("AMQPPASSFILE")
    if not (credential_file and os.path.exists(credential_file)):
        return

    from pika import PlainCredentials

    LOGGER.debug("Using passfile %s", credential_file)
    with open(credential_file) as fp:
        for line in fp.readlines():
            credentials = line.strip()
            if credentials and not credentials.startswith('#'):
                vhost, user, passwd = credentials.split(':')
                if vhost in ('*',vhost):
                    LOGGER.info("Using credentials for user '%s' on vhost '%s'", user, vhost)
                    kwargs['credentials'] = PlainCredentials(user,passwd)
                    break

class Monitor:

    def __init__(self, amqp_client ) -> None:
        """ Init AMQP monitor
        """
        self._client = amqp_client
        self._routing_key = os.environ['AMQP_ROUTING']
      
        # Get global tags
        tags = ((e.partition(TAG_PREFIX)[2],os.environ[e]) for e in os.environ if e.startswith(TAG_PREFIX))
        self._global_tags = { t:v for (t,v) in tags if t }
    

    def emit( self, status:int, arguments: Mapping[str,str], delta: float ) -> None:
        """ Publish monitor data
        """
        params = { k:_decode(v[0]) for k,v in arguments.items() }
        # Send all params to our logger
        ms = int(delta * 1000.0)
        params.update(self._global_tags,
                      RESPONSE_TIME=ms,
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

        hosts = os.environ['AMQP_HOST']
        vhost = os.environ.get('AMQP_VHOST','/')
        port  = os.environ.get('AMQP_PORT','5672')

        kwargs = {}

        _read_credentials( vhost, kwargs )

        exchange = os.environ.get('AMQP_EXCHANGE','qgis_log')

        client = AsyncPublisher(host=hosts,port=int(port),virtual_host=vhost,
                                reconnect_delay=0.001,
                                logger=LOGGER, **kwargs)

        # Catch exception in connection
        async def connect():
            try:
                await client.connect(exchange=exchange,exchange_type='topic')
                LOGGER.info("AMQP logger initialized.")
            except Exception:
                LOGGER.error("Failed to initialize AMQP logger: %s",traceback.format_exc())

        asyncio.ensure_future( connect() )

        inst = cls(client)
        setattr(cls,'_instance', inst)
        return inst


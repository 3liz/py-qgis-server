""" AMQP monitor for qgis requests
"""
import asyncio
import logging
import traceback
import json
import os

from typing import Union, Dict, Optional

from .config  import confservice

LOGGER = logging.getLogger('SRVLOG')

def _decode( b: Union[str,bytes] ) -> str:
    if not isinstance(b,str):
        return b.decode('utf-8')
    return b

TAG_PREFIX = 'AMQP_GLOBAL_TAG_' 


def _read_credentials( vhost: str, user: str ) -> Optional:  # ['PlainCredentials']
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
                cr_vhost, cr_user, passwd = credentials.split(':')
                if cr_vhost in ('*',vhost) and  cr_user in ('*',user):
                    LOGGER.info("Using credentials for user '%s' on vhost '%s'", user, vhost)
                    return PlainCredentials(user,passwd)


class Monitor:

    def __init__(self, amqp_client: 'AsyncPublisher', routing_key: str ) -> None: # noqa: F821
        """ Init AMQP monitor
        """
        self._client = amqp_client

        self._dynamic_routing = routing_key.startswith('@')
        if self._dynamic_routing:
            self._routing_key = routing_key[1:]
        else:
            self._routing_key = routing_key

        # Get global tags
        tags = ((e.partition(TAG_PREFIX)[2],os.environ[e]) for e in os.environ if e.startswith(TAG_PREFIX))
        self._global_tags = { t:v for (t,v) in tags if t }
    

    def emit( self, status:int, arguments: Dict, delta: float, meta: Dict ) -> None:
        """ Publish monitor data
        """
        if self._dynamic_routing:
            routing_key = self._routing_key.format(META=meta)
        else:
            routing_key = self._routing_key

        params = { k:_decode(v[0]) for k,v in arguments.items() }
        # Send all params to our logger
        ms = int(delta * 1000.0)
        params.update(self._global_tags,
                      RESPONSE_TIME=ms,
                      RESPONSE_STATUS=status,
                      ROUTING_KEY=routing_key)
        log_msg = json.dumps(params)
        self._client.publish( log_msg ,
                              routing_key  = routing_key,
                              expiration   = 3000,
                              content_type = 'application/json',
                              content_encoding ='utf-8')

    @classmethod
    def initialize(cls) -> 'Monitor':
        """ Register an instance of Monitor client
        """
        conf = confservice['monitor:amqp']
        routing_key = conf.get('routing_key')
        if not routing_key:
            return 

        try:
            from amqpclient.concurrent import AsyncPublisher
        except ImportError:
            LOGGER.warning("Cannot import 'amqpclient', AMQP logging will not be available")
            return None

        hosts = conf['host']
        user  = conf['user']
        vhost = conf['vhost']
        port  = conf['port']

        reconnect_delay = conf['reconnect_delay']

        kwargs = {}

        if user:
            credentials = _read_credentials( vhost, user )
            if credentials:
                kwargs['credentials'] = credentials

        exchange = conf['exchange']

        client = AsyncPublisher(host=hosts,port=int(port),virtual_host=vhost,
                                reconnect_delay=reconnect_delay,
                                logger=LOGGER, **kwargs)

        # Catch exception in connection
        async def connect():
            try:
                await client.connect(exchange=exchange,exchange_type='topic')
                LOGGER.info("AMQP logger initialized.")
            except Exception:
                LOGGER.error("Failed to initialize AMQP logger: %s",traceback.format_exc())

        asyncio.ensure_future( connect() )

        inst = cls(client, routing_key)
        setattr(cls,'_instance', inst)
        return inst


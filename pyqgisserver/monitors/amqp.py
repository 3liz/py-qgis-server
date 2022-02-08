""" AMQP monitor for qgis requests
"""
import asyncio
import logging
import traceback
import json
import os

from typing import Dict, Optional, Any

from amqpclient.concurrent import AsyncPublisher

from ..config  import confservice
from .base  import MonitorBase

LOGGER = logging.getLogger('SRVLOG')

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


class Monitor(MonitorBase):

    def __init__(self, amqp_client: 'AsyncPublisher', routing_key: str, default_routing: Optional[str]=None ) -> None: # noqa: F821
        """ Init AMQP monitor
        """
        super().__init__()

        self._client = amqp_client

        self._dynamic_routing = routing_key.startswith('@')
        if self._dynamic_routing:
            self._routing_key = routing_key[1:]
            self._default_routing = default_routing
            if not self._default_routing:
                LOGGER.warning("No default routing defined as fallback for dynamic routing")
        else:
            self._routing_key = routing_key

    def emit( self, params: Dict[str,Any], meta: Dict ) -> None:
        """ Publish monitor data
        """
        if self._dynamic_routing:
            try:
                routing_key = self._routing_key.format(META=meta)
            except KeyError: 
                # FALLBACK to default routing key
                if self._default_routing:
                    routing_key = self._default_routing
        else:
            routing_key = self._routing_key

        # Send all params to our logger
        data = dict(self.global_tags, ROUTING_KEY=routing_key)
        data.update(params)
        log_msg = json.dumps(data)
        self._client.publish( log_msg ,
                              routing_key  = routing_key,
                              expiration   = 3000,
                              content_type = 'application/json',
                              content_encoding ='utf-8')

    @classmethod
    def initialize(cls) -> 'Monitor':
        """ Register an instance of Monitor client
        """
        if hasattr(cls,'_instance'):
            return cls._instance

        conf = confservice['monitor:amqp']
        routing_key = conf.get('routing_key')
        if not routing_key:
            return 

        hosts = conf['host']
        user  = conf['user']
        vhost = conf['vhost']
        port  = conf['port']

        reconnect_delay = conf.getint('reconnect_delay')

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

        # Get default routing key in case as fallback in case
        # We fail to get dynamic key
        default_routing_key = conf.get('default_routing_key', fallback=None)

        inst = cls(client, routing_key, default_routing=default_routing_key)
        setattr(cls,'_instance', inst)
        return inst


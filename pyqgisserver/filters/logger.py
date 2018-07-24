""" AMQP logger filter
"""
import os
import logging
import json

from time import time
from qgis.server import QgsServerFilter

LOGGER = logging.getLogger('QGSRV')


def init_logger():
    """ Init the amqp logger
    """
    try:
        from amqpclient.basic import BasicPublisher
    except ImportError:
        LOGGER.warning("Cannot import 'amqpclient', AMQP logging will not be available")
        return None

    vhost = os.environ.get('AMQP_VHOST','/')
    port  = os.environ.get('AMQP_PORT','5672')
    hosts = os.environ['AMQP_HOST']

    exchange = os.environ.get('AMQP_EXCHANGE','qgis_log')

    client = BasicPublisher(host=hosts,port=int(port),virtual_host=vhost,
                            reconnect_delay=0.001,
                            logger=LOGGER)

    client.initialize(exchange, exchange_type='topic')
    return client


class LogFilter(QgsServerFilter):
    """ Qgis syslog filter implementation
    """
    def __init__(self, iface):
        
        self._client      = init_logger()
        self._routing_key = os.environ['AMQP_ROUTING']

        super().__init__(iface)

    def requestReady(self):
        """ Called when request is ready
        """
        self.t_start = time()

    def responseComplete(self):
        """ Called when response is ready
        """
        if not self._client:
            return

        req = self.serverInterface().requestHandler()
        params = req.parameterMap()
        # If we are called with no params
        # There is nothing to log so just return
        if len(params)==0:
            return
        # Send all params to our logger
        ms = int((time() - self.t_start) * 1000.0)
        status = "error" if req.exceptionRaised() else 'ok'
        code = req.statusCode() 
        params.update(RESPONSE_TIME=ms, 
                      RESPONSE_CODE=code, 
                      RESPONSE_STATUS=status, 
                      ROUTING_KEY=self._routing_key)
        log_msg = json.dumps(params)
        self._client.publish( log_msg , 
                routing_key  = self._routing_key,
                expiration   = 3000,
                content_type = 'application/json',
                content_encoding ='utf-8')

    @classmethod
    def register_self( cls, iface, pri=0 ):
         """ Register an instance of LogFilter

            Note that we seed to keep an instance to the filter
            to prevent python gc.
         """
         if os.environ.get('AMQP_ROUTING') is None:
             return

         inst = cls(iface)
         iface.registerFilter( inst, pri)
         setattr(cls,'_instance', inst)
         return inst


""" Qgis server handler
"""
import os
import logging

from ...config import get_config
from ...cache import cache_lookup
from ...utils.decorators import singleton
from ...exceptions import HTTPError2
from ...handlers.basehandler import BaseHandler

LOGGER = logging.getLogger('QGSRV')

@singleton 
class Adapters:
    def __init__(self):
        from ..adapters import Request, Response
        def _make_adapters(handler, method):
            return Request(handler, method=method), Response(handler)
        self._make_adapters = _make_adapters

    def __call__(self, handler, method, project=None):
        server = handler.application.settings['qgsserver']
        server.handleRequest(*self._make_adapters(handler, method), project=project)


class QgsServerHandler(BaseHandler):

    """ Proxy to Qgis server handler
    """

    def initialize(self):
        super().initialize()
        self.conf = get_config('server')
        
    def prepare(self):
        adapters = Adapters()
        path     = self.get_query_argument('MAP')

        try:
            project  = cache_lookup( path )
        except FileNotFoundError:
            raise HTTPError2(404, "map '%s' no found" % path) 

        self.handleRequest = lambda m: adapters(self,m,project)

    def get(self):
        """ Handle Get method
        """
        self.handleRequest('GET')
          
    def post(self):
        """ Handle Post method
        """
        self.handleRequest('POST')
        




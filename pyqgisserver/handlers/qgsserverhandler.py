""" Qgis server handler
"""
import os

from ..config import get_config
from ..cache import cache_lookup

from .basehandler import BaseHandler

from qgistools.utils import singleton

# Define lazy constructor to our QgsServer
#@singleton
#class Server:
#    def __new__(cls):
#        from qgis.server import QgsServer
#        return QgsServer()

#
# XXX We need to lazy load qgis modules because 
# the application crash  when we fork with globally
# imported modules
#

@singleton 
class Adaptors:
    def __init__(self):
        from pyqgisserver.http import adaptors
        from qgis.server import QgsServer
        
        self.server = QgsServer()
        
        def _make_adaptors(handler, method):
            return adaptors.Request(handler, method=method), adaptors.Response(handler)
        self._make_adaptors = _make_adaptors

    def __call__(self, handler, method, project=None):
        self.server.handleRequest(*self._make_adaptors(handler, method), project=project)


class QgsServerHandler(BaseHandler):

    """ Proxy to Qgis server handler
    """
    def initialize(self):
        super().initialize()

        self.conf = get_config('server')
        
        project = cache_lookup( self.get_query_argument('MAP'))

        adaptors = Adaptors()
        self.handleRequest = lambda m: adaptors(self,m,project)
       
    def get(self):
        """ Handle Get method
        """
        self.handleRequest('GET')
          
    def post(self):
        """ Handle Post method
        """
        self.handleRequest('POST')
        




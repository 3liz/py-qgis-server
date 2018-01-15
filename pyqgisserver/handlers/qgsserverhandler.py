""" Qgis server handler
"""
import os
import logging

from ..config import get_config
from ..cache import cache_lookup

from .basehandler import BaseHandler

from qgistools.utils import singleton

LOGGER = logging.getLogger('QGSRV')

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
class Adapters:
    def __init__(self):
        from pyqgisserver.http import adapters
        from qgis.server import QgsServer
        
        self.server = QgsServer()
        
        def _make_adapters(handler, method):
            return adapters.Request(handler, method=method), adapters.Response(handler)
        self._make_adapters = _make_adapters

    def __call__(self, handler, method, project=None):
        self.server.handleRequest(*self._make_adapters(handler, method), project=project)


class QgsServerHandler(BaseHandler):

    """ Proxy to Qgis server handler
    """

    @staticmethod
    def init_server():
        LOGGER.debug("Initializing server")

        # XXX HACK issue a dummy request for initializing 
        # network stuff
        from qgis.core import QgsProviderRegistry
        wmsuri = ("contextualWMSLegend=0&crs=EPSG:4326&dpiMode=7&featureCount=10&format=image/jpeg"
          "&layers=s2cloudless&styles&amp;tileMatrixSet=s2cloudless-wmsc-14"
          "&url=http://localhost:8080/?" )
       
        # XXX This will fail with a timeout, subesquent requests should
        # be ok then.
        provider = QgsProviderRegistry.instance().createProvider( "wms", wmsuri )

        adapters = Adapters()
        return adapters.server

    def initialize(self):
        super().initialize()
        self.conf = get_config('server')
        
    def prepare(self):
        adapters = Adapters()
        project  = cache_lookup( self.get_query_argument('MAP'))

        self.handleRequest = lambda m: adapters(self,m,project)

    def get(self):
        """ Handle Get method
        """
        self.handleRequest('GET')
          
    def post(self):
        """ Handle Post method
        """
        self.handleRequest('POST')
        




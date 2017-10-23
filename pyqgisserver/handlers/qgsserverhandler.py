""" Qgis server handler
"""

from ..config import get_config
from .basehandler import BaseHandler

from qgistools.utils import singleton

# Define lazy constructor to our QgsServer
@singleton
class Server:
    def __new__(cls):
        from qgis.server import QgsServer
        return QgsServer()


class QgsServerHandler(BaseHandler):

    """ Proxy to Qgis server handler
    """
    def initialize(self):
        super().initialize()
        self.conf   = get_config('server')
        self.server = Server()

    def adaptors(self, method):
        """ Return request/response adaptors
        """
        from pyqgisserver.http import adaptors
        return adaptors.Request(self, method=method), adaptors.Response(self)
         
    def get(self):
        """ Handle Get method
        """
        args = self.adaptors('GET')
        self.server.handleRequest(*args)
          
    def post(self):
        """ Handle Post method
        """
        args = self.adaptors('POST')
        self.server.handleRequest(*args)
        




""" Http qgis requests/response adapters to tornado http requests handlers
"""
import logging
import traceback

from urllib.parse import urlparse

from qgis.PyQt.QtCore import QBuffer, QIODevice
from qgis.server import (QgsServerRequest,
                         QgsServerResponse)

from contextlib import contextmanager

LOGGER = logging.getLogger('QGSRV')

class Request(QgsServerRequest):

    def __init__(self, handler, headers=None, method='GET' ):
        """ Create a new QgsServerRequest from tornado handler request
        """
        self._request = handler.request
        location = self._request.headers.get('X-Proxy-Location')
        if location:
            location += '?'+self._request.query
        else:
            location = self._request.full_url()

        if headers is None:
            # Transform request headers in single valued dict
            hdrs = self._request.headers
            headers = { k:hdrs[k].upper() for k in hdrs.keys() }

        LOGGER.debug("Using url location %s", location)

        super().__init__(location, method={
            'GET' : QgsServerRequest.GetMethod,
            'PUT' : QgsServerRequest.PutMethod,
            'POST': QgsServerRequest.PostMethod,
            }[method], headers=headers)
       
    def data(self): 
        """ Return post/put data a QByteArray
        """
        return QByteArray(self._request.body)


class Response(QgsServerResponse):
    """ Adaptor to Tornado handler response

        We keep our own buffer because we do not have
        acces to the handler internal buffer.

        The date is written at 'flush()' call.

        The adaptor keep track of headers set
        from the qgis server: only those headers 
        can be set/unset by the caller. 
        That way we do not stomp on specific  headers
        sets by the framework
    """

    def __init__(self, handler, on_finish=None):
        super().__init__()
        self._handler = handler
        self._buffer = QBuffer()
        self._buffer.open(QIODevice.ReadWrite)
        self._on_finish = on_finish

        # keep track of header sets
        self._headers = {}
        self._header_written = False

    def setStatusCode(self, code):
        self._handler.set_status(code)

    def statusCode(self):
        return self._handler.get_status()

    @contextmanager
    def _catch(self):
        # XXX Take care not to raise python
        # exception inside Qgis code
        try:
            yield
        except Exception as e:
            LOGGER.error("Caught Exception: %s" % e)
            traceback.print_exc()
            self._handler.send_error()

    def finish(self):
        # Do not call handler.finish() because
        # it will automatically called at the end of the request
        # process
        self.flush()
        if self._on_finish is not None:
            with self._catch():
               self._on_finish(self)

    def flush(self):
        """ Write the data to the handler buffer 
            and flush the socket
        """
        self._buffer.seek(0)
        bytesAvail = self._buffer.bytesAvailable()
        if bytesAvail:
            with self._catch():
                self._handler.write( bytes(self._buffer.data()) )
                self._buffer.buffer().clear()
                self._handler.flush()
                self._header_written = True


    def header(self, key):
        return self._headers.get(key)

    def headers(self):
        """ Return headers as dict
        """
        return self._headers
        
    def io(self):
        return self._buffer

    def setHeader(self, key, value):
        self._headers[key] = value
        self._handler.set_header(key,value)

    def removeHeader(self, key):
        """ Remove header

            Remove only header which has been set
            by setHeader, do not touch defaults headers
        """
        if key in self._headers:
            del self._headers[key]
            self._handler.clear_header(key)
   
    def sendError(self, code, message=None):
        """
        """
        self._handler.send_error(status_code=code, reason=message)

    def setHeader( self, key, value):
        self._handler.set_header(key, value)

    def data(self):
        """ Return buffer data
        """
        return self._buffer.data()

    def _clearHeaders(self):
        """ Clear headers set so far
        """
        for k in self._headers:
            self._handler.clear_header(key)
        # Reset headers
        self._headers = {}
 
    def clear(self):
        self._clearHeaders()
        self.truncate()

    def headersSent(self):
        return self._header_written

    def truncate(self):
        """ Truncate buffer
        """
        self._buffer.seek(0)
        self._buffer.buffer().clear()




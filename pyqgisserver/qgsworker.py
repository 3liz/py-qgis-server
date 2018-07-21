#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Qgis server request adapters

    Embedded qgis server in a 0MQ worker 
"""
import os
import sys
import logging
import traceback

from qgis.PyQt.QtCore import QBuffer, QIODevice, QByteArray
from qgis.server import (QgsServerRequest,
                         QgsServerResponse)

from .zeromq.worker import RequestHandler, run_worker
from .cache import cache_lookup

from .filters.logger import LogFilter

LOGGER = logging.getLogger('QGSRV')


class Request(QgsServerRequest):

    def __init__(self, handler ):
        """ Create a new QgsServerRequest from tornado handler request
        """
        req = handler.request
        
        # Recreate URL
        location = req.headers.get('X-Proxy-Location',"")
        location += '?'+req.query.lstrip('?')

        self._data = req.data

        super().__init__(location, method={
            'GET' : QgsServerRequest.GetMethod,
            'PUT' : QgsServerRequest.PutMethod,
            'POST': QgsServerRequest.PostMethod,
            }[req.method], headers=req.headers)
       
    def data(self): 
        """ Return post/put data a QByteArray
        """
        return QByteArray(self._data)


class Response(QgsServerResponse):
    """ Adaptor to handler response

        The data is written at 'flush()' call.
    """

    def __init__(self, handler):
        super().__init__()
        self._handler = handler
        self._buffer = QBuffer()
        self._buffer.open(QIODevice.ReadWrite)
        self._numbytes = 0
        self._finish   = False

    def setStatusCode(self, code):
        if not self._handler.header_written:
            self._handler.status_code = code
        else:
            LOGGER.error("Cannot set status code after header written")

    def statusCode(self):
        return self._handler.status_code

    def finish(self):
        """ Terminate the request
        """
        self._finish = True
        self.flush()

    def flush(self):
        """ Write the data to the handler buffer 
            and flush the socket

            Headers will be written at the first call to flush()
        """
        self._buffer.seek(0)
        bytesAvail = self._buffer.bytesAvailable()
        if self._finish:
            self._handler.headers['Content-Length']=bytesAvail
        # Take care of the logic: if finish and not handler.header_written then there is no
        # chunk following
        send_more = not self._finish or self._handler.header_written
        try:
            if bytesAvail:
                self._handler.send( bytes(self._buffer.data()), send_more )
                self._buffer.buffer().clear()
            # push the sentinel
            if send_more and self._finish:
                self._handler.send( b'', False )
        except Exception:
            LOGGER.error("Caught Exception:\n%s", traceback.format_exc())
            self._handler.status_code = 500

    def header(self, key):
        return self._handler.headers.get(key)

    def headers(self):
        """ Return headers as dict
        """
        return self._handler.headers
        
    def io(self):
        return self._buffer

    def data(self):
        """ Return buffer data
        """
        return self._buffer.data()

    def setHeader(self, key, value):
        if not self._handler.header_written:
            self._handler.headers[key] = value
        else:
            LOGGER.error("Cannot set header after header written")

    def removeHeader(self, key):
        self._handler.headers.pop(key,None)
   
    def sendError(self, code, message=None):
        if not self._handler.header_written:
            LOGGER.error("%s (%s)", message, code)
            self._handler.status_code = code
            self._handler.send(bytes(str(message).encode('ascii')))
            self._finish = True
        else:
            LOGGER.error("Cannot set error after header written")

    def _clearHeaders(self):
        """ Clear headers set so far
        """
        self._handler.headers = {}
 
    def clear(self):
        self._clearHeaders()
        self.truncate()

    def headersSent(self):
        return self._handler.header_written

    def truncate(self):
        """ Truncate buffer
        """
        self._buffer.seek(0)
        self._buffer.buffer().clear()


class QgsRequestHandler(RequestHandler):

    @classmethod
    def init_server(cls):
        if not hasattr(cls, 'qgis_server' ):
            from .utils.qgis import init_qgis_server

            LOGGER.debug("Initializing qgis server")
            qgsserver = init_qgis_server( network_timeout=3000,
                                          enable_processing=False, 
                                          logger=LOGGER, 
                                          verbose=LOGGER.level<=logging.DEBUG)
            setattr(cls, 'qgis_server' , qgsserver )

            # Register AMQP Logger filter
            LogFilter.register_self( qgsserver.serverInterface(), 1000)

    @staticmethod
    def run( router, identity=""):
        try:
            QgsRequestHandler.init_server()
        except:
            LOGGER.critical("Qggis initialization error:\n%s", traceback.format_exc())
            sys.exit(99)

        run_worker(router, QgsRequestHandler, identity=bytes(identity.encode('ascii')))

    def handle_message(self):
        """ Override this method to handle_messages
        """
        project_location = self.request.headers.pop('X-Map-Location')

        request  = Request(self)
        response = Response(self)

        try:
            project, updated = cache_lookup(project_location)
            if updated: 
               # Needed to cleanup cache capabilities cache
               iface = self.qgis_server.serverInterface()
               LOGGER.debug("Cleaning config cache entry %s", iface.configFilePath())
               iface.removeConfigCacheEntry(iface.configFilePath())
        except FileNotFoundError:
            response.sendError(404,"Project '%s' not found" % project_location)
        else:
            self.qgis_server.handleRequest(request, response, project=project)


def main():
    """ Run as command line interface
    """
    import os
    import sys
    import argparse
    from .zeromq.worker import run_worker
    from .version import __description__, __version__
    from .config  import (get_config, read_config_dict, validate_config_path)
    from .logger import setup_log_handler

    parser = argparse.ArgumentParser(description='Qgis Server Worker')
    parser.add_argument('--host'    , metavar="host"   , default='tcp://localhost', help="router host")   
    parser.add_argument('--router'  , metavar='address', default='tcp://{host}:18080', help="router address")
    parser.add_argument('--identity', default="", help="Set worker identity")
    parser.add_argument('--rootdir' , default=get_config('cache')['rootdir'], metavar='PATH', help='Path to qgis projects')
    parser.add_argument('--version', action='store_true', default=False, help="Return version number and exit")
    parser.add_argument('--logging' , choices=['debug', 'info', 'warning', 'error'], 
            default=get_config('logging')['level'].lower(), help="set log level")

    args = parser.parse_args()

    def print_version():
        program = os.path.basename(sys.argv[0])
        print("{name} {version}".format(name=program, version=__version__), file=sys.stderr)

    if args.version:
        print_version()
        sys.exit(1)

    # read configuration dict
    read_config_dict({
        'logging':{ 'level': args.logging.upper() },
        'cache'  :{ 'rootdir': args.rootdir },
    })

    print_version()

    validate_config_path('cache','rootdir')

    setup_log_handler(args.logging)
    print("Log level set to {}\n".format(logging.getLevelName(LOGGER.level)), file=sys.stderr)

    LOGGER.setLevel(getattr(logging, args.logging.upper()))

    QgsRequestHandler.run(args.router.format(host=args.host), identity=args.identity)

    print("Qgis worker terminated", file=sys.stderr)




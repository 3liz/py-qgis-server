#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Qgis server request adapters

    Embedded qgis server in a 0MQ worker 

    see: 
        - https://qgis.org/pyqgis/master/server/QgsBufferServerResponse.html
        - https://qgis.org/pyqgis/master/server/QgsBufferServerRequest.html
"""
import os
import logging
import traceback
import hashlib

try:
    import psutil
except ImportError:
    psutil = None

from datetime import datetime
from time import time
from typing import Dict, Optional, Any, Tuple, Callable

from qgis.PyQt.QtCore import Qt, QBuffer, QIODevice, QByteArray
from qgis.core import QgsProject
from qgis.server import (QgsServerRequest,
                         QgsServerResponse,
                         QgsServerException)

from .zeromq.worker import RequestHandler, run_worker
from .qgscache.cachemanager import (get_cacheservice,
                                    preload_projects,
                                    StrictCheckingError,
                                    UnreadableResourceError,
                                    PathNotAllowedError,
                                    UpdateState,
                                    CacheType)

from .qgscache.observer import Client as CacheObserver

from .plugins import load_plugins
from .config import confservice, configure_qgis_api, qgis_api_endpoints

LOGGER = logging.getLogger('SRVLOG')

HTTP_METHODS = {
    'GET' : QgsServerRequest.GetMethod,
    'PUT' : QgsServerRequest.PutMethod,
    'POST': QgsServerRequest.PostMethod,
    'HEAD': QgsServerRequest.HeadMethod,
    'DELETE': QgsServerRequest.DeleteMethod,
    'PATCH': QgsServerRequest.PatchMethod,
}

class Request(QgsServerRequest):

    def __init__(self, handler: RequestHandler ) -> None:
        """ Create a new QgsServerRequest from zmq handler request
        """
        req = handler.request
        
        # Recreate URL
        location = req.headers.get('X-Forwarded-Url',"")
        query    = req.query.lstrip('?')
        if query:
            location += f"?{query}"

        self._data = req.data
        super().__init__(location, HTTP_METHODS[req.method], headers=req.headers)
         
    def data(self) -> QByteArray: 
        """ Return post/put data a QByteArray
        """
        # Make sure that data is valid
        return QByteArray(self._data) if self._data else QByteArray()


class Response(QgsServerResponse):
    """ Adaptor to handler response

        The data is written at 'flush()' call.
    """

    def __init__(self, handler: RequestHandler, metadata_fn: Callable ) -> None:
        super().__init__()
        self._handler = handler
        self._buffer = QBuffer()
        self._buffer.open(QIODevice.ReadWrite)
        self._numbytes = 0
        self._finish   = False
        self._metadata_fn  = metadata_fn

        self._extra_headers = {}

    def get_metadata(self):
        if self._metadata_fn:
            return self._metadata_fn()
        
    def setExtraHeader( self, key: str, value: str ) -> None:
        # Keep extra headers so we may 
        # set them again on clear()
        self._extra_headers[key] = value
        self.setHeader(key, value)

    def setStatusCode(self, code: int) -> None:
        if not self._handler.header_written:
            self._handler.status_code = code
        else:
            LOGGER.error("Cannot set status code after header written")

    def statusCode(self) -> int:
        return self._handler.status_code

    def finish(self) -> None:
        """ Terminate the request
        """
        self._finish = True
        self.flush()

    def flush(self) -> None:
        """ Write the data to the handler buffer 
            and flush the socket

            Headers will be written at the first call to flush()
        """
        try:
            meta = self.get_metadata()

            self._buffer.seek(0)
            bytesAvail = self._buffer.bytesAvailable()
            LOGGER.debug("%s: Flushing response data: (%d bytes)",self._handler.identity, bytesAvail)
            if self._finish and bytesAvail:
                # Make sure that we have Content-length set
                self._handler.headers['Content-Length']=bytesAvail
            # Take care of the logic: if finish and not handler.header_written then there is no
            # chunk following
            send_more = not self._finish or self._handler.header_written
            if bytesAvail:
                LOGGER.debug("Sending bytes %s (send_more: %s)", bytesAvail, send_more)
                self._handler.send( bytes(self._buffer.data()), send_more, meta )
                self._buffer.buffer().clear()
            else:
                # Return empty response
                LOGGER.debug("Sending empty response (send_more: %s)", send_more)
                self._handler.send( b'', send_more, meta )
            # push the sentinel
            if send_more and self._finish:
                LOGGER.debug("Sending EOF")
                self._handler.send( b'', False, meta )
        except Exception:
            trace = traceback.format_exc()
            LOGGER.error("Caught Exception (worker: %s, msg: %s):\n%s",
                         self._handler.identity, self._handler.msgid,
                         trace)
            del self._handler.headers['Content-Type']
            self.sendError(500, "Internal server error")

    def header(self, key: str) -> str:
        return self._handler.headers.get(key)

    def headers(self) -> Dict[str,str]:
        """ Return headers as dict
        """
        return self._handler.headers
        
    def io(self) -> QIODevice:
        return self._buffer

    def data(self) -> QByteArray:
        """ Return buffer data
        """
        return self._buffer.data()

    def setHeader(self, key: str, value: str) -> None:
        if not self._handler.header_written:
            self._handler.headers[key] = value
        else:
            LOGGER.error("Cannot set header after header written")

    def removeHeader(self, key: str) -> None:
        self._handler.headers.pop(key,None)

    def sendError(self, code: int, message: Optional[str]=None) -> None:
        try:
            if not self._handler.header_written:
                LOGGER.error("%s (%s)", message, code)
                self._handler.status_code = code
                self._handler.send(str(message).encode())
                self._finish = True
            else:
                LOGGER.error("Cannot set error after header written")
        except Exception:
            LOGGER.critical("Unrecoverable exception:\n%s", traceback.format_exc())


    def _clearHeaders(self) -> None:
        """ Clear headers set so far
        """
        self._handler.headers = {}
        self._handler.headers.update(self._extra_headers)
 
    def clear(self) -> None:
        self._clearHeaders()
        self.truncate()

    def headersSent(self) -> bool:
        return self._handler.header_written

    def truncate(self) -> None:
        """ Truncate buffer
        """
        self._buffer.seek(0)
        self._buffer.buffer().clear()


class QgsRequestHandler(RequestHandler):

    @classmethod
    def init_server(cls) -> None:
        """ Initialize qgis server
        """
        if hasattr(cls, 'qgis_server' ):
            return
        
        from .utils.qgis import init_qgis_server

        # Enable qgis server verbosity
        if LOGGER.isEnabledFor(logging.DEBUG):
            os.environ['QGIS_SERVER_LOG_LEVEL'] = '0'
            os.environ['QGIS_DEBUG'] = '1'

        cache_config = confservice['projects.cache']
        trust_mode_on = cache_config.getboolean('trust_layer_metadata')
        if trust_mode_on:
            os.environ['QGIS_SERVER_TRUST_LAYER_METADATA'] = 'yes'

        if cache_config.getboolean('disable_getprint'):
            os.environ['QGIS_SERVER_DISABLE_GETPRINT'] = 'yes'

        # Get refresh interval
        cls._cache_service        = get_cacheservice()
        cls._cache_check_interval = cache_config.getint('check_interval')
        cls._cache_last_check     = time()  
      
        cls._pid = os.getpid()
        cls._advanced_report = cache_config.getboolean('advanced_report')

        if cls._advanced_report:
            if psutil is not None:
                cls._process = psutil.Process(cls._pid)
            else:
                LOGGER.warning("No 'PSUtil' module, advanced report will be disabled")
                cls._advanced_report = False
                cls._process = None

        # Attach cache observer
        if cache_config.getboolean('has_observers'):
            LOGGER.info("Attaching worker cache observer")
            cls._cache_observer = CacheObserver()
            cls._cache_service.add_observer(cls._cache_observer.observe)

        # Configure qgis api
        for name,_ in qgis_api_endpoints(enabled_only=False):
            configure_qgis_api(name)                         
        
        verbose = LOGGER.level<=logging.DEBUG or confservice.getboolean('logging','qgis_info')

        LOGGER.debug("Initializing qgis server")
        qgsserver = init_qgis_server( enable_processing=False, 
                                      logger=LOGGER, 
                                      verbose=verbose)

        serverIface = qgsserver.serverInterface()
        load_plugins(serverIface)

        if confservice['management'].getboolean('enabled'):
            from .management.apis import register_management_apis
            register_management_apis(serverIface)

        preload_projects()

        setattr(cls, 'qgis_server' , qgsserver )

    @classmethod
    def refresh_cache(cls) -> None:
        if cls._cache_check_interval <= 0 or time() - cls._cache_last_check < cls._cache_check_interval:
            return
        LOGGER.debug("Refreshing cache")
        iface = cls.qgis_server.serverInterface()
        for (key, state) in cls._cache_service.refresh():
            # Remove from Qgis server ConfigCache
            if state == UpdateState.UPDATED:
                details = cls._cache_service.peek(key)
                iface.removeConfigCacheEntry(details.project.fileName())
        
        cls._cache_last_check = time()

    @classmethod
    def cache_lookup(cls, key) -> Tuple[QgsProject, UpdateState]:
        return cls._cache_service.lookup(key, refresh = cls._cache_check_interval <= 0)

    @classmethod
    def post_process(cls, idle: bool) -> None:
        """ Post processing operation

            At this time request has been replied and worker is not busy anymore
        """
        cls.refresh_cache()

    @classmethod
    def get_modified_time(cls, key: str, from_cache: bool=True) -> datetime:
        return cls._cache_service.get_modified_time(key, from_cache=from_cache)

    def compute_etag(self, uri: str, last_modified: datetime, request: QgsServerRequest) -> Optional[str]:
        """ Compute ETAG for GetCapabilities requests
        """
        conf = confservice['projects.cache']
        if conf.getboolean('force_etag') or conf.getboolean('trust_layer_metadata'):
            owsrequest = request.parameter('REQUEST') or ""
            if owsrequest.lower() == "getcapabilities":
                hasher = hashlib.sha1()
                hasher.update(request.parameter('SERVICE').lower().encode())
                hasher.update((request.parameter('VERSION') or "").lower().encode())
                hasher.update(uri.encode())
                hasher.update(last_modified.isoformat().encode())
                return '"%s"' % hasher.hexdigest()

    def set_etag_header(self, uri: str, last_modified: datetime, request: QgsServerRequest,
                        response: Response ) -> Optional[str]:
        """ Compute and set etag
        """
        computed_etag = self.compute_etag(uri, last_modified, request )
        if computed_etag:
            response.setExtraHeader("Etag", computed_etag)

        return computed_etag

    def check_etag_header(self, uri: str, last_modified: datetime, request: QgsServerRequest,
                          response: Response) -> bool:
        """ Compute etag and check header
        """
        computed_etag = self.set_etag_header(uri, last_modified, request, response)
        if computed_etag is None:
            return False

        # Check etag header
        etag = self.request.headers.get("If-None-Match","")
        return etag == "*" or etag == computed_etag

    @staticmethod
    def run( router: str, identity: str="", **kwargs: Any) -> None:
        """ Run qgis server worker loop
        """
        QgsRequestHandler.init_server()

        run_worker(router, QgsRequestHandler, identity=bytes(identity.encode('ascii')), 
                   postprocess=QgsRequestHandler.post_process, **kwargs)

    QGIS_NO_MAP_ERROR_MSG = "No project defined. For OWS services: please provide a SERVICE and a MAP parameter" 

    def init_metadata_report(self) -> Dict:
        if self._advanced_report:
            start_mem = self._process.memory_info().rss
            def _metadata_report():
                return {
                    'pid'     : self._pid,
                    'mem_used': self._process.memory_info().rss - start_mem,
                }
            return _metadata_report

    def handle_message(self) -> None:
        """ Override this method to handle_messages
        """
        LOGGER.debug("Handling request: %s", self.msgid)

        project_location = self.request.headers.pop('X-Map-Location', None)
        ogc_scheme       = self.request.headers.pop('X-Ogc-Scheme'  , None)

        metadata_report = self.init_metadata_report()

        request  = Request(self)
        response = Response(self, metadata_report)

        if not project_location:
            # Try to get project from environment
            project_location = os.getenv("QGIS_PROJECT_FILE")
   
        if ogc_scheme == 'OWS': 
            if not project_location and request.parameter('SERVICE'):
                # Prevent qgis for returning 500 when MAP is not defined for
                # OWS services
                LOGGER.error("No project defined for %s", request.parameter('SERVICE'))
                # A project is required
                exception = QgsServerException(self.QGIS_NO_MAP_ERROR_MSG, 400)
                response.write(exception)
                response.finish()
                return

            # Handle HEAD method for OWS requests
            # Note that Qgis Server return 501 on head method on OWS methods
            if request.method() == QgsServerRequest.HeadMethod:
                # We can compute etag without loading resource
                if project_location:
                    last_modified = self.get_modified_time(project_location, from_cache=False)
                    self.set_etag_header(project_location, last_modified, request, response)
                    response.finish()
                    return

        self.handle_qgis_request(ogc_scheme, project_location, request, response)

    def handle_qgis_request(self, ogc_scheme: str, project_location: str, request: Request, response: Response ) -> None:
        """ Handle request passed to Qgis
        """
        if not project_location:
            # Pass request directly
            self.qgis_server.handleRequest(request, response)
            return

        # Handle cached project
        iface = self.qgis_server.serverInterface()
        try:
            project, updated = self.cache_lookup(project_location)
            config_path = project.fileName()
            if updated: 
                # Needed to cleanup cached capabilities
                LOGGER.debug("Cleaning config cache entry %s", config_path)
                iface.removeConfigCacheEntry(config_path)

            last_modified = self.get_modified_time(project_location)

            # Set the project uri in separate header, this
            # is useful for invalidating front-end cache
            response.setExtraHeader('X-Map-Id'      , project_location)
            response.setExtraHeader('Last-Modified' , last_modified.astimezone().isoformat())

            # Check etag for OWS requests
            if ogc_scheme == 'OWS':
                if self.check_etag_header(project_location, last_modified, request, response):
                    response.setStatusCode(304)
                    response.finish()
                    return

        except StrictCheckingError:
            response.sendError(422,f"Invalid layers for project '{project_location}' - strict mode on")
        except UnreadableResourceError:
            response.sendError(422,f"Cannot read project resource '{project_location}'")
        except PathNotAllowedError:
            response.sendError(403,"Project path not allowed")
        except FileNotFoundError:
            response.sendError(404,f"Project '{project_location}' not found")
        else:
            # See https://github.com/qgis/QGIS/pull/9773
            iface.setConfigFilePath(config_path)
            self.qgis_server.handleRequest(request, response, project=project)

    @classmethod
    def get_report(cls):
        report = super(QgsRequestHandler,cls).get_report()

        def _to_json(key: str, project: QgsProject, static: bool):
            return dict(
                key=key,
                filename=project.fileName(),
                last_modified=project.lastModified().toString(Qt.ISODate),
                num_layers=project.count(),
                static=static,
            )

        items = { k:(d,False) for k,d in get_cacheservice().items(CacheType.LRU) }
        items.update( (k,(d,True)) for (k,d) in get_cacheservice().items(CacheType.STATIC) )
        
        report.update(
            cache=[_to_json(k,d.project,static) for (k,(d,static)) in items.items()]
        )
        return report



def main():
    """ Run as command line interface
    """
    import os
    import sys
    import argparse
    from .version import __manifest__
    from .config  import (confservice, load_configuration, read_config_file, validate_config_path)
    from .logger import setup_log_handler

    parser = argparse.ArgumentParser(description='Qgis Server Worker')
    parser.add_argument('-d','--debug', action='store_true', default=False, help="debug mode") 
    parser.add_argument('-c','--config', metavar='PATH', nargs='?', dest='config',
                        default=None, help="Configuration file")
    parser.add_argument('--proxy-host' , dest="hostaddr", metavar="host"   , default='localhost' , help="router host")   
    parser.add_argument('--identity'   , default="", help="Set worker identity")
    parser.add_argument('--rootdir'    , default=argparse.SUPPRESS, metavar='PATH', help='Path to qgis projects')
    parser.add_argument('--version'    , action='store_true', default=False, help="Return version number and exit")

    args = parser.parse_args()

    def print_version(verbose=False) -> None:
        """ Display version infos
        """
        from .utils.qgis import print_qgis_version
        program = os.path.basename(sys.argv[0])
        print("{program} {version} (build {buildid},commit {commitid})".format(program=program,**__manifest__))
        print_qgis_version(verbose=verbose)

    if args.version:
        print_version(verbose=args.debug)
        sys.exit(1)
    else:
        print_version()

    load_configuration()

    if args.config:
        with open(args.config, mode='rt') as config_file:
            read_config_file(config_file)

    # Override config
    def set_arg( section:str, name:str ) -> None:
        if name in args:
            confservice.set( section, name, str(getattr(args,name)))

    set_arg('projects.cache', 'rootdir')
    set_arg('zmq', 'hostaddr')

    if args.debug:
        # Force debug mode
        confservice.set('logging', 'level', 'DEBUG')

    print_version()

    validate_config_path('projects.cache','rootdir')

    setup_log_handler(confservice.get('logging','level'))
    print("Log level set to {}\n".format(logging.getLevelName(LOGGER.level)), file=sys.stderr)

    broadcastaddr = confservice.get('zmq','broadcastaddr')
    router = confservice.get('zmq', 'bindaddr')

    QgsRequestHandler.run(router, identity=args.identity,
                          broadcastaddr=broadcastaddr)

    print("Qgis worker terminated", file=sys.stderr)




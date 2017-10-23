# -*- encoding=utf-8 -*-

from __future__ import print_function

import sys
import json
import logging
import re

from time import time

from .handlers import BasicHandler, RPCHandler
from ..logger import REQ

app    = RPCHandler()
notify = BasicHandler()


def setup(config):
    """ Initialize qgis
    """
    app.config = config

    # Set path to qgis python
    python_path = config['qgis_python_path']
    sys.path.append(python_path)

    # Set up logger
    logger = logging.getLogger('qgis_logger')
    app.logger = logger

    # Init qgis
    logging.info("Initializing qgis (PYTHONPATH={})".format(python_path))
    from qgis.server import QgsServer, QgsServerFilter

    # Set a log filter for qgis request
    class LogFilter(QgsServerFilter):
        def requestReady(self):
            self.t_start = time()

        def responseComplete(self):
            req = self.serverInterface().requestHandler()
            params = req.parameterMap()
            if not params:
                return
            ms = int((time() - self.t_start) * 1000)
            status = "error" if req.exceptionRaised() else "ok"
            params.update(RESPONSE_TIME=ms, RESPONSE_STATUS=status, WORKSPACE=config['workspace'])
            logger.log(REQ, json.dumps(params))
      
    app.qgis_server = QgsServer()
    app.qgis_server.init()

    # Get server interface
    iface = app.qgis_server.serverInterface()
    iface.registerFilter(LogFilter(iface))

    app.server_iface = iface


#
# commands
#

@app.command('wms')
def webservice(request, query):
    """ Call qgis server request
    """
    # Make sure that 
    # Request qgis server
    heads, body = app.qgis_server.handleRequest(query)
    # Parse headers
    headers = dict( head.split(': ',1) for head in heads.split('\n') if head )
    # Return response with the appropriate content type
    request.reply(body, content_type=headers.get('Content-Type'), headers=headers )


@app.command('status')
def status(request):
    """ Return the status for the server
    """
    config   = app.config
    response = dict(config = dict(config.items()))
   
    manifest = config.section('manifest', no_failure=True)
    if manifest is not None:
        response.update(manifest = dict(
                        version  = manifest.version,
                        buildid  = manifest.timestamp,
                        commitid = manifest.commitid))

    qgis_manifest = config.section('qgis_manifest', no_failure=True)
    if qgis_manifest is not None:   
        response.update(qgis_version = qgis_manifest.version)

    request.reply(json.dumps(response, sort_keys=True),
                  content_type="application/json",
                  content_encoding="utf-8")


@notify.command('flush')
def purge_project_layers(request, path):
    """ Remove project layers from qgis server cache
    """
    app.server_iface.removeConfigCacheEntry(path)
    app.server_iface.removeProjectLayers(path)
    logging.info('FLUSH\t%s' % path)




#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Qgis project cache and protocol resolver
"""

import os
import logging

from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

from typing import Tuple

from .utils.filecache import FileCache
from .utils.decorators import singleton

from .config import confservice

from qgis.core import QgsProjectBadLayerHandler, QgsProject
from qgis.server import QgsServerProjectUtils

LOGGER = logging.getLogger('SRVLOG')


class StrictCheckingError(Exception):
    pass



class BadLayerHandler(QgsProjectBadLayerHandler):

    def __init__(self):
        super().__init__()
        self.badLayerNames = set()

    def handleBadLayers( self, layers ) -> None: 
        """ See https://qgis.org/pyqgis/3.0/core/Project/QgsProjectBadLayerHandler.html
        """
        super().handleBadLayers( layers )

        nameElements = (l.firstChildElement("layername") for l in layers if l)
        self.badLayerNames = set(elem.text() for elem in nameElements if elem)
            
    def validatLayers( self, project: QgsProject ) -> bool:
        """ Check layers
            
            If layers are excluded do not count them as bad layers
            see https://github.com/qgis/QGIS/pull/33668
        """
        if self.badLayerNames:
            restricteds = set(QgsServerProjectUtils.wmsRestrictedLayers(project))
            return self.badLayerNames.issubset(restricteds)
        return True

@singleton
class _Cache(FileCache):

    def __init__(self) -> None:
        config    = confservice['cache']
        cachesize = config.getint('size')
        rootdir   = Path(config['rootdir'])

        self._strict_check = config.getboolean('strict_check')

        protocols = {}

        def get_protocol_path(scheme: str) -> Path:
            """ Resolve protocol path
            """
            LOGGER.debug("Resolving '%s' protocol", scheme)
            rootpath = protocols.get(scheme)
            if not rootpath:
                varname  = "QGSRV_%s_PROTOCOL" % scheme.replace('-','_').upper()
                LOGGER.debug("Lookup scheme '%s' in variable variable %s", scheme, varname) 
                rootpath = os.environ.get(varname)
                if not rootpath:
                    LOGGER.error('Undefined protocol %s' % scheme)
                    raise FileNotFoundError(scheme)
                rootpath = Path(rootpath)
                # XXX Security concern
                if not rootpath.is_absolute():
                    raise ValueError("protocol path must be absolute not %s" % rootpath)
                protocols[scheme] = rootpath
            return rootpath

        class _Store:
            def getpath(self, key: str) -> Tuple[str, datetime]:
                
                key = urlparse(key)
                if not key.scheme or key.scheme == 'file':
                    rootpath = rootdir
                else:
                    rootpath = get_protocol_path(key.scheme)
                
                key = key.path.strip('/')
                path = rootpath / key
                for sfx in ('.qgs','.qgz'):
                    path = path.with_suffix(sfx)
                    if path.is_file():
                        # Get modification time for the file
                        timestamp = datetime.fromtimestamp(path.stat().st_mtime)
                        return str(path), timestamp

                # No file found
                raise FileNotFoundError(str(path))

        # Init FileCache
        super().__init__(size=cachesize, store=_Store())  

    def on_cache_update(self, key: str, path: str) -> None:
        LOGGER.info("Cache '%s' updated with path: %s" % (key,path)) 

    def read_project(self, path) -> QgsProject:
        """ Override
        """
        project = self.QgsProject()
        badlayerh = BadLayerHandler()
        project.setBadLayerHandler(badlayerh)
        project.read(path)
        if self._strict_check and not badlayerh.validatLayers(project):
            raise StrictCheckingError
        return project


def cache_lookup( path ):
    return _Cache().lookup(path)



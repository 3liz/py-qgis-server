#
# Copyright 2020 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" File protocol handler
"""
import logging
import urllib.parse

from typing import Tuple, Optional
from datetime import datetime
from pathlib import Path

from qgis.core import QgsProject
from pyqgisservercontrib.core import componentmanager

LOGGER = logging.getLogger('SRVLOG')

ALLOWED_SFX=('.qgs','.qgz')

__all__= []

@componentmanager.register_factory('@3liz.org/cache/protocol-handler;1?scheme=file')
class FileProtocolHandler:
    """ Handle file protocol
    """

    def __init__(self):
        pass

    def _check_file(self, path: Path) -> bool:
        """
        """
        if not path.is_absolute():
            raise ValueError(f"file path must be absolute not {path}")
    
        exists = False
        if path.suffix not in ALLOWED_SFX:
            for sfx in ALLOWED_SFX:
                path = path.with_suffix(sfx)
                exists = path.is_file()
                if exists:
                    break
        else:
            exists = path.is_file()

        return path if exists else None

    def get_modified_time( self, url: urllib.parse.ParseResult) -> datetime:
        """ Return the modified date time of the project referenced by its url
        """
        path = self._check_file(Path(url.path))
        return datetime.fromtimestamp(path.stat().st_mtime)

    def get_project( self, url: Optional[urllib.parse.ParseResult], strict: Optional[bool]=None,
                     project: Optional[QgsProject]=None,
                     timestamp: Optional[datetime]=None) -> Tuple[QgsProject, datetime]:
        """ Create or return a proect
        """
        if url:
            path = self._check_file(Path(url.path))
        elif project:
            path = self._check_file(project.fileName())
        else:
            raise ValueError('Cannot get path from arguments')

        if not path:
            LOGGER.error("File protocol handler: File not found: %s", str(path)) 
            raise FileNotFoundError(str(path))

        modified_time = datetime.fromtimestamp(path.stat().st_mtime)
        if timestamp is None or timestamp < modified_time:
            cachmngr  = componentmanager.get_service('@3liz.org/cache-manager;1')
            project   = cachmngr.read_project(str(path), strict=strict)
            timestamp = modified_time

        return project, timestamp


#
# Copyright 2020 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Cache manager for Qgis Projects
"""

import logging
import urllib.parse

from urllib.parse import urlparse, urljoin, parse_qs
from typing import Tuple, Optional, Sequence
from collections import namedtuple
from pathlib import Path
from datetime import datetime

from ..utils.lru import lrucache
from ..config import confservice

from qgis.PyQt.QtCore import Qt 
from qgis.core import QgsProjectBadLayerHandler, QgsProject, QgsMapLayer
from qgis.server import QgsServerProjectUtils

from pyqgisservercontrib.core import componentmanager

# Import default handlers for auto-registration
from .handlers import * # noqa: F403,F401

LOGGER = logging.getLogger('SRVLOG')


class StrictCheckingError(Exception):
    pass


class PathNotAllowedError(Exception):
    pass


class UnreadableResourceError(Exception):
    """ Indicates that the  ressource exists but is not readable
    """
    pass


CacheDetails = namedtuple("CacheDetails",('project','timestamp'))


CACHE_MANAGER_CONTRACTID = '@3liz.org/cache-manager;1'


def _merge_qs( query1: str, query2: str ) -> str:
    """ Merge query1 with query2 but coerce values
        from query1 
    """
    params_1 = parse_qs(query1)
    params_2 = parse_qs(query2)
    params_2.update(params_1)
    return '&'.join('%s=%s' % (k,v[0]) for k,v in params_2.items())


@componentmanager.register_factory(CACHE_MANAGER_CONTRACTID)
class QgsCacheManager:
    """ Handle Qgis project cache 
    """

    StrictCheckingError=StrictCheckingError
    PathNotAllowedError=PathNotAllowedError
    UnreadableResourceError=UnreadableResourceError

    def __init__(self) -> None:
        """ Initialize cache

            :param size: size of the lru cache
        """
        cnf = confservice['projects.cache']

        size = cnf.getint('size')

        self._create_project = QgsProject
        self._cache = lrucache(size)
        self._strict_check         = cnf.getboolean('strict_check')
        self._trust_layer_metadata = cnf.getboolean('trust_layer_metadata')
        self._disable_getprint     = cnf.getboolean('disable_getprint')
        self._disable_owsurls      = cnf.getboolean('disable_owsurls', fallback=False)
        self._aliases = {}
        self._default_scheme = cnf.get('default_handler',fallback='file')

        # Set the base url for file protocol
        self._aliases['file'] = 'file:///%s/' % cnf.get('rootdir').strip('/')

        # Load protocol handlers
        componentmanager.register_entrypoints('qgssrv_contrib_protocol_handler')

    def clear(self) -> None:
        """ Clear the whole cache
        """
        self._cache.clear()

    def items(self) -> Sequence[Tuple[str,CacheDetails]]:
        return self._cache.items()

    def remove_entry(self, key: str) -> None:
        """ Remove cache entry
        """
        del self._cache[key]

    def resolve_alias(self, key: str ) -> urllib.parse.ParseResult:
        """ Resolve scheme from configuration variables
        """
        url    = urlparse(key)
        scheme = url.scheme or self._default_scheme
        LOGGER.debug("Resolving '%s' protocol", scheme)
        baseurl = self._aliases.get(scheme)
        if not baseurl:
            try:
                # Check for user-defined scheme
                baseurl = confservice.get('projects.schemes',scheme.replace('-','_').lower())
            except KeyError:
                pass
            else:
                LOGGER.info("Scheme '%s' aliased to %s", scheme, baseurl)
                self._aliases[scheme] = baseurl
        if baseurl:
            if '{path}' in baseurl:
                url = urlparse(baseurl.format(path=url.path))
            else:
                baseurl = urlparse(baseurl)
                # Build a new query from coercing with base url params 
                query = _merge_qs(baseurl.query, url.query)
                # XXX Note that the path of the base url must be terminated by '/'
                # otherwise urljoin() will replace the base name - may be not what we want
                url = urlparse(urljoin(baseurl.geturl(),url.path+'?'+query))
                # Make sure that the result url path is relative to base url
                try:
                    # Ensure that if an absolute path is given, we may extract
                    # a relative path to the base url - note that the base url may
                    # not have a leading '/'
                    Path(url.path).relative_to(Path('/') / baseurl.path)
                except ValueError:
                    LOGGER.error("The path '%s' is outside base path '%s'", url.path, baseurl.path)
                    raise PathNotAllowedError()                    

        return url

    def get_project(self, key: str, strict: Optional[bool]=None) -> Tuple[QgsProject,datetime,bool]:
        """ Load project 
        """
        url = self.resolve_alias(key)
    
        scheme = url.scheme or self._default_scheme
        # Retrieve the protocol-handler
        try:
            store = componentmanager.get_service('@3liz.org/cache/protocol-handler;1?scheme=%s' % scheme)
        except componentmanager.FactoryNotFoundError:
            LOGGER.error("No protocol handler found for %s", scheme) 
            raise FileNotFoundError(key)

        # Get details for the project
        details = self._cache.peek(key)
        if details is not None:
            project, timestamp  = store.get_project( url, strict=strict, **details._asdict())
            needupdate = timestamp != details.timestamp
        else:
            project, timestamp = store.get_project(url, strict=strict)
            needupdate = True

        return project, timestamp, needupdate
        
    def update_entry(self, key: str) -> bool:
        """ Update the cache

            :param key: The key of the entry to update
            :return: true if the entry has been updated
        """
        project, timestamp, updated = self.get_project(key)
        self._cache[key] = CacheDetails(project, timestamp)
        return updated

    def peek(self, key: str) -> Optional[CacheDetails]:
        """ Return entry if it exists
        """
        return self._cache.peek(key)

    def lookup(self, key: str) -> Tuple[QgsProject, bool]:
        """ Lookup entry from key
        """
        updated = self.update_entry(key)
        return self._cache[key].project, updated

    def prepare_project(self, project: QgsProject ) -> None:
        """ Set project configuration
        """
        if self._disable_owsurls:
            # Disable ows urls defined in project
            # May be needed because it overrides 
            # any proxy settings
            project.writeEntry("WMSUrl","/", "")
            project.writeEntry("WFSUrl","/", "")
            project.writeEntry("WCSUrl","/", "")

    def read_project(self, path: str, strict: Optional[bool]=None) -> QgsProject:
        """ Read project from path

            May be used by protocol-handlers to instanciate project
            from path.
        """
        LOGGER.debug("Reading Qgis project %s", path)
        project = self._create_project()

        readflags = QgsProject.ReadFlags()
        if self._trust_layer_metadata:
            readflags |= QgsProject.FlagTrustLayerMetadata
        if self._disable_getprint:
            readflags |= QgsProject.FlagDontLoadLayouts 
        badlayerh = BadLayerHandler()
        project.setBadLayerHandler(badlayerh)
        project.read(path,  readflags)

        strict = self._strict_check if strict is None else strict
        if strict and not badlayerh.validateLayers(project):
            raise StrictCheckingError

        self.prepare_project(project)
        return project


class BadLayerHandler(QgsProjectBadLayerHandler):

    def __init__(self):
        super().__init__()
        self.badLayerNames = set()

    def handleBadLayers( self, layers ) -> None:
        """ See https://qgis.org/pyqgis/3.0/core/Project/QgsProjectBadLayerHandler.html
        """
        super().handleBadLayers( layers )

        nameElements = (lyr.firstChildElement("layername") for lyr in layers if lyr)
        self.badLayerNames = set(elem.text() for elem in nameElements if elem)

    def validateLayers( self, project: QgsProject ) -> bool:
        """ Check layers
            
            If layers are excluded do not count them as bad layers
            see https://github.com/qgis/QGIS/pull/33668
        """
        if self.badLayerNames:
            LOGGER.debug("Found bad layers: %s", self.badLayerNames)
            restricteds = set(QgsServerProjectUtils.wmsRestrictedLayers(project))
            return self.badLayerNames.issubset(restricteds)
        return True


def get_cacheservice() -> QgsCacheManager:
    return componentmanager.get_service(CACHE_MANAGER_CONTRACTID)


def preload_projects_file( path: Path, cacheservice: QgsCacheManager ) ->  int:
    """ Preload projects from configuration file
    """
    conf_file = Path(path)
    if not conf_file.exists():
        LOGGER.error("%s file do not exists, ignoring preload config", path)
        return 0

    # No point to preload more files than the cache size
    maxfiles = confservice['projects.cache'].getint('size')
    loaded_so_far = 0
    
    # Read the projects, strip comments 
    with conf_file.open() as fp:
        for p in filter(None,(line.strip('\n ').partition('#')[0] for line in fp.readlines())):
            p = p.strip(' ')
            try:
                project, updated = cacheservice.lookup(p)
            except StrictCheckingError:
                LOGGER.error("Preload: '%s' as invalid layers - strict mode on" , p)
            except PathNotAllowedError:
                LOGGER.error("Preload: '%s' path not allowed", p)
            except FileNotFoundError:
                LOGGER.error("Preload: '%s' not found", p)
            else:
                LOGGER.info("Preload: '%s' loaded", p)
                loaded_so_far += 1
            if loaded_so_far >= maxfiles:
                LOGGER.warning("Preload: cache size reached")
                break
    return loaded_so_far


def preload_projects() -> None:
    """ Preload projects in cache
    """
    confpath = confservice['projects.cache'].get('preload_config', fallback=None)
    if not confpath:
        return

    preload_projects_file( confpath, get_cacheservice() )


def get_project_summary( key: str, project: QgsProject ):
    """ Return json summary for cached project
    """
    def layer_summary( layer_id: str, layer: QgsMapLayer ):
        return dict(
            id=layer_id,
            name=layer.name(),
            source=layer.publicSource(),
            crs=layer.crs().userFriendlyIdentifier(),
            valid=layer.isValid(),
            spatial=layer.isSpatial(),
        )

    layers = [layer_summary(idstr,l) for (idstr,l) in project.mapLayers().items()]

    return dict(
        cache_key=key,
        filename=project.fileName(),
        bad_layers_count=sum(1 for ls in layers if not ls['valid']),
        layers=layers,
        crs=project.crs().userFriendlyIdentifier(),
        last_modified=project.lastModified().toString(Qt.ISODate)
    )


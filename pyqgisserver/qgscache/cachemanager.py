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
import traceback

from urllib.parse import urlparse, urlunparse, urljoin, parse_qs
from typing import Any, Tuple, Optional, Sequence, NamedTuple, Callable, Generator
from collections import OrderedDict
from pathlib import Path
from datetime import datetime
from enum import Enum

from ..utils.lru import lrucache
from ..config import confservice

from .types import UpdateState

from qgis.PyQt.QtCore import Qt 
from qgis.core import (QgsApplication,
                       QgsProjectBadLayerHandler, 
                       QgsProject, 
                       QgsMapLayer)

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


class CacheDetails(NamedTuple):
    project: QgsProject 
    timestamp: datetime


CACHE_MANAGER_CONTRACTID = '@3liz.org/cache-manager;1'



def _merge_qs( query1: str, query2: str ) -> str:
    """ Merge query1 with query2 but coerce values
        from query1 
    """
    params_1 = parse_qs(query1)
    params_2 = parse_qs(query2)
    params_2.update(params_1)
    return '&'.join('%s=%s' % (k,v[0]) for k,v in params_2.items())


class CacheType(Enum): 
    LRU = 'lru'
    STATIC = 'static'


class QgisStorageHandler:
    """ Handler for handling Qgis supported storage
        throught the `QgsProjectStorage` api.
    """
    def __init__(self):
        pass

    def get_storage_metadata( self, uri: str ):
        # Check out for storage
        storage = QgsApplication.projectStorageRegistry().projectStorageFromUri(uri)
        if not storage:
            LOGGER.error("No project storage found for %s", uri)
            raise FileNotFoundError(uri)
        res, metadata = storage.readProjectStorageMetadata( uri )
        if not res:
            LOGGER.error("Failed to read storage metadata for %s", uri)
            raise FileNotFoundError(uri)
        return metadata

    def get_modified_time( self, url: urllib.parse.ParseResult) -> datetime:
        """ Return the modified date time of the project referenced by its url
        """
        metadata = self.get_storage_metadata(urlunparse(url))
        return metadata.lastModified.toPyDateTime()

    def get_project( self, url: urllib.parse.ParseResult,
                     project: Optional[QgsProject]=None,
                     timestamp: Optional[datetime]=None) -> Tuple[QgsProject, datetime]:
        """ Create or return a project
        """
        uri = urlunparse(url)

        metadata = self.get_storage_metadata(uri)
        modified_time = metadata.lastModified.toPyDateTime()

        if timestamp is None or timestamp < modified_time:
            cachmngr  = componentmanager.get_service('@3liz.org/cache-manager;1')
            project   = cachmngr.read_project(uri)
            timestamp = modified_time

        return project, timestamp


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
        self._lru_cache            = lrucache(size)
        self._static_cache         = OrderedDict()
        self._strict_check         = cnf.getboolean('strict_check')
        self._trust_layer_metadata = cnf.getboolean('trust_layer_metadata')
        self._disable_getprint     = cnf.getboolean('disable_getprint')
        self._disable_owsurls      = cnf.getboolean('disable_owsurls', fallback=False)
        self._aliases = {}
        self._default_scheme = cnf.get('default_handler')
        self._observers = []   

        allowed_schemes = cnf.get('allow_storage_schemes')
        if allowed_schemes != '*':
            allowed_schemes = [s.strip() for s in allowed_schemes.split(',')]
        self._allowed_schemes = allowed_schemes
    
        # Set the base url for file protocol
        self._aliases['file'] = 'file:///%s/' % cnf.get('rootdir').strip('/')

        if self._disable_getprint:
            LOGGER.info("** Cache: Getprint disabled")

        if self._trust_layer_metadata:
            LOGGER.info("** Cache: Trust Layer Metadata on")

        # Load protocol handlers
        componentmanager.register_entrypoints('qgssrv_contrib_protocol_handler')

    def add_observer( self, observer: Callable[[str,datetime,int],None] ) -> None: 
        """ Add observer for cache invalidation
        """
        self._observers.append(observer)

    def notify_observers( self, key: str, modified_time: datetime,
                          state: UpdateState) -> None:
        """ Notify all observers
        """
        if not self._observers:
            return

        modified_time = modified_time.replace(microsecond=0)
        for obs in self._observers:
            try:
                obs(key, modified_time, int(state))
            except Exception:
                LOGGER.critical("Uncaugh error in observer: %s\n%s", obs, traceback.format_exc())

    @property
    def trust_mode_on(self) -> bool:
        return self._trust_layer_metadata

    @property
    def strict_mode_on(self) -> bool:
        return self._strict_check

    def items(self, cachetype: CacheType = CacheType.LRU) -> Sequence[Tuple[str,CacheDetails]]:
        if cachetype == CacheType.LRU:
            return self._lru_cache.items()
        elif cachetype == CacheType.STATIC:
            return self._static_cache.items()

    def resolve_alias(self, key: str ) -> urllib.parse.ParseResult:
        """ Resolve scheme from configuration variables
        """
        url    = urlparse(key)
        scheme = url.scheme or self._default_scheme
        LOGGER.debug("Resolving '%s' protocol for '%s'", scheme, key)
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

    def get_protocol_handler(self, key: str, scheme: Optional[str] ) -> Any:
        """ Find protocol handler for the given scheme
        """
        scheme = scheme or self._default_scheme
        # Check for allowed schemes
        if self._allowed_schemes != '*' and scheme not in self._allowed_schemes:
            LOGGER.error("Scheme %s not allowed", scheme)
            raise PathNotAllowedError(key)
        # Retrieve the protocol-handler
        try:
            store = componentmanager.get_service('@3liz.org/cache/protocol-handler;1?scheme=%s' % scheme)
        except componentmanager.FactoryNotFoundError:
            # Fallback to Qgis storage handler
            store = QgisStorageHandler()

        return store 

    def refresh(self) -> Generator[Tuple[str,UpdateState], None, None]:
        """ Refresh all entries

            keys are returned from most recently user to the last recently,
            then we have to update in reverse for preserving order 
        """
        # Update static cache;
        for key,_ in self.items(CacheType.STATIC):
            self.update_static_entry(key)

        # Update both caches
        keys = reversed([k for k,_ in self.items(CacheType.LRU)])
        return ((key, self.update_entry(key)) for key in keys)

    def peek(self, key:str, cachetype: Optional[CacheType] = None) -> CacheDetails:
        """ Return cache details 
        """
        if cachetype == CacheType.LRU:
            return self._lru_cache.peek(key)
        elif cachetype == CacheType.STATIC:
            return self._static_cache.get(key)
        else:
            return self._lru_cache.peek(key) or self._static_cache.get(key)

    def get_modified_time(self, key: str, from_cache: bool=True) -> datetime:
        """ Get the modified time for the given project uri
        """
        details = self.peek(key)
        if details:
            if from_cache:
                # Return from cached resource
                return details.timestamp.replace(microsecond=0)

            # Trust Qgis to return modified time
            last_modified = details.project.lastModified()
            if not last_modified.isValid():
                # Occurs if resource is not valid 
                LOGGER.error("QgsProject::lastModified() returned invalid date time for %s", 
                             details.project.fileName())
                raise FileNotFoundError(key)
            last_modified = last_modified.toPyDateTime()
        else:
            # Get modified 
            url = self.resolve_alias(key)
            store = self.get_protocol_handler(key, url.scheme)
            last_modified = store.get_modified_time(url)

        return last_modified.replace(microsecond=0)

    def _get_project_details(self, key: str, 
                             details: Optional[CacheDetails]) -> Tuple[CacheDetails, bool]: 
        """ Return updated project details
        """
        url   = self.resolve_alias(key)
        store = self.get_protocol_handler(key, url.scheme)

        if details is not None:
            project, timestamp  = store.get_project(url, **details._asdict())
            update = UpdateState.UPDATED if timestamp != details.timestamp else UpdateState.UNCHANGED
        else:
            project, timestamp = store.get_project(url)
            update = UpdateState.INSERTED

        return CacheDetails(project, timestamp), update

    def update_static_entry( self, key: str ) -> UpdateState:
        """ Update static cache
        """
        details, update = self._get_project_details(key, self._static_cache.get(key))
        self._static_cache[key] = details
        return update

    def update_entry(self, key: str) -> UpdateState:
        """ Update LRU entry
        """
        # Get details for the project
        details = self._lru_cache.peek(key)

        # Lookup in static cache
        if not details and key in self._static_cache:
            details = self._static_cache[key]
            details, update = self._get_project_details(key, details)
            if update == UpdateState.UPDATED:
                self._static_cache[key] = details
            # LRU is updated
            update = UpdateState.INSERTED
        else:
            details, update = self._get_project_details(key, details)

        self._lru_cache[key] = details

        # Notify
        if update:
            LOGGER.info("Updated project '%s' in cache", key),
            self.notify_observers(key, details.timestamp, update)

        return update

    def lookup(self, key: str, refresh: bool = True) -> Tuple[QgsProject, UpdateState]:
        """ Lookup entry from key

            If refresh is False, return actual cache
            content without refresh.
        """
        if not refresh:
            # Lookup LRU
            details = self.peek(key, CacheType.LRU)
            if details:
                return details.project, UpdateState.UNCHANGED
            # Update from static cache
            details = self.peek(key, CacheType.STATIC)
            if details:
                self._lru_cache[key] = details
                return details.project, UpdateState.UPDATED
           
        update = self.update_entry(key)
        return self._lru_cache[key].project, update

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
            project.writeEntry("WMTSUrl","/", "")

    def read_project(self, uri: str) -> QgsProject:
        """ Read project from path

            May be used by protocol-handlers to instanciate project
            from uri.
        """
        LOGGER.debug("Reading Qgis project %s", uri)
        project = self._create_project()

        readflags = QgsProject.ReadFlags()
        if self._trust_layer_metadata:
            readflags |= QgsProject.FlagTrustLayerMetadata
        if self._disable_getprint:
            readflags |= QgsProject.FlagDontLoadLayouts 
        badlayerh = BadLayerHandler()
        project.setBadLayerHandler(badlayerh)
        if not project.read(uri,  readflags):
            raise RuntimeError(f"Failed to read Qgis project {uri}")

        if self._strict_check and not badlayerh.validateLayers(project):
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
            LOGGER.error("Found bad layers: %s", self.badLayerNames)
            restricteds = set(QgsServerProjectUtils.wmsRestrictedLayers(project))
            return self.badLayerNames.issubset(restricteds)
        return True


def get_cacheservice() -> QgsCacheManager:
    return componentmanager.get_service(CACHE_MANAGER_CONTRACTID)


def preload_projects_file( path: Path, cacheservice: QgsCacheManager ) ->  int:
    """ Preload projects from configuration file in static cache
    """
    conf_file = Path(path)
    if not conf_file.exists():
        LOGGER.error("%s file do not exists, ignoring preload config", path)
        return 0
    
    loaded_so_far = 0

    # Read the projects, strip comments 
    with conf_file.open() as fp:
        for p in filter(None,(line.strip('\n ').partition('#')[0] for line in fp.readlines())):
            p = p.strip(' ')
            try:
                cacheservice.update_static_entry(p)
            except StrictCheckingError:
                LOGGER.error("Preload: '%s' as invalid layers - strict mode on" , p)
            except PathNotAllowedError:
                LOGGER.error("Preload: '%s' path not allowed", p)
            except FileNotFoundError:
                LOGGER.error("Preload: '%s' not found", p)
            else:
                loaded_so_far += 1
                LOGGER.info("Preload: '%s' loaded", p)

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

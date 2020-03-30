#
# Copyright 2020 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Cache manager for Qgis Projects
"""

import os
import logging
import urllib.parse

from urllib.parse import urlparse, urljoin, parse_qs
from typing import TypeVar, Tuple, Dict
from collections import namedtuple

from ..utils.lru import lrucache
from ..config import confservice

from qgis.core import QgsProjectBadLayerHandler, QgsProject
from qgis.server import QgsServerProjectUtils

from pyqgisservercontrib.core import componentmanager

# Import default handlers
from .handlers import *

LOGGER = logging.getLogger('SRVLOG')

CacheDetails = namedtuple("CacheDetails",('project','timestamp'))


class StrictCheckingError(Exception):
    pass


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

    def __init__(self) -> None:
        """ Initialize cache

            :param size: size of the lru cache
        """
        cnf = confservice['projects.cache']

        size = cnf.getint('size')

        self._create_project = QgsProject
        self._cache = lrucache(size)
        self._strict_check = cnf.getboolean('strict_check')
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

        return url

    def update_entry(self, key: str) -> bool:
        """ Update the cache

            :param key: The key of the entry to update
            :param force: Force updating entry

            :return: true if the entry has been updated
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
            project, timestamp  = store.get_project( url, **details._asdict())
            updated = timestamp != details.timestamp
        else:
            project, timestamp = store.get_project(url)
            updated = True
        self._cache[key] = CacheDetails(project, timestamp)
        return updated

    def peek(self, key: str) -> CacheDetails:
        """ Return entry if it exists
        """
        return self._cache.peek(key)

    def lookup(self, key: str) -> Tuple[QgsProject, bool]:
        """ Lookup entry from key
        """
        updated = self.update_entry(key)
        return self._cache[key].project, updated

    def read_project(self, path: str) -> QgsProject:
        """ Read project from path

            May be used by protocol-handlers to instanciate project
            from path.
        """
        LOGGER.debug("Reading Qgis project %s", path)
        project = self._create_project()
        badlayerh = BadLayerHandler()
        project.setBadLayerHandler(badlayerh)
        project.read(path)
        if self._strict_check and not badlayerh.validatLayers(project):
            raise StrictCheckingError
        return project




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
            LOGGER.debug("Found bad layers: %s", self.badLayerNames)
            restricteds = set(QgsServerProjectUtils.wmsRestrictedLayers(project))
            return self.badLayerNames.issubset(restricteds)
        return True


cacheservice = componentmanager.get_service(CACHE_MANAGER_CONTRACTID)


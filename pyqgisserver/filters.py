#
# Copyright 2019 3liz
# Author: David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


""" Define middleware filters

    Declare filters as

    @blockingfilter(pri=100, uri="/ows/")
    def myfilter1( handller: tornado.web.RequestHandler, *args ) -> None:
        ...

    @asyncfilter(pri=100, uri="/ows/")
    async def myfilter2( handller: tornado.web.RequestHandler, *args) -> None:
        ...


    Filters are applied before sending the request, a filter can return response or 
    raise exception based on authorization rules.

    Registering filters:

    Modules implementing filters must register their filters using setup.py entry_points with the 
    key 'pyqgisserver_filters'

    def register_filters():
        # Do initialization stuff
        return [ myfilter1, myfilter2 ]
"""

import functools
import logging
import tornado.web

from typing import Coroutine, Mapping, List, Callable, Awaitable

from tornado.web import HTTPError


LOGGER = logging.getLogger('QGSRV')

class ServerFilter:
    pass


def load_filters( default_uri: str ) -> Mapping[str,List[ServerFilter]]:
    """ Load filters and return a Mapping
    """
    from pkg_resources import iter_entry_points
   
    filters = { default_uri: [] }
    for ep in iter_entry_points("pyqgisserver_filters"):
        LOGGER.info("Loading filters from %s", ep.name)
        for filt in ep.load()():
            uri = filt.uri or default_uri
            fls = filters.get(uri,[])
            fls.append(filt)
            filters[uri] = fls
    # Sort filters
    for flist in filters.values():
        flist.sort(key=lambda f: f.pri, reverse=True)
    return filters


class asyncfilter(ServerFilter):
    """ Decorator for asynchronous request filter

        Assume that the function return a  coroutine
    """

    def __init__(self, uri=None, pri=0):
        self.pri = pri
        self.uri = uri

    def __call__(self, fn: Callable[[tornado.web.RequestHandler], Awaitable[None]]) -> 'asyncfilter':
        self.fn = fn
        return self

    def apply( self, handler: tornado.web.RequestHandler, *args ) -> Coroutine:
        return self.fn(handler, *args)


class blockingfilter(ServerFilter):
    """ Decorator for synchronous request filter
    """

    def __init__(self, pri=0, uri=None):
        self.pri = pri
        self.uri = uri

    def __call__(self, fn):
        self.fn = fn
        return self

    async def apply( self, handler: tornado.web.RequestHandler, *args ) -> None:
        self.fn(handler, *args)


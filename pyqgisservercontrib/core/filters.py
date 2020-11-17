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

import logging
import tornado.web

from typing import Coroutine, Callable, Awaitable

LOGGER = logging.getLogger('SRVLOG')


class ServerFilter:
    pass


class asyncfilter(ServerFilter):
    """ Decorator for asynchronous request filter

        Assume that the function return a  coroutine
    """

    def __init__(self, pri=0, uri=""):
        self.pri = pri
        self.uri = uri

    def __call__(self, fn: Callable[[tornado.web.RequestHandler], Awaitable[None]]) -> 'asyncfilter':
        self.fn = fn
        return self

    def apply( self, handler: tornado.web.RequestHandler ) -> Coroutine:
        return self.fn(handler)


class blockingfilter(ServerFilter):
    """ Decorator for synchronous request filter
    """

    def __init__(self, pri=0, uri=""):
        self.pri = pri
        self.uri = uri

    def __call__(self, fn):
        self.fn = fn
        return self

    async def apply( self, handler: tornado.web.RequestHandler ) -> None:
        self.fn(handler)


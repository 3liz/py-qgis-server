#
# Copyright 2019 3liz
# Author: David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


""" Define middleware filters

    Declare filters as

    @blockingfilter(uri="/ows/")
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

    policy_service.add_policy([myfilter1, myfilter2], pri=1000)
"""

import logging
import re

from tornado.httputil import HTTPServerRequest

from typing import (
    Union,
    Tuple,
    Callable, 
    Awaitable, 
    Optional,
)

LOGGER = logging.getLogger('SRVLOG')


class _FilterBase:

    def __init__(self, match: Optional[Union[str,re.Pattern]]=None, repl: Optional[str]=None):
        if isinstance(match, str):
            match = re.compile(match, re.IGNORECASE)
        self.pattern = match
        self.repl = repl
        self.match_args = []
        self.match_kwargs = {}

    def __str__(self) -> str:
        return f"_FilterBase<{hex(id(self))}>(match={self.pattern}, repl={self.repl})"
    def match(self, path: str) -> Tuple[bool,str]:
        """ Check uri against pattern
        """
        if self.pattern:
            match = self.pattern.match(path)
            if match:
                # match.groups() includes both named and
                # unnamed groups, we want to use either groups
                # or groupdict but not both. 
                if self.pattern.groupindex:
                    self.match_kwargs = match.groupdict()
                else:
                    self.match_args = match.groups() 
                if self.repl:
                    path = self.pattern.sub(self.repl, path, count=1)
                return True, path
        else:
            # Match everything
            return True, path

        return False, None

    def __call__(self, fn: Callable):
        self.fn = fn
        return self

    def apply(self, request: HTTPServerRequest) -> Optional[Awaitable]:
        self.fn(request, *self.match_args, **self.match_kwargs)
        return


class policy_filter(_FilterBase):
    """ Decorator for synchronous request filter
    """
    pass


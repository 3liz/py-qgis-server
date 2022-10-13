#
# Copyright 2018-2019 3liz
# Author: David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Qgis server handler
"""
import logging
from urllib.parse import urlencode

from .asynchandler import AsyncClientHandler

from typing import Any, Union, Dict

LOGGER = logging.getLogger('SRVLOG')


def _decode( b: Union[str,bytes] ) -> str:
    if not isinstance(b,str):
        return b.decode('utf-8')
    return b


class OwsHandler(AsyncClientHandler):

    def initialize(self, *args, getfeaturelimit: int=-1,  **kwargs) -> None:
        super().initialize(*args, **kwargs)
        self.getfeaturelimit = getfeaturelimit
        self.ogc_scheme = 'OWS'

    MONITOR_ARGUMENTS = (
        'MAP',
        'SERVICE',
        'REQUEST',
    )

    def get_monitor_params(self) -> Dict[str,Any]:
        """ Override
        """
        args = self.request.arguments
        params = { k:_decode(args.get(k,["__unknown__"])[0]) for k in self.MONITOR_ARGUMENTS }
        return params

    def prepare(self) -> None:
        super().prepare()
        # Replace query arguments to upper case: (it's ok for OWS)
        self.request.arguments = { k.upper():v for (k,v) in self.request.arguments.items() }

    def fix_getfeature(self, arguments: Dict) -> Dict:
        """ Take care of WFS/GetFeature limit

            Qgis does not set a default limit and unlimited
            request may cause issues
        """
        if self.getfeaturelimit > 0 \
                and arguments.get('SERVICE', b'').upper() == b'WFS' \
                and arguments.get('REQUEST', b'').lower() == b'getfeature':

            if arguments.get('VERSION', b'').startswith(b'2.'):
                key = 'COUNT'
            else:
                key = 'MAXFEATURES'

            limit = self.getfeaturelimit
            try:
                actual_limit = int(arguments.get(key,0))
                if actual_limit > 0:
                    limit =  min(limit, actual_limit)
            except ValueError:
                pass
            arguments[key] = str(limit).encode()

        return arguments

    def encode_arguments(self) -> str:
        arguments = {k:v[0] for k,v in self.request.arguments.items()}
        return '?'+urlencode(self.fix_getfeature(arguments))


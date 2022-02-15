# Copyright 2022 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


""" Cache Observer that send a BAN request
"""
import asyncio
import logging

from datetime import datetime
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from pyqgisserver.config import confservice

LOGGER=logging.getLogger('SRVLOG')

server_address = None
http_client    = None

def init() -> None:
    """
    """
    LOGGER.debug("*** Initializing ban observer")
    confservice.add_section('cache.observers:ban')

    global server_address, http_client
    server_address = confservice.get('cache.observers:ban','server_address')
    http_client = AsyncHTTPClient()

    LOGGER.debug("*** Ban observer: sending_request to %s", server_address)

async def ban( key: str) -> None:
    """ Ban key
    """
    LOGGER.info("Sending BAN request to %s", server_address)

    request = HTTPRequest(server_address, method='BAN', 
                          headers={ 'X-Map-Id': key },
                          user_agent="py-qgis-server; ban observer",
                          allow_nonstandard_methods=True)

    response = await http_client.fetch(request, raise_error=False)
    if response.code != 200:
        LOGGER.error("Ban server returned status code %s", response.code)
    


def observe(key: str, datetime: datetime, insert: bool) -> None:
    asyncio.create_task(ban(key))


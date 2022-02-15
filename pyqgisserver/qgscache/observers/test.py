# Copyright 2022 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


""" Cache Observer used for testing 
"""
import logging

from datetime import datetime

LOGGER=logging.getLogger('SRVLOG')

notify_data = {}

def init() -> None:
    pass

def observe(key: str, datetime: datetime, insert: bool) -> None:
    LOGGER.debug("*** TEST CACHE OBSERVER: Received update notification for %s %s [Inserted: %s]", key, datetime, insert)
    notify_data[key] = (key,datetime,insert)


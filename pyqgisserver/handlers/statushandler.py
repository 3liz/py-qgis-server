#
# Copyright 2018 3liz
# Author: David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import tornado
import logging

from .basehandler import BaseHandler
from ..version import __version__
from ..config import config_to_dict

LOGGER=logging.getLogger('SRVLOG')


class PingHandler(BaseHandler):
    def get(self):
        self.write_json({ 'status': 'ok' })


class StatusHandler(BaseHandler):
    def get(self):

        stats = self.application.stats

        try:
            from qgis.core import Qgis
            QGIS_VERSION="{} ({})".format(Qgis.QGIS_VERSION_INT,Qgis.QGIS_RELEASE_NAME)
        except Exception as e:
            LOGGER.error("Cannot get Qgis version %s", e)
            QGIS_VERSION="n/a"

        response = dict(tornado_ver=tornado.version,
                        version = __version__,
                        author="3Liz",
                        author_url="http://3liz.com",
                        qgis_version=QGIS_VERSION,
                        documentation="http://{}/doc/".format(self.request.host),
                        configuration=config_to_dict(),
                        env=dict(os.environ))
                        
        response.update(stats.json())

        self.write_json(response)

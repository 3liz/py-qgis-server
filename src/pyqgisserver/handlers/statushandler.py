#
# Copyright 2018 3liz
# Author: David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os

from typing import Dict

import tornado

from ..config import config_to_dict
from ..version import __version__
from .basehandler import BaseHandler

LOGGER = logging.getLogger('SRVLOG')


class PingHandler(BaseHandler):

    def set_default_headers(self) -> None:
        super().set_default_headers()
        # Disable cache because this is healtcheck requests
        self.set_header("Cache-control", "no-store")
        self.set_header("X-Server-Status", "ok")

    def get(self):
        self.write_json({'status': 'ok'})

    def head(self):
        pass


class StatusHandler(BaseHandler):

    def get(self):

        path = self.request.path.rstrip('/')

        if path == '/status/config':
            response = config_to_dict()
        elif path == '/status/env':
            response = dict(os.environ)
        elif path == '/status/stats':
            response = self.application.stats
        elif path == '/status/versions':
            response = self.get_versions()
        else:
            response = self.get_versions()
            req = self.request

            def _link(path: str, title: str, rel: str) -> Dict[str, str]:
                return {
                    'href': f"{req.protocol}://{req.host}{path}",
                    'rel': rel,
                    'title': title,
                    'type': "application/json",
                }

            response.update(links=[
                _link("/status/config", "Server configuration", "status"),
                _link("/status/env", "Execution environment", "status"),
                _link("/status/versions", "Versions", "status"),
                _link("/status/", "Server status", "self"),
            ])

        self.write_json(response)

    def get_versions(self) -> Dict[str, str]:
        try:
            from qgis.core import Qgis
            QGIS_VERSION = str(Qgis.QGIS_VERSION_INT)
            QGIS_RELEASE = Qgis.QGIS_RELEASE_NAME
        except Exception as e:
            LOGGER.error("Cannot get Qgis version %s", e)
            QGIS_VERSION = "n/a"
            QGIS_RELEASE = "n/a"

        return dict(
            tornado_ver=tornado.version,
            version=__version__,
            qgis_version=QGIS_VERSION,
            qgis_release=QGIS_RELEASE,
        )

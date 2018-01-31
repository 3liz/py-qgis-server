# -*- encoding=utf-8 -*-

import tornado
import logging

from .basehandler import BaseHandler
from ..version import __version__
from ..config import config_to_dict

LOGGER=logging.getLogger('QGSRV')


class RootHandler(BaseHandler):
    def get(self):
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
                        config=config_to_dict(),
                        qgis_version=QGIS_VERSION,
                        documentation="http://{}/doc/".format(self.request.host))

        self.write_json(response)

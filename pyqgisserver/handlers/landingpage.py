#
# Copyright 2018 3liz
# Author: David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from ..config import confservice
from ..version import __version__
from .basehandler import BaseHandler

LOGGER = logging.getLogger('SRVLOG')


class LandingPage(BaseHandler):

    def initialize(self):
        super().initialize()

        self._metadata = confservice['metadata']

    def get(self):
        """
        """
        req = self.request
        self._server = f"{req.protocol}://{req.host}"
        doc = {}
        doc.update(
            servers=[{
                'url': self._server,
            }],
            info=self.service_infos(),
            externalDocs=self.external_doc(),
            paths={},
        )
        self.write_json(doc)

    def service_infos(self):
        m = self._metadata.get
        doc = {
            'title': m('title'),
            'description': m('description'),
            'termsOfService': m('terms_of_service'),
            'contact': {
                'name': m('contact_name'),
                'url': m('contact_url'),
                'email': m('contact_email'),
            },
            'licence': {
                'name': m('licence_name'),
                'url': m('licence_url'),
            },
            'version': __version__,
        }

        doc.update(self.qgis_version_info())
        return doc

    def qgis_version_info(self):
        try:
            from qgis.core import Qgis
            qgis_version = Qgis.QGIS_VERSION_INT
            qgis_release = Qgis.QGIS_RELEASE_NAME
        except ImportError:
            LOGGER.critical("Failed to import Qgis module !")
            qgis_version = qgis_release = 'n/a'

        return (
            ('x-qgis-version', qgis_version),
            ('x-qgis-release', qgis_release),
        )

    def external_doc(self):
        return {
            'description': self._metadata['external_doc_description'],
            'url': self._metadata['external_doc_url'],
        }

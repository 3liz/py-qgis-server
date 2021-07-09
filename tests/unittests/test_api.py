"""
    Test server disponibility
"""

import pytest

from pyqgisserver.tests import HTTPTestCase
from urllib.parse import urlparse

from qgis.core import Qgis

@pytest.mark.skipif(Qgis.QGIS_VERSION_INT < 32000, reason="Requires qgis >= 3.20")
class Tests(HTTPTestCase):

    def test_landing_page(self):
        """ Test landing_page
        """
        rv = self.client.get( '', path="/ows/catalog/" )
        assert rv.status_code == 200


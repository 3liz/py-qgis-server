"""
    Test server disponibility
"""


import pytest

from pyqgisserver.tests import HTTPTestCase


class Tests(HTTPTestCase):

    # XXX This test takes an insane amount with QGIS >= 3.26+
    # of time on gitlab CI, this need to be investigated
    # See https://github.com/qgis/QGIS/pull/49476
    @pytest.mark.skip(reason="Wait to fix project loading in landing page")
    def test_landing_page(self):
        """ Test landing_page
        """
        rv = self.client.get('', path="/ows/catalog/")
        assert rv.status_code == 200

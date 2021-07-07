"""
    Test server disponibility
"""

from pyqgisserver.tests import HTTPTestCase
from urllib.parse import urlparse

class Tests(HTTPTestCase):

    def test_landing_page(self):
        """ Test landing_page
        """
        rv = self.client.get( '', path="/ows/catalog/" )
        assert rv.status_code == 200


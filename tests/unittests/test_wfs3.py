"""
    Test server disponibility
"""

from qgis.core import Qgis

from pyqgisserver.tests import HTTPTestCase

ns = {"wms": "http://www.opengis.net/wms"}

xlink = "{http://www.w3.org/1999/xlink}"

if Qgis.versionInt() >= 40000:
    WFS3_ROOT = "/ogcapi"
else:
    WFS3_ROOT = "/wfs3"


class Tests(HTTPTestCase):

    def test_wfs3_base(self):
        """ Test wfs3
        """
        rv = self.client.get('', path=f"{WFS3_ROOT}/?MAP=france_parts.qgs")
        assert rv.status_code == 200
        assert rv.headers['Content-Type'].find('application/json') >= 0

        rv = self.client.get('', path=f"{WFS3_ROOT}.json?MAP=france_parts.qgs")
        assert rv.status_code == 200
        assert rv.headers['Content-Type'].find('application/json') >= 0

        data = rv.json()
        assert data['links'][0]['href'].find(f"{WFS3_ROOT}.json?MAP=france_parts")

        rv = self.client.get('', path=f"{WFS3_ROOT}.html?MAP=france_parts.qgs")
        assert rv.status_code == 200
        assert rv.headers['Content-Type'].find('text/html') >= 0

    def test_wfs3_collections(self):
        """ Test wfs3
        """
        rv = self.client.get('', path=f"{WFS3_ROOT}/collections/?MAP=france_parts.qgs")
        assert rv.status_code == 200
        assert rv.headers['Content-Type'].find('application/json') >= 0

        rv = self.client.get('', path=f"{WFS3_ROOT}/collections.json?MAP=france_parts.qgs")
        assert rv.status_code == 200
        assert rv.headers['Content-Type'].find('application/json') >= 0

        rv = self.client.get('', path=f"{WFS3_ROOT}/collections.html?MAP=france_parts.qgs")
        assert rv.status_code == 200
        assert rv.headers['Content-Type'].find('text/html') >= 0

    def test_wfs3_should_return_404(self):
        """ Test wfs3
        """
        rv = self.client.get('', path=f"{WFS3_ROOT}/foobar/?MAP=france_parts.qgs")
        assert rv.status_code == 404

    def test_wfs3_limit_parameter(self):
        """ Test parameters in wfs3
        """
        rv = self.client.get('', path=f"{WFS3_ROOT}/collections/france_parts/items.json?MAP=france_parts&limit=1")
        assert rv.status_code == 200
        data = rv.json()
        assert len(data['features']) == 1

        rv = self.client.get('', path=f"{WFS3_ROOT}/collections/france_parts/items.json?MAP=france_parts&limit=2")
        assert rv.status_code == 200
        data = rv.json()
        assert len(data['features']) == 2

"""
    Test server disponibility
"""
from pyqgisserver.tests import HTTPTestCase
from urllib.parse import urlencode

ns = { "wms": "http://www.opengis.net/wms" }
xlink = "{http://www.w3.org/1999/xlink}"

class Tests(HTTPTestCase):

    def test_project_ok(self):
        """ Test getcapabilities hrefs
        """
        rv = self.client.get( "?MAP=project_simple&SERVICE=WMS&request=GetCapabilities" )
        assert rv.status_code == 200
        assert rv.headers['Content-Type'] == 'text/xml; charset=utf-8'

        elem = rv.xml.findall(".//wms:Layer/wms:Layer", ns)
        assert len(elem) == 2

    def test_project_with_excluded(self):
        """ Test getcapabilities hrefs
        """
        rv = self.client.get( "?MAP=project_simple_with_excluded&SERVICE=WMS&request=GetCapabilities" )
        assert rv.status_code == 200
        assert rv.headers['Content-Type'] == 'text/xml; charset=utf-8'

        elem = rv.xml.findall(".//wms:Layer/wms:Layer", ns)
        assert len(elem) == 1

    def test_project_with_invalid(self):
        """ Test getcapabilities hrefs
        """
        rv = self.client.get( "?MAP=project_simple_with_invalid&SERVICE=WMS&request=GetCapabilities" )
        assert rv.status_code == 422

    def test_project_with_invalid_excluded(self):
        """ Test getcapabilities hrefs
        """
        rv = self.client.get( "?MAP=project_simple_with_invalid_excluded&SERVICE=WMS&request=GetCapabilities" )
        assert rv.status_code == 200
        assert rv.headers['Content-Type'] == 'text/xml; charset=utf-8'

        elem = rv.xml.findall(".//wms:Layer/wms:Layer", ns)
        assert len(elem) == 1







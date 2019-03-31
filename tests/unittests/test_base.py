"""
    Test server disponibility
"""
from pyqgisserver.tests import HTTPTestCase

class Tests(HTTPTestCase):

    def test_root_request(self):
        """ Test response from root path
        """
        rv = self.client.get('',path='/')
        assert rv.status_code == 200

    def test_wms_getcapabilitiesatlas(self):
        """
        """
        rv = self.client.get("?MAP=france_parts.qgs&SERVICE=WMS&request=GetCapabilitiesAtlas")
        assert rv.status_code == 200
        assert rv.headers['Content-Type'] == 'text/xml; charset=utf-8'

    def test_wms_getcaps(self):
        """
        """
        rv = self.client.get("?MAP=france_parts.qgs&SERVICE=WMS&request=GetCapabilities")
        assert rv.status_code == 200
        assert rv.headers['Content-Type'] == 'text/xml; charset=utf-8'

    def test_wfs_getcaps(self):
        """ 
        """
        rv = self.client.get("?MAP=france_parts.qgs&SERVICE=WFS&request=GetCapabilities")
        assert rv.status_code == 200
        assert rv.headers['Content-Type'] == 'text/xml; charset=utf-8'

    def test_wcs_getcaps(self):
        """
        """
        rv = self.client.get("?MAP=france_parts.qgs&SERVICE=WCS&request=GetCapabilities")
        assert rv.status_code == 200
        assert rv.headers['Content-Type'] == 'text/xml; charset=utf-8'

    def test_map_not_found_return_404(self):
        """ Test that non existent map return 404
        """
        rv = self.client.get("?MAP=i_do_not_exists.qgs&SERVICE=WFS&request=GetCapabilities")
        assert rv.status_code == 404

    def test_protocol_resolution(self):
        """ Test that custom protocol is correctly resolved
        """
        rv = self.client.get("?MAP=test:france_parts.qgs&SERVICE=WFS&request=GetCapabilities")
        assert rv.status_code == 200

    def test_unknown_protocol_is_404(self):
        """ Test that custom protocol is correctly resolved
        """
        rv = self.client.get("?MAP=fail:france_parts.qgs&SERVICE=WFS&request=GetCapabilities")
        assert rv.status_code == 404



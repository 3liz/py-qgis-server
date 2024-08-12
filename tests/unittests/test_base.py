"""
    Test server disponibility
"""
from pyqgisserver.tests import HTTPTestCase


class Tests(HTTPTestCase):

    def test_status_request(self):
        """ Test response from root path
        """
        rv = self.client.get('', path='/status/')
        assert rv.status_code == 200

    def test_wms_getcapabilitiesatlas(self):
        """
        """
        rv = self.client.get("?MAP=france_parts.qgs&SERVICE=WMS&request=GetCapabilitiesAtlas")
        assert rv.status_code == 501
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

    def test_open_with_basename(self):
        """ Test that custom protocol is correctly resolved
        """
        rv = self.client.get("?MAP=france_parts&SERVICE=WFS&request=GetCapabilities")
        assert rv.status_code == 200

    def test_open_qgz(self):
        """ Test that custom protocol is correctly resolved
        """
        rv = self.client.get("?MAP=france_parts_qgz&SERVICE=WFS&request=GetCapabilities")
        assert rv.status_code == 200

    def test_ows_service_nomap_return_400(self):
        """ Test that a ows request without Map  return 400
        """
        rv = self.client.get("?Service=WMS&request=GetCapabilities")
        assert rv.status_code == 400

    def test_allowed_headers(self):
        """ Test allowed headers as defined in configuration

            Use the 'headers' test plugin
        """
        headers = {
            'X-Qgis-Test': 'This is Qgis header',
            'X-Lizmap-Test': 'This is Lizmap header',
        }

        rv = self.client.get("?MAP=france_parts&SERVICE=WFS&request=GetCapabilities",
                             headers=headers)
        assert rv.status_code == 200
        assert rv.headers['X-Qgis-Header'] == headers['X-Qgis-Test']
        assert rv.headers['X-Lizmap-Header'] == headers['X-Lizmap-Test']

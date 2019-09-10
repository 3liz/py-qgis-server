"""
    Test profiles
"""
from pyqgisserver.tests import HTTPTestCase

class Tests(HTTPTestCase):

    def test_profile_request(self):
        """ Test response from root path
        """
        uri = ('/ows/p/wmsonly/?bbox=-621646.696284,5795001.359349,205707.697759,6354520.406319&crs=EPSG:3857'
               '&dpi=96&exceptions=application/vnd.ogc.se_inimage&format=image/png&height=915'
               '&layers=france_parts&request=GetMap'
               '&service=WMS&styles=default&transparent=TRUE&version=1.3.0&width=1353')

        rv = self.client.get(uri,path='')
        assert rv.status_code == 200

    def test_profile_return_403(self):
        """ Test unauthorized WFS return a 403 response
        """
        uri = ('/ows/p/wmsonly/?exceptions=application/vnd.ogc.se_inimage'
               '&service=WFS&request=GetCapabilities')

        rv = self.client.get(uri,path='')
        assert rv.status_code == 403

    def test_ip_ok(self):
        """ Test authorized ip return a 200 response
        """
        uri = '/ows/p/rejectips/?service=WMS&request=GetCapabilities'
        rv = self.client.get(uri,  headers={ 'X-Forwarded-For': '192.168.2.1' }, path='')
        assert rv.status_code == 200

    def test_ip_rejected_return_403(self):
        """ Test unauthorized WFS return a 403 response
        """
        uri = '/ows/p/rejectips/?service=WMS&request=GetCapabilities'

        rv = self.client.get(uri, headers={ 'X-Forwarded-For': '192.168.3.1' }, path='')
        assert rv.status_code == 403

    def test_profile_with_path(self):
        """ Test response from root path
        """
        uri = ('/ows/p/wms/testpath?bbox=-621646.696284,5795001.359349,205707.697759,6354520.406319&crs=EPSG:3857'
               '&dpi=96&exceptions=application/vnd.ogc.se_inimage&format=image/png&height=915'
               '&layers=france_parts&request=GetMap'
               '&service=WMS&styles=default&transparent=TRUE&version=1.3.0&width=1353')

        rv = self.client.get(uri,path='')
        assert rv.status_code == 200

    def test_wfs_profile(self):
        """ Test profile located in subdir
        """
        uri = ('/ows/p/wfsonly/')

        rv = self.client.get(uri,path='')
        assert rv.status_code == 200




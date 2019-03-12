"""
    Test server disponibility
"""
from pyqgisserver.tests import HTTPTestCase
from urllib.parse import urlencode


class Tests(HTTPTestCase):

    def test_getmap_request(self):
        """ Test response from root path
        """
        query = ('?bbox=-621646.696284,5795001.359349,205707.697759,6354520.406319&crs=EPSG:3857'
               '&dpi=96&exceptions=application/vnd.ogc.se_inimage&format=image/png&height=915'
               '&layers=france_parts&map=france_parts.qgs&request=GetMap'
               '&service=WMS&styles=default&transparent=TRUE&version=1.3.0&width=1353')

        rv = self.client.get(query)
        assert rv.status_code == 200

    def test_getmap_post_request(self):
        """ Test response from root path
        """
        arguments = { 
          'bbox':'-621646.696284,5795001.359349,205707.697759,6354520.406319',
          'crs':'EPSG:3857',
          'dpi':'96',
          'exceptions':'application/vnd.ogc.se_inimage',
          'format':'image/png',
          'height':'915',
          'layers':'france_parts',
          'map':'france_parts.qgs',
          'request':'GetMap',
          'service':'WMS',
          'styles':'default',
          'transparent':'TRUE',
          'version':'1.3.0',
          'width':'1353' }

        rv = self.client.post(urlencode(arguments))
        assert rv.status_code == 200



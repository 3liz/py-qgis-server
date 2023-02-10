"""
    Test server disponibility
"""

from pyqgisserver.tests import HTTPTestCase
from urllib.parse import urlparse

ns = { 
       "wfs": "http://www.opengis.net/wfs",
       "qgs": "http://www.qgis.org/gml",
       "xsd": "http://www.w3.org/2001/XMLSchema",
     }

xlink = "{http://www.w3.org/1999/xlink}"

class Tests(HTTPTestCase):

    def test_wfs_describe_feature_type(self):
        """ Test DescribeFeatureType
        """
        rv = self.client.get( "?MAP=france_parts.qgs&SERVICE=WFS&request=DescribeFeatureType&VERSION=1.0.0"
                               "&TypeName=france_parts_bordure")

        assert rv.status_code == 200
        assert rv.headers['Content-Type'] == 'text/xml; charset=utf-8'

        elem = rv.xml.findall(".//xsd:complexContent", ns)
        assert len(elem) > 0


    def test_wfs_getfeature(self):
        """ Test DescribeFeatureType
        """
        rv = self.client.get( "?MAP=france_parts.qgs&SERVICE=WFS&request=GetFeature&VERSION=1.0.0"
                               "&TypeName=france_parts_bordure")

        assert rv.status_code == 200

        content_type = rv.headers['Content-Type']
        assert "text/xml" in content_type
        assert "subtype=gml" in content_type

        elem = rv.xml.findall(".//qgs:france_parts_bordure", ns)
        assert len(elem) > 0


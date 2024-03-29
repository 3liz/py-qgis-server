"""
    Test Getfeature requests
"""
import pytest

from pyqgisserver.tests import HTTPTestCase, NAMESPACES
from pyqgisserver.config import confservice

from urllib.parse import urlparse
from qgis.core import Qgis

xlink = "{http://www.w3.org/1999/xlink}"

class Tests1(HTTPTestCase):

    def get_app(self) -> None:
        confservice.set('server', 'getfeaturelimit', "-1")
        return super().get_app()

    def test_getfeature_nolimit(self):
        """ Test getcapabilities hrefs
        """
        rv = self.client.get( "?MAP=france_parts.qgs&SERVICE=WFS&REQUEST=GetFeature&VERSION=1.0.0" 
                              "&TYPENAME=france_parts_bordure")
        assert rv.status_code == 200
        assert rv.headers['Content-Type'].startswith('text/xml;')

        features = rv.xml.findall(".//gml:featureMember", NAMESPACES)
        assert len(features) == 4


class Tests2(HTTPTestCase):

    def get_app(self) -> None:
        confservice.set('server', 'getfeaturelimit', "2")
        return super().get_app()

    def test_getfeature_limit(self):
        """ Test getcapabilities hrefs
        """

        assert confservice.getint('server', 'getfeaturelimit') == 2

        rv = self.client.get( "?MAP=france_parts.qgs&SERVICE=WFS&REQUEST=GetFeature&VERSION=1.0.0" 
                              "&TYPENAME=france_parts_bordure")
        assert rv.status_code == 200
        assert rv.headers['Content-Type'].startswith('text/xml;')

        features = rv.xml.findall(".//gml:featureMember", NAMESPACES)
        assert len(features) == 2

    def test_getfeature_limit_ok(self):
        """ Test getcapabilities hrefs
        """

        assert confservice.getint('server', 'getfeaturelimit') == 2

        rv = self.client.get( "?MAP=france_parts.qgs&SERVICE=WFS&REQUEST=GetFeature&VERSION=1.0.0" 
                              "&TYPENAME=france_parts_bordure&MAXFEATURES=1")
        assert rv.status_code == 200
        assert rv.headers['Content-Type'].startswith('text/xml;')

        features = rv.xml.findall(".//gml:featureMember", NAMESPACES)
        assert len(features) == 1

    def test_getfeature_limit_not_ok(self):
        """ Test getcapabilities hrefs
        """
        assert confservice.getint('server', 'getfeaturelimit') == 2

        rv = self.client.get( "?MAP=france_parts.qgs&SERVICE=WFS&REQUEST=GetFeature&VERSION=1.0.0" 
                              "&TYPENAME=france_parts_bordure&MAXFEATURES=3")
        assert rv.status_code == 200
        assert rv.headers['Content-Type'].startswith('text/xml;')

        features = rv.xml.findall(".//gml:featureMember", NAMESPACES)
        assert len(features) == 2


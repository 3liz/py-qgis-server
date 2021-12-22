"""
    Test server disponibility
"""
import pytest

from pyqgisserver.tests import HTTPTestCase
from urllib.parse import urlparse
from qgis.core import Qgis

ns = { "wms": "http://www.opengis.net/wms" }

xlink = "{http://www.w3.org/1999/xlink}"

class Tests(HTTPTestCase):

    def test_wms_getcapabilities_hrefs(self):
        """ Test getcapabilities hrefs
        """
        rv = self.client.get( "?MAP=france_parts.qgs&SERVICE=WMS&request=GetCapabilities" )
        assert rv.status_code == 200
        assert rv.headers['Content-Type'] == 'text/xml; charset=utf-8'

        elem = rv.xml.findall(".//wms:OnlineResource", ns)
        assert len(elem) > 0
        
        href = urlparse(elem[0].get(xlink+'href'))
        self.logger.info(href.geturl())

    def test_forwarded_url(self):
        """ Test proxy location
        """
        urlref = urlparse('https://my.proxy.loc:9999/anywhere/')
        rv = self.client.get("?MAP=france_parts.qgs&SERVICE=WMS&request=GetCapabilities", 
                             headers={ 'X-Forwarded-Url': urlref.geturl() } )

        assert rv.status_code == 200
        assert rv.headers['Content-Type'] == 'text/xml; charset=utf-8'

        elem = rv.xml.findall(".//wms:OnlineResource", ns)
        assert len(elem) > 0

        href = urlparse(elem[0].get(xlink+'href'))
        assert href.scheme   == urlref.scheme
        assert href.hostname == urlref.hostname
        assert href.path     == urlref.path

    def test_wmsurl(self):
        """ Test proxy location is overrided by WMSUrl
        """
        from pyqgisserver.config import confservice

        proxy_url = 'https://my.proxy.loc:9999/anywhere'
        rv = self.client.get("?MAP=france_parts_wmsurl.qgs&SERVICE=WMS&request=GetCapabilities", 
                             headers={ 'X-Forwarded-Url': proxy_url } )

        assert rv.status_code == 200
        assert rv.headers['Content-Type'] == 'text/xml; charset=utf-8'

        elem = rv.xml.findall(".//wms:OnlineResource", ns)
        assert len(elem) > 0

        if confservice.getboolean('projects.cache', 'disable_owsurls'):
            urlref = urlparse( proxy_url )
        else:
            urlref = urlparse( "http://test.proxy.loc/whatever/" )

        href = urlparse(elem[0].get(xlink+'href'))
        assert href.scheme   == urlref.scheme
        assert href.hostname == urlref.hostname
        assert href.path     == urlref.path

    def test_cors_options(self):
        """ Test CORS options
        """
        rv = self.client.options( headers={ 'Origin': 'my.home' } )

        assert rv.status_code == 200
        assert 'Allow' in rv.headers
        assert 'Access-Control-Allow-Methods' in rv.headers
        assert 'Access-Control-Allow-Origin'  in rv.headers

    def test_ows_request_with_cors(self):
        """ Test getcapabilities hrefs
        """
        rv = self.client.get( "?MAP=france_parts.qgs&SERVICE=WMS&request=GetCapabilities",
                headers={ 'Origin': 'my.home' })

        assert rv.status_code == 200
        assert rv.headers['Content-Type'] == 'text/xml; charset=utf-8'
        assert 'Access-Control-Allow-Origin'  in rv.headers

    def test_lower_case_query_params(self):
        """ Test that we support lower case query param
        """
        rv = self.client.get( "?map=france_parts.qgs&SERVICE=WMS&request=GetCapabilities" )
        assert rv.status_code == 200    

    @pytest.mark.skipif(Qgis.QGIS_VERSION_INT <= 32000, reason="Requires qgis >= 3.20")
    def test_qgis_urls(self):
        """ Test X-Qgis-* urls 
            see https://github.com/qgis/QGIS/pull/41333
        """
        urlref = urlparse('https://my.proxy.loc:9999/anywhere/')
        rv = self.client.get("?MAP=france_parts.qgs&SERVICE=WMS&request=GetCapabilities", 
                             headers={ 'X-Qgis-Service-Url': urlref.geturl() } )

        assert rv.status_code == 200
        assert rv.headers['Content-Type'] == 'text/xml; charset=utf-8'

        elem = rv.xml.findall(".//wms:OnlineResource", ns)
        assert len(elem) > 0

        href = urlparse(elem[0].get(xlink+'href'))
        assert href.scheme   == urlref.scheme
        assert href.hostname == urlref.hostname
        assert href.path     == urlref.path

    def test_getcapabilities_etag(self):
        """ Test getcapabilities etag
        """
        rv = self.client.get( "?MAP=france_parts.qgs&SERVICE=WFS&request=GetCapabilities" )
        assert rv.status_code == 200
        assert rv.headers['Content-Type'] == 'text/xml; charset=utf-8'

        etag = rv.headers.get('Etag')
        assert etag is not None

        # Redo request with etag
        rv = self.client.get( "?MAP=france_parts.qgs&SERVICE=WFS&request=GetCapabilities",
                              headers={ 'If-None-Match': etag })
        assert rv.status_code == 304




"""
    Test server disponibility
"""

from pyqgisserver.tests import HTTPTestCase
from urllib.parse import urlparse

ns = { "wms": "http://www.opengis.net/wms" }

xlink = "{http://www.w3.org/1999/xlink}"

class Tests(HTTPTestCase):

    def test_wms_getcapabilities_hrefs(self):
        """ Test getcapabilities hrefs
        """
        rv = self.client.get( "?MAP=france_parts.qgs&SERVICE=WMS&request=GetCapabilities" )
        assert rv.status_code == 200
        assert rv.headers['content-type'] == 'text/xml; charset=utf-8'

        elem = rv.xml.findall(".//wms:OnlineResource", ns)
        assert len(elem) > 0
        
        href = urlparse(elem[0].get(xlink+'href'))
        self.logger.info(href.geturl())

    def test_proxy_location(self):
        """ Test proxy location
        """
        urlref = urlparse('https://my.proxy.loc:9999/anywhere')
        rv = self.client.get("?MAP=france_parts.qgs&SERVICE=WMS&request=GetCapabilities", 
                             headers={ 'X-Proxy-Location': urlref.geturl() } )

        assert rv.status_code == 200
        assert rv.headers['content-type'] == 'text/xml; charset=utf-8'

        elem = rv.xml.findall(".//wms:OnlineResource", ns)
        assert len(elem) > 0

        href = urlparse(elem[0].get(xlink+'href'))
        assert href.scheme   == urlref.scheme
        assert href.hostname == urlref.hostname
        assert href.path     == urlref.path
        
    def test_lower_case_query_params(self):
        """ Test that we support lower case query param
        """
        rv = self.client.get( "?map=france_parts.qgs&SERVICE=WMS&request=GetCapabilities" )
        assert rv.status_code == 200    



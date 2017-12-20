"""
    Test server disponibility
"""
import requests
import lxml.etree as etree

from urllib.parse import urlparse

ns = { "wms": "http://www.opengis.net/wms" }

xlink = "{http://www.w3.org/1999/xlink}"

def test_wms_getcapabilities_hrefs( host ):
    """ Test getcapabilities hrefs
    """
    urlref = urlparse( "http://{}/ows/?MAP=france_parts.qgs&SERVICE=WMS&request=GetCapabilities".format( host ) )
    rv = requests.get( urlref.geturl() )
    assert rv.status_code == 200
    assert rv.headers['content-type'] == 'text/xml; charset=utf-8'

    urlref = urlparse("http://{}/ows/".format( host ))

    xml  = etree.fromstring(rv.content)

    elem = xml.findall(".//wms:OnlineResource", ns)
    assert len(elem) > 0

    href = urlparse(elem[0].get(xlink+'href'))
    assert href.scheme   == urlref.scheme
    assert href.hostname == urlref.hostname
    assert href.path     == urlref.path


def test_proxy_location( host ):
    """ Test proxy location
    """
    urlref = urlparse('https://my.proxy.loc:9999/anywhere')
    rv = requests.get("http://{}/ows/?MAP=france_parts.qgs&SERVICE=WMS&request=GetCapabilities".format( host ) , 
                      headers={ 'X-Proxy-Location': urlref.geturl() } )

    assert rv.status_code == 200
    assert rv.headers['content-type'] == 'text/xml; charset=utf-8'

    xml = etree.fromstring(rv.content)

    elem = xml.findall(".//wms:OnlineResource", ns)
    assert len(elem) > 0

    href = urlparse(elem[0].get(xlink+'href'))
    assert href.scheme   == urlref.scheme
    assert href.hostname == urlref.hostname
    assert href.path     == urlref.path
    
def test_lower_case_query_params( host ):
    """ Test that we support lower case query param
    """
    urlref = "http://{}/ows/?map=france_parts.qgs&SERVICE=WMS&request=GetCapabilities".format( host )
    rv = requests.get( urlref )
    assert rv.status_code == 200    

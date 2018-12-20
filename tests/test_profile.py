"""
    Test server disponibility
"""
import requests


def test_profile_request( host ):
    """ Test response from root path
    """
    url = ('/ows/p/foobar/?bbox=-621646.696284,5795001.359349,205707.697759,6354520.406319&crs=EPSG:3857'
           '&dpi=96&exceptions=application/vnd.ogc.se_inimage&format=image/png&height=915'
           '&layers=france_parts&request=GetMap'
           '&service=WMS&styles=default&transparent=TRUE&version=1.3.0&width=1353')

    rv = requests.get("http://{}{}".format( host, url ))
    assert rv.status_code == 200

def test_profile_return_403( host ):
    """ Test unauthorized WFS return a 403 response
    """
    url = ('/ows/p/foobar/?exceptions=application/vnd.ogc.se_inimage&format=image/'
           '&service=WFS&request=GetCapabilities')

    rv = requests.get("http://{}{}".format( host, url ))
    assert rv.status_code == 403




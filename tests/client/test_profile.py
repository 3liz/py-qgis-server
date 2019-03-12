"""
    Test server disponibility
"""
import requests


def test_profile_request( host ):
    """ Test response from root path
    """
    url = ('/ows/p/wmsonly/?bbox=-621646.696284,5795001.359349,205707.697759,6354520.406319&crs=EPSG:3857'
           '&dpi=96&exceptions=application/vnd.ogc.se_inimage&format=image/png&height=915'
           '&layers=france_parts&request=GetMap'
           '&service=WMS&styles=default&transparent=TRUE&version=1.3.0&width=1353')

    rv = requests.get("http://{}{}".format( host, url ))
    assert rv.status_code == 200


def test_profile_return_403( host ):
    """ Test unauthorized WFS return a 403 response
    """
    url = ('/ows/p/wmsonly/?exceptions=application/vnd.ogc.se_inimage'
           '&service=WFS&request=GetCapabilities')

    rv = requests.get("http://{}{}".format( host, url ))
    assert rv.status_code == 403


def test_ip_ok( host ):
    """ Test authorized ip return a 200 response
    """
    url = ('/ows/p/rejectips/?service=WMS&request=GetCapabilities')

    rv = requests.get("http://{}{}".format( host, url ),  headers={ 'X-Forwarded-For': '192.168.2.1' })
    assert rv.status_code == 200



def test_ip_rejected_return_403( host ):
    """ Test unauthorized WFS return a 403 response
    """
    url = ('/ows/p/rejectips/?service=WMS&request=GetCapabilities')

    rv = requests.get("http://{}{}".format( host, url ), headers={ 'X-Forwarded-For': '192.168.3.1' })
    assert rv.status_code == 403


def test_profile_with_path( host ):
    """ Test response from root path
    """
    url = ('/ows/p/wms/testpath?bbox=-621646.696284,5795001.359349,205707.697759,6354520.406319&crs=EPSG:3857'
           '&dpi=96&exceptions=application/vnd.ogc.se_inimage&format=image/png&height=915'
           '&layers=france_parts&request=GetMap'
           '&service=WMS&styles=default&transparent=TRUE&version=1.3.0&width=1353')

    rv = requests.get("http://{}{}".format( host, url ))
    assert rv.status_code == 200




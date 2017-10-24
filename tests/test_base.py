"""
    Test server disponibility
"""
import requests


def test_root_request( host ):
    """ Test response from root path
    """
    rv = requests.get("http://{}/".format( host ))
    assert rv.status_code == 200


def test_wms_getcaps( host ):
    """ Test 
    """
    rv = requests.get("http://{}/wms?MAP=france_parts.qgs&SERVICE=WMS&request=GetCapabilities".format( host ))
    assert rv.status_code == 200
    assert rv.headers['content-type'] == 'text/xml; charset=utf-8'


def test_wfs_getcaps( host ):
    """ Test 
    """
    rv = requests.get("http://{}/wms?MAP=france_parts.qgs&SERVICE=WFS&request=GetCapabilities".format( host ))
    assert rv.status_code == 200
    assert rv.headers['content-type'] == 'text/xml; charset=utf-8'


def test_wcs_getcaps( host ):
    """ Test 
    """
    rv = requests.get("http://{}/wms?MAP=france_parts.qgs&SERVICE=WCS&request=GetCapabilities".format( host ))
    assert rv.status_code == 200
    assert rv.headers['content-type'] == 'text/xml; charset=utf-8'




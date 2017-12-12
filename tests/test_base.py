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
    rv = requests.get("http://{}/ows/?MAP=france_parts.qgs&SERVICE=WMS&request=GetCapabilities".format( host ))
    assert rv.status_code == 200
    assert rv.headers['content-type'] == 'text/xml; charset=utf-8'


def test_wfs_getcaps( host ):
    """ Test 
    """
    rv = requests.get("http://{}/ows/?MAP=france_parts.qgs&SERVICE=WFS&request=GetCapabilities".format( host ))
    assert rv.status_code == 200
    assert rv.headers['content-type'] == 'text/xml; charset=utf-8'


def test_wcs_getcaps( host ):
    """ Test 
    """
    rv = requests.get("http://{}/ows/?MAP=france_parts.qgs&SERVICE=WCS&request=GetCapabilities".format( host ))
    assert rv.status_code == 200
    assert rv.headers['content-type'] == 'text/xml; charset=utf-8'

def test_map_not_found_return_404( host ):
    """ Test that non existent map return 404
    """
    rv = requests.get("http://{}/ows/?MAP=i_do_not_exists.qgs&SERVICE=WFS&request=GetCapabilities".format( host ))
    assert rv.status_code == 404

def test_protocol_resolution( host ):
    """ Test that custom protocol is correctly resolved
    """
    rv = requests.get("http://{}/ows/?MAP=test:france_parts.qgs&SERVICE=WFS&request=GetCapabilities".format( host ))
    assert rv.status_code == 200

def test_unknown_protocol_is_404( host ):
    """ Test that custom protocol is correctly resolved
    """
    rv = requests.get("http://{}/ows/?MAP=fail:france_parts.qgs&SERVICE=WFS&request=GetCapabilities".format( host ))
    assert rv.status_code == 404



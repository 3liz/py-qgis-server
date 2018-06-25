"""
    Test server disponibility
"""
import requests


def test_getmap_request( host ):
    """ Test response from root path
    """
    url = ('/ows/?bbox=-621646.696284,5795001.359349,205707.697759,6354520.406319&crs=EPSG:3857'
           '&dpi=96&exceptions=application/vnd.ogc.se_inimage&format=image/png&height=915'
           '&layers=france_parts&map=france_parts.qgs&request=GetMap'
           '&service=WMS&styles=default&transparent=TRUE&version=1.3.0&width=1353')

    rv = requests.get("http://{}{}".format( host, url ))
    assert rv.status_code == 200

def test_getmap_post_request( host ):
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

    rv = requests.post("http://{}/ows/".format( host ), data=arguments)
    assert rv.status_code == 200



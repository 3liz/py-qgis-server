"""
    Test server disponibility
"""
import pytest

from pyqgisserver.tests import HTTPTestCase

ns = {"wms": "http://www.opengis.net/wms"}

xlink = "{http://www.w3.org/1999/xlink}"


class Tests(HTTPTestCase):

    @pytest.mark.skip(reason="This test randomly fail, need to investigate")
    def test_wfs_segfault(self):
        """ Test that wfs request return a result
            see https://projects.3liz.org/infra-v3/py-qgis-server/issues/3
        """
        urlref = ("?map=Hot_Spot_Deforestation_Patch_analysis.qgs&request=GetFeature&service=WFS"
                  "&typename=Near_real_time_deforestation&version=1.0.0")
        rv = self.client.get(urlref)
        assert rv.status_code < 500

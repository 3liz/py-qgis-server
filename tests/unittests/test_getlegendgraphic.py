"""
    Test Getfeature requests
"""
import pytest

from pyqgisserver.tests import HTTPTestCase

xlink = "{http://www.w3.org/1999/xlink}"


class Tests(HTTPTestCase):

    @pytest.mark.skip(reason="Wait for proper datasource")
    def test_getlegendgraphic_xml(self):
        """ Test getlegendgraphic
        """
        rv = self.client.get(
            "?MAP=france_parts.qgs&SERVICE=WFS&REQUEST=GetLegendGraphic&VERSION=1.0.0"
            "&FORMAT=image/png&WIDTH=20&HEIGHT=20&LAYER=france_parts_bordure",
        )
        assert rv.status_code == 200
        assert rv.headers['Content-Type'].startswith('text/xml;')

    @pytest.mark.skip(reason="Wait for proper datasource")
    def test_getlegendgraphic_json(self):
        """ Test getlegendgraphic in json format
        """
        rv = self.client.get(
            "?MAP=france_parts.qgs&SERVICE=WFS&REQUEST=GetLegendGraphic&VERSION=1.0.0"
            "&FORMAT=json&WIDTH=20&HEIGHT=20&LAYER=france_parts_bordure",
        )
        assert rv.status_code == 200
        assert rv.headers['Content-Type'].startswith('text/xml;')

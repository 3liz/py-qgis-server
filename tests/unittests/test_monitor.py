""" Test monitoring data
"""
import os

from pyqgisserver.tests import HTTPTestCase
from pyqgisserver.monitor import Monitor

class Tests(HTTPTestCase):

    def test_monitor_data(self):
        """ Test getcapabilities hrefs
        """
        monitor = Monitor.initialize()
        assert monitor is not None

        monitor.messages.clear()

        # Check invironment
        assert 'QGSRV_MONITOR_TAG_EXTRA_DATA' in os.environ        
        assert 'EXTRA_DATA' in monitor.global_tags

        # Send request
        rv = self.client.get( "?MAP=france_parts.qgs&SERVICE=WMS&request=GetCapabilities" )
        assert rv.status_code == 200

        #check monitor data
        assert len(monitor.messages) == 1
        
        params, meta = monitor.messages[0]
        assert params['MAP'] == 'france_parts.qgs'
        assert params['SERVICE'] == 'WMS'
        assert params['REQUEST'] == 'GetCapabilities'
        assert params['EXTRA_DATA'] == 'monitor.test'
        assert params['RESPONSE_STATUS'] == 200
        assert 'RESPONSE_TIME' in params
        

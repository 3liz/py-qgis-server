""" Store monitoring data in memory table

    Used for testing purposes
    DO NOT USE IN PRODUCTION
"""
import logging

from typing import Dict

from  .base import MonitorBase

LOGGER = logging.getLogger('SRVLOG')

class Monitor(MonitorBase):

    def __init__(self):
        super().__init__()

        self.messages = []

    def emit( self, params: Dict[str,str], meta: Dict ) -> None:
        """ Publish monitor data
        """
        data = dict(self.global_tags)
        data.update(params)
        self.messages.append((data,meta))


__instance = Monitor()


# Entry point
def get_monitor_service() -> Monitor:
    """ Entry point for 'amqp' monitor
    """
    return __instance



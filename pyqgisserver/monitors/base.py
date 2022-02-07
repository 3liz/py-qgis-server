""" Monitor utilities
"""
import os

TAG_PREFIX_LEGACY = 'AMQP_GLOBAL_TAG_'
TAG_PREFIX = 'QGSRV_MONITOR_TAG_'

def _get_tags( prefix: str ):
    return ((e.partition(prefix)[2],os.environ[e]) for e in os.environ if e.startswith(prefix))

class MonitorBase:

    def __init__( self ):
        """ Return tags defined in environment
        """
        # Get global tags
        tags =  { t:v for (t,v) in _get_tags(TAG_PREFIX) if t }
        tags.update( (t,v) for (t,v) in _get_tags(TAG_PREFIX_LEGACY) if t )
        self.global_tags = tags

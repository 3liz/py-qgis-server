
import os
import traceback
import logging
from tornado.web import StaticFileHandler
from .runtime import read_configuration, run_application_context
from .version import __description__, __version__
from .config import get_config, validate_config_path

from qgistools.app import start_qgis_application

LOGGER = logging.getLogger('QGSRV')

def configure_handlers():
    """
    """
    from .handlers import (RootHandler, QgsServerHandler)
    handlers = []

    handlers.extend([
        (r"/"   , RootHandler),
        (r"/wms", QgsServerHandler)
    ])

    return handlers


def set_server_loglevel():
    """ Set environment variable QGIS_SERVER_LOG_LEVEL
    """
    loglevel = LOGGER.level
    if loglevel <= logging.DEBUG:
        level='0'
    elif loglevel <= logging.WARNING:
        level='1'
    else:
        level=2
        
    os.environ['QGIS_SERVER_LOG_LEVEL'] = level
 

def main():
    """ Run server loop
    """
    import argparse

    version_tag = "Qgis WMS/WFS server/{}".format(__version__)

    read_configuration("qgisserver", cli_parser=argparse.ArgumentParser(description=__description__))
    handlers = configure_handlers()

    validate_config_path('cache','rootdir')
    try:
        with run_application_context(handlers) as task_id:
            if task_id is not None:
                # Configure extra stuff after fork
               set_server_loglevel()
               start_qgis_application( enable_processing=True, verbose=LOGGER.level<=logging.DEBUG)
    finally:
        pass


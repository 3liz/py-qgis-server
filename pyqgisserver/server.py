
import os
import traceback
import logging
from tornado.web import StaticFileHandler
from .runtime import read_configuration, run_application_context
from .version import __description__, __version__
from .config import get_config, validate_config_path, read_config_dict

from qgistools.app import start_qgis_application

LOGGER = logging.getLogger('QGSRV')

def configure_handlers():
    """
    """
    from .handlers import (RootHandler, QgsServerHandler)
    handlers = []

    handlers.extend([
        (r"/"    , RootHandler),
        (r"/ows/", QgsServerHandler)
    ])

    return handlers


def main():
    """ Run server loop
    """
    import argparse

    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument('--rootdir', default=get_config('cache')['rootdir'], metavar='PATH', help='Path to qgis projects')

    args = read_configuration(cli_parser=parser)
    read_config_dict({'cache': { 'rootdir': args.rootdir }})
    validate_config_path('cache','rootdir')

    handlers = configure_handlers()

    try:
        with run_application_context(handlers) as task_id:
            if task_id is not None:
               # Configure extra stuff after fork
               start_qgis_application( enable_processing=True, logger=LOGGER, verbose=LOGGER.level<=logging.DEBUG)
    finally:
        pass


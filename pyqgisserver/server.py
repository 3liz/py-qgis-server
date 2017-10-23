import os
from tornado.web import StaticFileHandler
from .runtime import read_configuration, run_application_context
from .version import __description__, __version__
from .config import get_config, validate_config_path

from qgistools.app import start_qgis_application, setup_qgis_paths

def configure_handlers():
    """
    """
    from .handlers import (RootHandler)
    handlers = []


    handlers.extend([
        (r"/", RootHandler),
    ])

    return handlers


def main():
    """ Run server loop
    """
    import argparse

    version_tag = "Qgis WMS/WFS server/{}".format(__version__)

    read_configuration("qgisserver", cli_parser=argparse.ArgumentParser(description=__description__))
    handlers = configure_handlers()
    verbose  = get_config('logging').get('level').upper()=='DEBUG'

    validate_config_path('server','rootdir')
    try:
        with run_application_context(handlers) as task_id:
            if task_id is not None:
                # Configure extra stuff after fork
                start_qgis_application( enable_processing=True, verbose=verbose)
    finally:
        pass


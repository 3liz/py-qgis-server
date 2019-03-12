import sys
import os
import pytest

import logging
from pyqgisserver.tests import TestRuntime
from time import sleep

def pytest_addoption(parser):
    parser.addoption("--server-log-level", choices=['debug', 'info', 'warning', 'error'] , help="log level",
                     default='info')


server_log_level = None

def pytest_configure(config):
    global server_log_level
    server_log_level = config.getoption('server_log_level')


def pytest_sessionstart(session):
    """ Start subprocesses
    """
    logging.basicConfig( stream=sys.stderr )
    logging.disable(logging.ERROR)

    logger = logging.getLogger('QGSRV')
    logger.setLevel(getattr(logging, server_log_level.upper()))

    rt = TestRuntime.instance()
    rt.start()
    print("Waiting for server to initialize...")
    sleep(2)

def pytest_sessionfinish(session, exitstatus):
    """ End subprocesses
    """
    rt = TestRuntime.instance()
    rt.stop()
   


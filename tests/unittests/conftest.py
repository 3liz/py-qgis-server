import sys
import os
import pytest

import logging
from pyqgisserver.tests import TestRuntime
from time import sleep

from pathlib import Path

def pytest_addoption(parser):
    parser.addoption("--server-debug", action="store_true" , help="Set debug mode",
                     default=False)


server_debug = False

@pytest.fixture(scope='session')
def data(request):
    return Path(request.config.rootdir.strpath).parent / 'data'


def pytest_configure(config):
    global server_debug
    server_debug = config.getoption('server_debug')


def pytest_sessionstart(session):
    """ Start subprocesses
    """
    logging.basicConfig( stream=sys.stderr, level=logging.DEBUG )

    if not server_debug:
        logging.disable(logging.WARNING)

    #logger = logging.getLogger('QGSRV')
    #logger.setLevel(log_level)

    rt = TestRuntime.instance()
    rt.start()
    print("Waiting for server to initialize...")
    sleep(2)

def pytest_sessionfinish(session, exitstatus):
    """ End subprocesses
    """
    rt = TestRuntime.instance()
    rt.stop()
   


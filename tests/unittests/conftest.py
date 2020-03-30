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
    parser.addoption("--with-postgres", action="store_true", help="Run postgres tests",
                     default=False)

server_debug  = False

def pytest_configure(config):

    # Debug mode
    global server_debug, postgres_user
    server_debug  = config.getoption('server_debug')

    # Postgres 
    config.with_postgres = config.getoption('with_postgres')
    config.addinivalue_line("markers", "with_postgres: mark test as postgres run")


@pytest.fixture(scope='session')
def data(request):
    return Path(request.config.rootdir.strpath).parent / 'data'


@pytest.fixture(scope='session')
def data(pg):
    return Path(request.config.rootdir.strpath).parent / 'data'

def pytest_collection_modifyitems(config, items):
    if config.with_postgres:
        # postgres enabled: do not skip tests
        return
    skip_postgres = pytest.mark.skip(reason="Postgres tests disabled")
    for item in items:
        if "with_postgres" in item.keywords:
            item.add_marker(skip_postgres)


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
   


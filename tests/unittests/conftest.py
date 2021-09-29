import sys
import os
import pytest

import logging
from pyqgisserver.tests import TestRuntime
from time import sleep

from pathlib import Path

def pytest_addoption(parser):
    parser.addoption("--with-postgres", action="store_true", help="Run postgres tests",
                     default=False)
    parser.addoption("--with-profiles", action="store_true", help="Run profiles tests",
                     default=False)


def pytest_configure(config):

    # Debug mode
    global postgres_user

    # Postgres 
    config.with_postgres = config.getoption('with_postgres')
    config.addinivalue_line("markers", "with_postgres: mark test as postgres run")

    # Profiles
    config.with_profiles = config.getoption('with_profiles')
    config.addinivalue_line("markers", "with_profiles: mark test as profiles test")


@pytest.fixture(scope='session')
def data(request):
    return Path(request.config.rootdir.strpath).parent / 'data'


def pytest_collection_modifyitems(config, items):
    if config.with_postgres:
        # postgres enabled: do not skip tests
        return
    skip_postgres = pytest.mark.skip(reason="Postgres tests disabled")
    skip_profiles = pytest.mark.skip(reason="Profiles tests disabled")
    for item in items:
        if "with_postgres" in item.keywords:
            item.add_marker(skip_postgres)
        if "with_profiles" in item.keywords:
            item.add_marker(skip_profiles)


def pytest_sessionstart(session):
    """ Start subprocesses
    """
    rt = TestRuntime.instance()
    rt.start()
    print("Waiting for server to initialize...")
    sleep(2)


def pytest_sessionfinish(session, exitstatus):
    """ End subprocesses
    """
    rt = TestRuntime.instance()
    rt.stop()
   


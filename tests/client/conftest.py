import os
import pytest

server_host = "localhost:8080"


def pytest_addoption(parser):
    parser.addoption("--host", metavar="HOST[:PORT]", default=server_host, help="server host name (and port)")
    parser.addoption("--with-postgres", action="store_true", help="Run postgres tests",
                     default=False)
    parser.addoption("--with-profiles", action="store_true", help="Run profiles tests",
                     default=False)



def pytest_configure(config):
    global server_host
    server_host = config.getoption('host')

    # Postgres 
    config.with_postgres = config.getoption('with_postgres')
    config.addinivalue_line("markers", "with_postgres: mark test as postgres run")

    # Profiles
    config.with_profiles = config.getoption('with_profiles')
    config.addinivalue_line("markers", "with_profiles: mark test as profiles test")


def pytest_collection_modifyitems(config, items):
    if config.with_postgres:
        # postgres enabled: do not skip tests
        return
    if config.with_profiles:
        # postgres enabled: do not skip tests
        return
    skip_postgres = pytest.mark.skip(reason="Postgres tests disabled")
    skip_profiles = pytest.mark.skip(reason="Profiles tests disabled")
    for item in items:
        if "with_postgres" in item.keywords:
            item.add_marker(skip_postgres)
        if "with_profiles" in item.keywords:
            item.add_marker(skip_profiles)

@pytest.fixture(scope='session')
def host():
    return server_host




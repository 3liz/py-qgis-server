import os
import pytest

server_host = "localhost:8080"


def pytest_addoption(parser):
    parser.addoption("--host", metavar="HOST[:PORT]", default=server_host, help="server host name (and port)")


def pytest_configure(config):
    global server_host
    server_host = config.getoption('host')


@pytest.fixture(scope='session')
def host():
    return server_host




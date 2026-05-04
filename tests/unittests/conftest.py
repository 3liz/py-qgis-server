import os
import sys

from pathlib import Path
from time import sleep

import pytest

from pyqgisserver.tests import TestRuntime


def pytest_report_header(config):
    from osgeo import gdal

    from qgis.core import Qgis
    from qgis.PyQt.QtCore import QT_VERSION_STR

    gdal_version = gdal.VersionInfo("VERSION_NUM")
    return (
        f"QGIS : {Qgis.versionInt()}\n"
        f"QT : {QT_VERSION_STR}"
        f"Python GDAL : {gdal_version}\n"
        f"Python : {sys.version}\n"
    )


def pytest_addoption(parser):
    parser.addoption("--with-postgres", action="store_true", help="Run postgres tests", default=False)
    parser.addoption("--with-profiles", action="store_true", help="Run profiles tests", default=False)


def pytest_configure(config):

    # Debug mode
    global postgres_user

    # Postgres
    config.with_postgres = config.getoption("with_postgres")
    config.addinivalue_line("markers", "with_postgres: mark test as postgres run")

    # Profiles
    config.with_profiles = config.getoption("with_profiles")
    config.addinivalue_line("markers", "with_profiles: mark test as profiles test")


@pytest.fixture(scope="session")
def rootdir(request: pytest.FixtureRequest) -> Path:
    return request.config.rootpath


@pytest.fixture(scope="session")
def data(rootdir: Path) -> Path:
    return rootdir.joinpath("data")


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


def pytest_sessionstart(session: pytest.Session):
    """Start subprocesses"""
    # Setup configuration
    root = session.config.rootpath

    qgis_config_path = str(root.joinpath("qgis"))
    project_rootdir = str(root.joinpath("data"))
    plugins_path = str(root.joinpath("plugins"))

    os.environ.update(
        QGIS_OPTIONS_PATH=qgis_config_path,
        QGIS_CUSTOM_CONFIG_PATH=qgis_config_path,
        QGIS_SERVER_DISABLE_GETPRINT="yes",
        QGSRV_CACHE_ROOTDIR=project_rootdir,
        QGSRV_TRUST_LAYER_METADATA="yes",
        QGSRV_SERVER_WORKERS="1",
        QGSRV_SERVER_PLUGINPATH=plugins_path,
        QGSRV_PROJECTS_SCHEMES_TEST=f"{project_rootdir}/",
        QGSRV_PROJECTS_SCHEMES_FOO="file:foobar/",
        QGSRV_PROJECTS_SCHEMES_BAR="file:foobar?data={path}",
        QGSRV_LOGGING_LEVEL="DEBUG",
        QGSRV_SERVER_HTTP_PROXY="yes",
        QGSRV_SERVER_STATUS_PAGE="yes",
        QGSRV_API_ENDPOINTS_LANDING_PAGE="/ows/catalog",
        QGSRV_API_ENABLED_LANDING_PAGE="yes",
        QGSRV_CACHE_STRICT_CHECK="yes",
        QGSRV_SERVER_MONITOR="test",
        QGSRV_MONITOR_TAG_EXTRA_DATA="monitor.test",
        QGSRV_CACHE_ADVANCED_REPORT="yes",
        ASYNC_TEST_TIMEOUT=os.getenv("ASYNC_TEST_TIMEOUT", "20"),
    )

    rt = TestRuntime.instance()
    rt.start()
    print("Waiting for server to initialize...")
    sleep(2)


def pytest_sessionfinish(session, exitstatus):
    """End subprocesses"""
    rt = TestRuntime.instance()
    rt.stop()

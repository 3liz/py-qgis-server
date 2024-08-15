
from pathlib import Path

import pytest

from qgis.core import QgsProject

from pyqgisserver.config import confservice
from pyqgisserver.qgscache.cachemanager import (
    CacheType,
    PathNotAllowedError,
    QgsCacheManager,
    preload_projects_file,
)


def test_aliases():
    """ Test alias resolution for file
    """
    rootpath = Path(confservice.get('projects.cache', 'rootdir'))

    cacheservice = QgsCacheManager()

    url = cacheservice.resolve_alias('france_parts')
    assert url.scheme == 'file'
    assert url.path   == str(rootpath / 'france_parts')

    url = cacheservice.resolve_alias('file:france_parts')
    assert url.scheme == 'file'
    assert url.path   == str(rootpath / 'france_parts')

    url = cacheservice.resolve_alias('foo:france_parts')
    assert url.scheme == 'file'
    assert url.path   == '/foobar/france_parts'

    url = cacheservice.resolve_alias('test:france_parts')
    assert url.scheme == ''
    assert url.path   == str(rootpath / 'france_parts')

    url = cacheservice.resolve_alias('bar:france_parts')
    assert url.scheme == 'file'
    assert url.path   == 'foobar'
    assert url.query  == 'data=france_parts'


def test_absolute_path_with_alias():
    """
    """
    cacheservice = QgsCacheManager()

    # Passing an absolute path that is compatible with
    # the scheme base url is ok
    url = cacheservice.resolve_alias('foo:/foobar/france_parts')
    assert url.scheme == 'file'
    assert url.path   == '/foobar/france_parts'

    # But not a path wich does is no a relative path
    # to base url
    with pytest.raises(PathNotAllowedError):
        url = cacheservice.resolve_alias('foo:/france_parts')


def test_file_cache():
    """ Tetst file protocol handler
    """
    rootpath = Path(confservice.get('projects.cache', 'rootdir'))

    cacheservice = QgsCacheManager()
    details = cacheservice.peek('france_parts')
    assert details is None

    project, updated = cacheservice.lookup('france_parts')
    assert updated
    assert project is not None
    assert project.fileName() == str(rootpath / 'france_parts.qgs')

    details = cacheservice.peek('france_parts')
    assert details is not None
    assert details.project is project


def test_projects_scheme():
    """ Tetst file protocol handler
    """
    rootpath = Path(confservice.get('projects.cache', 'rootdir'))

    cacheservice = QgsCacheManager()
    details = cacheservice.peek('test:france_parts')
    assert details is None

    project, updated = cacheservice.lookup('test:france_parts')
    assert updated
    assert project is not None
    assert project.fileName() == str(rootpath / 'france_parts.qgs')

    details = cacheservice.peek('test:france_parts')
    assert details is not None
    assert details.project is project


def test_file_not_found():
    """ Test non existant file return error
    """
    cacheservice = QgsCacheManager()
    with pytest.raises(FileNotFoundError):
        cacheservice.lookup('I_do_not_exists')


def test_invalid_scheme():
    """ Test non existant file return error
    """
    cacheservice = QgsCacheManager()
    with pytest.raises(FileNotFoundError):
        cacheservice.lookup('badscheme:///foo')


@pytest.mark.with_postgres
def test_postgres_cache():
    """ Test postgres handler
    """
    cacheservice = QgsCacheManager()

    url = 'postgres:///?project=france_parts'

    details = cacheservice.peek(url)
    assert details is None

    project, updated = cacheservice.lookup(url)
    assert updated
    assert isinstance(project, QgsProject)

    # Check that project is updated
    project, updated = cacheservice.lookup(url)
    assert not updated
    assert isinstance(project, QgsProject)

    details = cacheservice.peek(url)
    assert details is not None
    assert details.project is project


@pytest.mark.with_postgres
def test_postgres_with_pgservice():

    url = 'postgres:///?service=local&project=france_parts'

    cacheservice = QgsCacheManager()

    details = cacheservice.peek(url)
    assert details is None

    project, updated = cacheservice.lookup(url)
    assert updated
    assert isinstance(project, QgsProject)

    details = cacheservice.peek(url)
    assert details is not None
    assert details.project is project


@pytest.mark.with_postgres
def test_postgres_pgservice_fail():

    url = 'postgres:///?service=not_working&project=france_parts'

    cacheservice = QgsCacheManager()

    with pytest.raises(FileNotFoundError):
        cacheservice.lookup(url)


def test_preload_projects(data: Path):
    """ Test preloading projects files
    """
    cacheservice = QgsCacheManager()
    path = data / 'preloads.list'

    loaded = preload_projects_file(path, cacheservice)
    assert loaded == 2

    # file:france_parts.qgs
    # project_simple.qgs
    # raster_layer.qgs (invalid layer)

    # Ensure  that items are in static cache
    items = list(k for k, _ in cacheservice.items(CacheType.STATIC))
    assert "file:france_parts.qgs" in items
    assert "project_simple.qgs" in items

    details = cacheservice.peek('file:france_parts.qgs')
    assert details is not None

    details = cacheservice.peek('project_simple.qgs')
    assert details is not None

    details = cacheservice.peek('raster_layer.qgs')
    assert details is None


def test_get_modified_time(data: Path):
    """ Test modified time
    """
    cacheservice = QgsCacheManager()

    path = data / 'france_parts.qgs'
    modified_time1 = cacheservice.get_modified_time('file:france_parts.qgs')

    # Check that no files is loaded
    assert cacheservice.peek('file:france_parts.qgs') is None

    # Update file
    path.touch()
    modified_time2 = cacheservice.get_modified_time('file:france_parts.qgs')

    assert modified_time2 > modified_time1

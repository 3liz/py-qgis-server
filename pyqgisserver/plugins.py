#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Qgis server plugin managment

"""
import sys
import logging
import configparser
import traceback

from pathlib import Path
from typing import Generator, Dict

from .config  import confservice

LOGGER = logging.getLogger('SRVLOG')

server_plugins = {}
failed_plugins = {}


def checkQgisVersion(minver: str, maxver: str) -> bool:
    from qgis.core import Qgis

    def to_int(ver):
        major, *ver = ver.split('.')
        major = int(major)
        minor = int(ver[0]) if len(ver) > 0 else 0
        rev   = int(ver[1]) if len(ver) > 1 else 0
        if minor >= 99:
            minor = rev = 0
            major += 1
        if rev > 99:
            rev = 99
        return int("{:d}{:02d}{:02d}".format(major,minor,rev))


    version = to_int(Qgis.QGIS_VERSION.split('-')[0])
    minver  = to_int(minver) if minver else version
    maxver  = to_int(maxver) if maxver else version

    return minver <= version <= maxver



def find_plugins(path: str) -> Generator[str,None,None]:
    """ return list of plugins in given path
    """
    path = Path(path)
    for plugin in path.glob("*"):
        LOGGER.debug(f"Looking for plugin in '{plugin}'")

        if not plugin.is_dir():
            # Warn about dangling symlink
            # This occurs when running in docker container
            # and symlink target path are not visible from the
            # container - give some hint for debugging
            if plugin.is_symlink():
                LOGGER.warning(f"*** The symbolic link '{plugin}' is not resolved."
                               " If you are running in docker container please consider"
                               "mounting the target path in the container.")
            continue

        metadata_file = plugin / 'metadata.txt'
        if not metadata_file.exists():
            # Do not log here
            continue

        if not (plugin / '__init__.py').exists():
            LOGGER.warning(f"'{plugin}' : Found metadata file but no Python entry point !")
            continue

        cp = configparser.ConfigParser()

        try:
            with metadata_file.open(mode='rt') as f:
                cp.read_file(f)

            if not cp['general'].getboolean('server'):
                LOGGER.warning(f"'{plugin}' is not a server plugin")
                continue

            min_ver = cp['general'].get('qgisMinimumVersion')
            max_ver = cp['general'].get('qgisMaximumVersion')

        except Exception as exc:
            LOGGER.error(f"'{plugin}' : Error reading plugin metadata '{metadata_file}': {exc}")
            continue

        if not checkQgisVersion(min_ver,max_ver):
            LOGGER.warning(f"Unsupported version for {plugin}. Discarding")
            continue

        yield plugin.name



def load_plugins(serverIface: 'QgsServerInterface'): # noqa F821
    """ Start all plugins """

    plugin_path = confservice.get('server','pluginpath')
    if not plugin_path:
        return

    LOGGER.info(f"Initializing plugins from {plugin_path}")
    sys.path.append(plugin_path)

    success = 0
    error = 0
    for plugin in find_plugins(plugin_path):
        # noinspection PyBroadException
        try:
            __import__(plugin)

            package = sys.modules[plugin]

            # Initialize the plugin
            server_plugins[plugin] = package.serverClassFactory(serverIface)
            LOGGER.info(f"Loaded plugin {plugin}")
            success += 1
        except Exception:
            strace = traceback.format_exc()
            LOGGER.error(f"Error loading plugin '{plugin}'\n{strace}")
            failed_plugins[plugin] = strace
            error += 1

    LOGGER.info(f"Loaded {success} plugin(s) successfully")
    if error:
        LOGGER.warning(f"{error} plugin(s) having an issue")


def plugin_metadata( plugin: str ) -> Dict:
    """ Return plugin metadata
    """
    if plugin not in server_plugins:
        return

    # Read metadata
    path = Path(sys.modules[plugin].__file__)
    metadatafile = path.parent / 'metadata.txt'
    if not metadatafile.exists():
        return

    with metadatafile.open(mode='rt') as f:
        cp = configparser.ConfigParser()
        cp.read_file(f)
        metadata = { s: dict(p.items()) for s,p in cp.items() }
        metadata.pop('DEFAULT',None)
        metadata.update(path=str(path))
        return metadata


def plugin_list():
    """ Iterate over loaded plugins
    """
    return (k for k in server_plugins.keys())

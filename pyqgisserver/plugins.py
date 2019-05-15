#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Qgis server plugin managment 

"""
import os
import sys
import logging
import traceback
import glob
import configparser

from typing import Generator

from .config  import get_config

LOGGER = logging.getLogger('QGSRV') 

server_plugins = {}

class PluginError(Exception): pass


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
    from qgis.core import Qgis

    for plugin in glob.glob(path + "/*"):
        LOGGER.debug("Looking for plugin in %s", plugin)
        if not os.path.isdir(plugin):
            continue

        metadatafile = os.path.join(plugin, 'metadata.txt')
        if not os.path.exists(metadatafile):
            continue

        if not os.path.exists(os.path.join(plugin, '__init__.py')):
            LOGGER.warning("Found metadata file but no entry point !")
            continue

        cp = configparser.ConfigParser()

        try:
            with open(metadatafile, mode='rt') as f:
                cp.read_file(f)

            if not cp['general'].getboolean('server'):
                LOGGER.warning("%s is not a server plugin", plugin)
                continue

            minver = cp['general'].get('qgisMinimumVersion')
            maxver = cp['general'].get('qgisMaximumVersion')

        except Exception as exc:
            LOGGER.error("Error reading plugin metadata '%s': %s",metadatafile,exc)
            continue

        if not checkQgisVersion(minver,maxver):
            LOGGER.warning("Unsupported version for %s. Discarding", plugin)
            continue

        yield os.path.basename(plugin)



def load_plugins(serverIface: 'QgsServerInterface') -> None:
    """ Start all plugins
    """

    plugin_path = get_config('server')['pluginpath']
    if not plugin_path:
        return

    LOGGER.info("Initializing plugins from %s", plugin_path)
    sys.path.append(plugin_path)

    for plugin in find_plugins(plugin_path):
        try:
            __import__(plugin)

            package = sys.modules[plugin] 

            # Initialize the plugin
            server_plugins[plugin] = package.serverClassFactory(serverIface)
            LOGGER.info("Loaded plugin %s",plugin)
        except:
            LOGGER.error("Error loading plugin %s",plugin)
            raise 
    



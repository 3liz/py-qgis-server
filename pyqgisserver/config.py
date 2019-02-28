#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" 
Configuration management
"""
import os
import sys
import configparser
import logging

CONFIG = None

getenv = os.environ.get

LOGGER = logging.getLogger('QGSRV')

def get_config(section):
    """ Return the configuration section
    """
    if CONFIG is None:
        load_configuration()

    return CONFIG[section]


def set_config(section, name, value):
    """ Set configuration value
    """
    CONFIG.set(section, name , value)


def load_configuration():
    """ Read configuration file

        Load PyWPS configuration from configuration file.

    :param cfgfile: path to the configuration file
    :param cfgdefault: default configuration dict
    :param cfgdict: configuration dict (override file and default)
    """

    global CONFIG

    LOGGER.info('loading configuration')
    CONFIG = configparser.ConfigParser()    

    CONFIG.add_section('server')
    CONFIG.set('server', 'port'       , getenv('QGSRV_SERVER_HTTP_PORT', '8080'))
    CONFIG.set('server', 'interfaces' , getenv('QGSRV_SERVER_INTERFACES', '0.0.0.0'))
    CONFIG.set('server', 'workers'    , getenv('QGSRV_SERVER_WORKERS', '2'))
    CONFIG.set('server', 'timeout'    , getenv('QGSRV_SERVER_TIMEOUT', '20'))
    CONFIG.set('server', 'profiles'   , getenv('QGSRV_SERVER_PROFILES', ''))
    CONFIG.set('server', 'map_rewrite', getenv('QGSRV_SERVER_MAP_REWRITE', ''))
    CONFIG.set('server', 'http_proxy' , getenv('QGSRV_SERVER_HTTP_PROXY', 'no'))
    CONFIG.set('server', 'proxy_url'  , getenv('QGSRV_SERVER_PROXY_URL' , ''))
    CONFIG.set('server', 'restartfile', getenv('QGSRV_SERVER_RESTARTFILE' , ''))

    CONFIG.add_section('logging')
    CONFIG.set('logging', 'level', getenv('QGSRV_LOGGING_LEVEL', 'DEBUG'))

    CONFIG.add_section('cache')
    CONFIG.set('cache', 'size'    , getenv('QGSRV_CACHE_SIZE','10' ))
    CONFIG.set('cache', 'rootdir' , getenv('QGSRV_CACHE_ROOTDIR',''))

    CONFIG.add_section('qgis')
    CONFIG.set('qgis', 'network_timeout', getenv('QGSRV_QGIS_NETWORK_TIMEOUT','20000'))

    CONFIG.add_section('zmq')
    CONFIG.set('zmq', 'identity'     , getenv('QGSRV_ZMQ_IDENTITY' ,'OWS-SERVER'))
    CONFIG.set('zmq', 'bindaddr'     , getenv('QGSRV_ZMQ_INADDR'   ,'tcp://*:18080'))
    CONFIG.set('zmq', 'maxqueue'     , getenv('QGSRV_ZMQ_MAXQUEUE' ,'1000'))
    CONFIG.set('zmq', 'timeout'      , getenv('QGSRV_ZMQ_TIMEOUT'  ,'15000'))
    CONFIG.set('zmq', 'broadcastaddr', getenv('QGSRV_ZMQ_BROADCASTADDR','tcp://*:18090'))

def read_config_dict( userdict ):
    """ Read configuration from dictionary

        Will override previous settings
    """
    CONFIG.read_dict( userdict )


def read_config_file( cfgfile ):
    """ Read configuration from file
    """
    CONFIG.read_file(cfgfile)
    LOGGER.info('Configuration file <%s> loaded', cfgfile)


def config_to_dict():
    """ Convert actual configuration to dictionary
    """
    return { s: dict(p.items()) for s,p in CONFIG.items() }


def validate_config_path(confname, confid, optional=False):
    """ Validate directory path
    """
    confvalue = get_config(confname).get(confid,'')

    if not confvalue and optional:
        return

    confvalue = os.path.normpath(confvalue)
    if not os.path.isdir(confvalue):
        LOGGER.error('server->%s configuration value %s is not directory' % (confid, confvalue))
        raise ValueError(confvalue)

    if not os.path.isabs(confvalue):
        LOGGER.error('server->%s configuration value %s is not absolute path' % (confid, confvalue))
        raise ValueError(confvalue)

    CONFIG.set(confname, confid, confvalue)




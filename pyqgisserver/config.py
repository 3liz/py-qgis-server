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
import functools

from typing import Any

getenv = os.getenv

LOGGER = logging.getLogger('SRVLOG')

CONFIG = configparser.ConfigParser()    


def print_config( fp ):
    """ print configuration to file
    """
    CONFIG.write(fp)


def load_configuration():
    """ Read configuration file

        Load server configuration from configuration file.
    """
    CONFIG.clear()

    LOGGER.info('loading configuration')

    CONFIG.add_section('server')
    CONFIG.set('server', 'port'          , getenv('QGSRV_SERVER_HTTP_PORT', '8080'))
    CONFIG.set('server', 'interfaces'    , getenv('QGSRV_SERVER_INTERFACES', '0.0.0.0'))
    CONFIG.set('server', 'workers'       , getenv('QGSRV_SERVER_WORKERS', '2'))
    CONFIG.set('server', 'timeout'       , getenv('QGSRV_SERVER_TIMEOUT', '20'))
    CONFIG.set('server', 'enable_filters', getenv('QGSRV_SERVER_ENABLE_FILTERS', 'yes'))
    CONFIG.set('server', 'http_proxy'    , getenv('QGSRV_SERVER_HTTP_PROXY', 'no'))
    CONFIG.set('server', 'proxy_url'     , getenv('QGSRV_SERVER_PROXY_URL' , ''))
    CONFIG.set('server', 'restartmon'    , getenv('QGSRV_SERVER_RESTARTMON' , ''))
    CONFIG.set('server', 'pluginpath'    , getenv('QGSRV_SERVER_PLUGINPATH' , ''))
    CONFIG.set('server', 'ssl'           , getenv('QGSRV_SERVER_SSL' , 'no'))
    CONFIG.set('server', 'ssl_cert'      , getenv('QGSRV_SERVER_SSL_CERT', ''))
    CONFIG.set('server', 'ssl_key'       , getenv('QGSRV_SERVER_SSL_KEY' , ''))
    CONFIG.set('server', 'cross_origin'  , getenv('QGSRV_SERVER_CROSS_ORIGIN' , 'yes'))

    CONFIG.add_section('logging')
    CONFIG.set('logging', 'level', getenv('QGSRV_LOGGING_LEVEL', 'DEBUG'))

    CONFIG.add_section('cache')
    CONFIG.set('cache', 'size'    , getenv('QGSRV_CACHE_SIZE','10' ))
    CONFIG.set('cache', 'rootdir' , getenv('QGSRV_CACHE_ROOTDIR',''))
    # Ensure that loaded project is valid before loading in cache
    CONFIG.set('cache', 'strict_check' , getenv('QGSRV_CACHE_STRICT_CHECK','yes'))

    CONFIG.add_section('zmq')
    CONFIG.set('zmq', 'identity'     , getenv('QGSRV_ZMQ_IDENTITY' ,'OWS-SERVER'))
    CONFIG.set('zmq', 'bindaddr'     , getenv('QGSRV_ZMQ_INADDR'   ,'tcp://*:18080'))
    CONFIG.set('zmq', 'maxqueue'     , getenv('QGSRV_ZMQ_MAXQUEUE' ,'1000'))
    # Control the lifetime of requests on waiting queue
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
    confvalue = CONFIG[confname].get(confid,'')

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

#
# Published services
#
from pyqgisservercontrib.core import componentmanager


NO_DEFAULT=object()

@componentmanager.register_factory('@3liz.org/config-service;1')
class ConfigService:
    """ Act as a proxy
    """ 

    def __init__(self):
        self.allow_env = True

    def __get_impl( self, _get_fun, section:str, option:str, fallback:Any = NO_DEFAULT ) -> Any:
        """
        """
        if self.allow_env:
            varname  = 'QGSRV_%s_%s' % (section.upper(),option.upper())
            value = _get_fun(section, option, fallback=os.getenv(varname, fallback))
        else:
            value = _get_fun(section, option, fallback=fallback)
        if value is NO_DEFAULT:
            raise KeyError('%s:%s' % (section,option))
        return value

    get        = functools.partialmethod(__get_impl,CONFIG.get) 
    getint     = functools.partialmethod(__get_impl,CONFIG.getint) 
    getboolean = functools.partialmethod(__get_impl,CONFIG.getboolean) 
    getfloat   = functools.partialmethod(__get_impl,CONFIG.getfloat) 

    def __getitem__(self, section):
        return CONFIG[section]

    def __contains__(self, section):
        return section in CONFIG

    def set( self, section:str, option:str, value: Any ) -> None:
        CONFIG.set( section, option, value )


confservice = ConfigService()



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


def get_env_config(section, name, env, default=None):
    """ Get configuration value from environment
        if not found in loaded config
    """
    cfg = CONFIG[section]
    return cfg.get(name,getenv(env,default))


def set_config(section, name, value):
    """ Set configuration value
    """
    CONFIG.set(section, name , value)


def print_config( fp ):
    """ print configuration to file
    """
    CONFIG.write(fp)


def load_configuration():
    """ Read configuration file

        Load server configuration from configuration file.
    """

    global CONFIG

    LOGGER.info('loading configuration')
    CONFIG = configparser.ConfigParser()    

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

    CONFIG.add_section('logging')
    CONFIG.set('logging', 'level', getenv('QGSRV_LOGGING_LEVEL', 'DEBUG'))

    CONFIG.add_section('cache')
    CONFIG.set('cache', 'size'    , getenv('QGSRV_CACHE_SIZE','10' ))
    CONFIG.set('cache', 'rootdir' , getenv('QGSRV_CACHE_ROOTDIR',''))

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




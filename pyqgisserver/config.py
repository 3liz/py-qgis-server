# -*- coding: utf-8 -*-i
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
    CONFIG.set('server', 'port'      , getenv('QGSRV_SERVER_HTTP_PORT', '8080'))
    CONFIG.set('server', 'interfaces', getenv('QGSRV_SERVER_INTERFACES', '*'))
    CONFIG.set('server', 'workers'   , getenv('QGSRV_SERVER_WORKERS', '2'))
    CONFIG.set('server', 'rootdir'   , getenv('QGSRV_SERVER_ROOTDIR', ''))

    CONFIG.add_section('logging')
    CONFIG.set('logging', 'level', getenv('QGSRV_LOGGING_LEVEL', 'DEBUG'))


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




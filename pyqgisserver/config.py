#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Configuration management

Configuration can be done either by using aconfiguration file or with environnement variable.

Except stated otherwise, the rule for environnement variable names is ``QGSRV_<SECTION>_<KEY>`` all in uppercase.

Options 


"""

import os
import configparser
import logging
import functools

from typing import Any, Iterable, Tuple

from pyqgisservercontrib.core import componentmanager

getenv = os.getenv

LOGGER = logging.getLogger('SRVLOG')

CONFIG = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())    
# Preserve case
CONFIG.optionxform = lambda opt: opt


def getenv2( env1, env2, default):
    """ Get value from alternate env variable
    """
    return getenv(env1,getenv(env2,default))


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
    CONFIG.set('server', 'enable_filters', getenv('QGSRV_SERVER_ENABLE_FILTERS', 'no'))
    CONFIG.set('server', 'http_proxy'    , getenv('QGSRV_SERVER_HTTP_PROXY', 'no'))
    CONFIG.set('server', 'proxy_url'     , getenv('QGSRV_SERVER_PROXY_URL', ''))
    CONFIG.set('server', 'restartmon'    , getenv('QGSRV_SERVER_RESTARTMON', ''))
    CONFIG.set('server', 'ssl'           , getenv('QGSRV_SERVER_SSL', 'no'))
    CONFIG.set('server', 'ssl_cert'      , getenv('QGSRV_SERVER_SSL_CERT', ''))
    CONFIG.set('server', 'ssl_key'       , getenv('QGSRV_SERVER_SSL_KEY', ''))
    CONFIG.set('server', 'cross_origin'  , getenv('QGSRV_SERVER_CROSS_ORIGIN', 'yes'))
    CONFIG.set('server', 'status_page'   , getenv('QGSRV_SERVER_STATUS_PAGE', 'no'))
    CONFIG.set('server', 'allow_headers' , getenv('QGSRV_SERVER_ALLOW_HEADERS', 'X-Qgis-,X-Lizmap-'))
    CONFIG.set('server', 'memory_high_water_mark', 
               getenv('QGSRV_SERVER_MEMORY_HIGH_WATER_MARK', '0.9'))
    CONFIG.set('server', 'getfeaturelimit', getenv('QGSRV_SERVER_GETFEATURELIMIT', '-1'))
    CONFIG.set('server', 'pluginpath', 
               getenv2('QGSRV_SERVER_PLUGINPATH','QGIS_PLUGINPATH', ''))
 
    #
    # Logging
    #
    CONFIG.add_section('logging')
    CONFIG.set('logging', 'level', getenv('QGSRV_LOGGING_LEVEL', 'DEBUG'))
    CONFIG.set('logging', 'qgis_info', getenv('QGSRV_LOGGING_QGIS_INFO', 'no'))

    #
    # Api configuration
    #

    # Qgis api endpoints
    CONFIG.add_section('api.endpoints')
    CONFIG.set('api.endpoints', 'landing_page', getenv('QGSRV_API_ENDPOINTS_LANDING_PAGE','/ows/catalog'))
    CONFIG.set('api.endpoints', 'lizmap_api', getenv('QGSRV_API_ENDPOINTS_LIZMAP','/lizmap'))

    # Services enabled
    CONFIG.add_section('api.enabled')
    CONFIG.set('api.enabled', 'landing_page', getenv('QGSRV_API_ENABLED_LANDING_PAGE','no'))
    CONFIG.set('api.enabled', 'lizmap_api', getenv('QGSRV_API_ENABLED_LIZMAP','no'))

    # Landing page config mapping
    CONFIG.add_section('api:landing_page')
    CONFIG.set('api:landing_page', 'QGIS_SERVER_LANDING_PAGE_PREFIX', 
               '${api.endpoints:landing_page}')
    CONFIG.set('api:landing_page', 'QGIS_SERVER_LANDING_PAGE_PROJECTS_DIRECTORIES', 
               '${projects.cache:rootdir}')

    #
    # Projects cache
    #
    CONFIG.add_section('projects.cache')
    CONFIG.set('projects.cache', 'size'    , getenv('QGSRV_CACHE_SIZE','10' ))
    CONFIG.set('projects.cache', 'rootdir' , getenv('QGSRV_CACHE_ROOTDIR',''))
    CONFIG.set('projects.cache', 'strict_check' , getenv('QGSRV_CACHE_STRICT_CHECK','yes'))
    CONFIG.set('projects.cache', 'insecure'     , getenv('QGSRV_CACHE_INSECURE','no'))
    CONFIG.set('projects.cache', 'preload_config'      , getenv('QGSRV_CACHE_PRELOAD_CONFIG',''))
    # Use same variable name as Qgis server options
    CONFIG.set('projects.cache', 'trust_layer_metadata', 
               getenv2('QGSRV_TRUST_LAYER_METADATA','QGIS_SERVER_TRUST_LAYER_METADATA','no'))
    CONFIG.set('projects.cache', 'disable_getprint'    , 
               getenv2('QGSRV_DISABLE_GETPRINT','QGIS_SERVER_DISABLE_GETPRINT','no'))
    CONFIG.set('projects.cache', 'disable_owsurls'     , getenv('QGSRV_CACHE_DISABLE_OWSURLS','no')) 
    CONFIG.set('projects.cache', 'force_etag'          , getenv('QGSRV_CACHE_FORCE_ETAG','no')) 
    CONFIG.set('projects.cache', 'default_handler'     , getenv('QGSRV_CACHE_DEFAULT_HANDLER', 'file'))
    CONFIG.set('projects.cache', 'allow_storage_schemes', getenv('QGSRV_CACHE_ALLOW_STORAGE_SCHEMES', '*'))
    CONFIG.set('projects.cache', 'check_interval'      , getenv('QGSRV_CACHE_CHECK_INTERVAL', '0'))
    CONFIG.set('projects.cache', 'observers'           , getenv('QGSRV_CACHE_OBSERVERS', ''))
    CONFIG.set('projects.cache', 'advanced_report'     , getenv('QGSRV_CACHE_ADVANCED_REPORT', 'no'))

    # Map read/create options
    CONFIG.set('projects.cache', 'force_readonly_layers'    , getenv('QGIS_SERVER_FORCE_READONLY_LAYERS', 'yes'))

    # 
    CONFIG.add_section('projects.schemes')

    #
    CONFIG.add_section('zmq')
    # Identity prefix used in 0MQ worker socket 
    CONFIG.set('zmq', 'identity'     , getenv('QGSRV_ZMQ_IDENTITY' ,'OWS-SERVER'))
    # Control the maximum lenghth of the waiting queue
    CONFIG.set('zmq', 'maxqueue'     , getenv('QGSRV_ZMQ_MAXQUEUE' ,'1000'))
    # Control the lifetime of requests on the waiting queue 
    CONFIG.set('zmq', 'timeout'      , getenv('QGSRV_ZMQ_TIMEOUT'  ,'15000'))
    # Host Address to bind/connect 0MQ sockets - used only with proxy/worker configuration
    CONFIG.set('zmq', 'hostaddr'     , getenv('QGSRV_ZMQ_HOSTADDR'   ,'*'))
    # Address to bind 0MQ socket - used only with proxy/worker configuration
    CONFIG.set('zmq', 'bindaddr'     , getenv('QGSRV_ZMQ_INADDR'   ,'tcp://${zmq:hostaddr}:18080'))
    # Address to bind broadcast address to - used only with proxy/worker configuration
    CONFIG.set('zmq', 'broadcastaddr', getenv('QGSRV_ZMQ_BROADCASTADDR','tcp://${zmq:hostaddr}:18090'))
    # Address to bind cache observer - used only with proxy/worker configuration
    CONFIG.set('zmq', 'cache_observer_addr', getenv('QGSRV_ZMQ_CACHEOBSERVERADDR','tcp://${zmq:hostaddr}:18091'))

    #
    # Monitoring (AMQP)
    #
    CONFIG.add_section('monitor:amqp')
    CONFIG.set('monitor:amqp','routing_key', getenv('AMQP_ROUTING',''))
    CONFIG.set('monitor:amqp','host'       , getenv('AMQP_HOST','amqp'))
    CONFIG.set('monitor:amqp','user'       , getenv('AMQP_USER',''))
    CONFIG.set('monitor:amqp','vhost'      , getenv('AMQP_VHOST','/'))
    CONFIG.set('monitor:amqp','port'       , getenv('AMQP_PORT','5672'))
    CONFIG.set('monitor:amqp','exchange'   , getenv('AMQP_EXCHANGE','qgis_log'))
    # Beware that a too small reconnect delay 
    # may prevent other asynchronous tasks to run
    CONFIG.set('monitor:amqp','reconnect_delay', getenv('AMQP_RECONNECT_DELAY','5'))

    #
    # Management 
    #
    CONFIG.add_section('management')
    CONFIG.set('management','enabled'    , getenv('QGSRV_MANAGEMENT_ENABLED','no'))
    CONFIG.set('management','interfaces' , getenv('QGSRV_MANAGEMENT_INTERFACES', '127.0.0.1'))
    CONFIG.set('management','ssl'        , getenv('QGSRV_MANAGEMENT_SSL','no'))
    CONFIG.set('management','ss_key'     , getenv('QGSRV_MANAGEMENT_SSL_KEY' ,''))
    CONFIG.set('management','ssl_cert'   , getenv('QGSRV_MANAGEMENT_SSL_CERT',''))
    CONFIG.set('management','port'       , getenv('QGSRV_MANAGEMENT_PORT','19876'))
 
    #
    # Metadata
    #
    CONFIG.add_section('metadata')
    CONFIG.set('metadata', 'contact_name', '3liz')
    CONFIG.set('metadata', 'contact_address', '')
    CONFIG.set('metadata', 'contact_email', 'info@3liz.com')
    CONFIG.set('metadata', 'contact_url', 'https://www.3liz.com/')
    CONFIG.set('metadata', 'licence_url', 'http://mozilla.org/MPL/2.0/')
    CONFIG.set('metadata', 'licence_name','Mozilla Public Licences, v2.0')
    CONFIG.set('metadata', 'external_doc_description','Py-qgis-wps server documentation')
    CONFIG.set('metadata', 'external_doc_url','https://docs.3liz.org/py-qgis-wps/')

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


def configure_qgis_api( name: str ) -> None:
    """ Configure qgis service environnement variables
    """
    section = f"api:{name}"
    if not CONFIG.has_section(section):
        return

    config = CONFIG[section]
    for k,v in config.items():
        LOGGER.debug("configuring qgis api '%s': %s = %s", name, k, v) 
        os.environ[k] = v


def qgis_api_endpoints(enabled_only: bool=True) -> Iterable[Tuple[str,str]]:
    """ Return the list of enabled services
    """
    endpoints = CONFIG["api.endpoints"]
    enabled   = CONFIG["api.enabled"] 
    items     = ((name,endpoint) for name,endpoint in endpoints.items())
    if enabled_only:
        items = filter(lambda item: enabled.getboolean(item[0]),items) 
    return items
        

#
# Published services
#

NO_DEFAULT=object()

# Chars that are to be replaced in env variable name
ENV_REPLACE_CHARS=':.-@#$%&*'

@componentmanager.register_factory('@3liz.org/config-service;1')
class ConfigService:
    """ Act as a proxy
    """ 

    def __init__(self):
        self.allow_env = True

    def __get_impl( self, _get_fun, section:str, option:str, fallback:Any = NO_DEFAULT ) -> Any:
        """
        """
        value = _get_fun(section, option, fallback=NO_DEFAULT)
        if value is NO_DEFAULT:
            # Look in environment
            # Note that the section must exists
            if self.allow_env:
                LOGGER.debug("Looking for option '%s.%s' in environment", section, option)
                varname  = 'QGSRV_%s_%s' % (section.upper(), option.upper())
                varname  = functools.reduce( lambda s,c: s.replace(c,'_'), ENV_REPLACE_CHARS, varname)
                varvalue = os.getenv(varname)
                if varvalue is not None:
                    LOGGER.debug("Setting config value from %s", varname)
                    CONFIG.set(section, option, varvalue)
                # Let config parser translate the value for us
                value = _get_fun(section, option, fallback=fallback)
            else:
                value = fallback
        if value is NO_DEFAULT:
            raise KeyError('[%s] %s' % (section,option))
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

    def add_section( self, sectionname:str ) -> None:
        # We do not care if the section already exists
        try:
            CONFIG.add_section( sectionname )
        except configparser.DuplicateSectionError:
            pass



confservice = ConfigService()



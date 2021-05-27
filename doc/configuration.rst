.. _configuration_settings:

Configuration Settings
======================

Configuration can be done either by using a configuration file or with environnement variable.

Except stated otherwise, the rule for environnement variable names is ``QGSRV_<SECTION>_<KEY>`` all in uppercase.


Common Configuration Options
=============================





.. _SERVER_HTTP_PORT:

SERVER_HTTP_PORT
----------------

Port to listen to

:Type: int
:Default: 8080
:Section: server
:Key: port
:Env: QGSRV_SERVER_HTTP_PORT




.. _SERVER_INTERFACES:

SERVER_INTERFACES
-----------------

Interfaces to listen to


:Type: string
:Default: 0.0.0.0
:Section: server
:Key: interfaces
:Env: QGSRV_SERVER_INTERFACES




.. _SERVER_TIMEOUT:

SERVER_TIMEOUT
--------------

Set the timeout for Qgis response in seconds. If a Qgis worker takes more than 
the corresponding value a timeout error (504) is returned to the client. 


:Type: int
:Default: 20
:Section: server
:Key: timeout
:Env: QGSRV_SERVER_TIMEOUT




.. _SERVER_WORKERS:

SERVER_WORKERS
--------------

The number of workers for processing requests

:Type: int
:Default: 2
:Section: server
:Key: workers
:Env: QGSRV_SERVER_WORKERS




.. _SERVER_ENABLE_FILTERS:

SERVER_ENABLE_FILTERS
---------------------

Enable filters as python extension

:Type: boolean
:Default: yes
:Section: server
:Key: enable_filters
:Env: QGSRV_SERVER_ENABLE_FILTERS




.. _SERVER_HTTP_PROXY:

SERVER_HTTP_PROXY
-----------------

Indicates that the server is behind a reverse proxy

:Type: boolean
:Default: no
:Section: server
:Key: http_proxy
:Env: QGSRV_SERVER_HTTP_PROXY




.. _SERVER_PROXY_URL:

SERVER_PROXY_URL
----------------

The url that must be seen by the client when the server is behind a proxy.



:Type: string
:Section: server
:Key: proxy_url
:Env: QGSRV_SERVER_PROXY_URL




.. _SERVER_RESTARTMON:

SERVER_RESTARTMON
-----------------

The file to watch for restarting workers. When the modified date of the file is changed.
a restart command is broadcasted to the workers. Note that workers processes are restarted 
without dropping requests.


:Type: path
:Section: server
:Key: restartmon
:Env: QGSRV_SERVER_RESTARTMON




.. _SERVER_PLUGINPATH:

SERVER_PLUGINPATH
-----------------

The path to qgis server plugins

:Type: path
:Section: server
:Key: pluginpath
:Env: QGSRV_SERVER_PLUGINPATH




.. _SERVER_SSL:

SERVER_SSL
----------

Enable SSL endpoint

:Type: boolean
:Default: no
:Section: server
:Key: ssl
:Env: QGSRV_SERVER_SSL




.. _SERVER_SSL_CERT:

SERVER_SSL_CERT
---------------

Path to the SSL certificat file

:Type: path
:Section: server
:Key: ssl_cert
:Env: QGSRV_SERVER_SSL_CERT




.. _SERVER_SSL_KEY:

SERVER_SSL_KEY
--------------

Path to the SSL key file

:Type: path
:Section: server
:Key: ssl_key
:Env: QGSRV_SERVER_SSL_KEY




.. _SERVER_CROSS_ORIGIN:

SERVER_CROSS_ORIGIN
-------------------

Allows any origin for CORS. If set to 'no', allow only CORS for the 'Origin'
header.


:Type: boolean
:Section: server
:Key: cross_origin
:Env: QGSRV_SERVER_CROSS_ORIGIN




.. _LOGGING_LEVEL:

LOGGING_LEVEL
-------------

Set the logging level

:Type: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
:Default: DEBUG
:Section: logging
:Key: level
:Env: QGSRV_LOGGING_LEVEL




.. _CACHE_SIZE:

CACHE_SIZE
----------

The maximal number of Qgis projects held in cache. The cache strategy is LRU.


:Type: int
:Default: 10
:Section: projects.cache
:Key: size
:Env: QGSRV_CACHE_SIZE




.. _CACHE_ROOTDIR:

CACHE_ROOTDIR
-------------

The directory location for Qgis project files.


:Type: path
:Section: projects.cache
:Key: rootdir
:Env: QGSRV_CACHE_ROOTDIR




.. _CACHE_STRICT_CHECK:

CACHE_STRICT_CHECK
------------------

Activate strict checking of project layers. When enabled, Qgis projects
with invalid layers will be dismissed and an 'Unprocessable Entity' (422) HTTP error
will be issued.


:Type: boolean
:Default: yes
:Section: projects.cache
:Key: strict_check
:Env: QGSRV_CACHE_STRICT_CHECK




.. _CACHE_INSECURE:

CACHE_INSECURE
--------------

Enable or disable the insecure cache mode. The insecure cache mode allow scheme handlers
to enable or disable some features considered harmful. See the handler's description
for the limitations induced in secure mode.


:Type: boolean
:Default: no
:Section: projects.cache
:Key: insecure
:Env: QGSRV_CACHE_INSECURE




.. _TRUST_LAYER_METADATA:

TRUST_LAYER_METADATA
--------------------

Trust layer metadata. Improves layer load time by skipping expensive checks 
like primary key unicity, geometry type and 
srid and by using estimated metadata on layer load. Since QGIS 3.16.


:Type: boolean
:Default: no
:Version Added: 1.4
:Section: projects.cache
:Key: trust_layer_metadata
:Env: QGSRV_TRUST_LAYER_METADATA
:Alternate name: QGIS_SERVER_TRUST_LAYER_METADATA




.. _DISABLE_GETPRINT:

DISABLE_GETPRINT
----------------

Don't load print layouts. Improves project read time if layouts are not required, 
and allows projects to be safely read in background threads (since print layouts are 
not thread safe).


:Type: boolean
:Default: no
:Version Added: 1.4
:Section: projects.cache
:Key: disable_getprint
:Env: QGSRV_DISABLE_GETPRINT
:Alternate name: QGIS_SERVER_DISABLE_GETPRINT




.. _CACHE_PRELOAD_CONFIG:

CACHE_PRELOAD_CONFIG
--------------------

Path to configuration file for preloading projects. The file must have one project uri 
per line. Each uri is similar to the project uri passed in the 'MAP' query parameter
of OWS requests.


:Type: path
:Version Added: 1.4
:Section: projects.cache
:Key: preload_config
:Env: QGSRV_CACHE_PRELOAD_CONFIG




.. _CACHE_DISABLE_OWSURLS:

CACHE_DISABLE_OWSURLS
---------------------

Disable ows urls defined in projects. This may be necessary because Qgis projects
urls override proxy urls.


:Type: boolean
:Default: no
:Version Added: 1.5.4
:Section: projects.cache
:Key: disable_owsurls
:Env: QGSRV_CACHE_DISABLE_OWSURLS




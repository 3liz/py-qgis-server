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
Note that this option will be overidden by `QGIS_SERVER_<SERVICE>_URL` or 
by `X-Qgis-<service>-Url` headers.



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
:Alternate name: QGIS_PLUGINPATH




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
:Default: no
:Section: server
:Key: cross_origin
:Env: QGSRV_SERVER_CROSS_ORIGIN




.. _SERVER_MEMORY_HIGH_WATER_MARK:

SERVER_MEMORY_HIGH_WATER_MARK
-----------------------------

Set memory high water mark as fraction of total memory. Workers are 
restarted if total memory percent usage of workers exceed that value.


:Type: float
:Default: 0.9
:Version Added: 1.8.0
:Section: server
:Key: memory_high_water_mark
:Env: QGSRV_SERVER_MEMORY_HIGH_WATER_MARK




.. _SERVER_GETFEATURELIMIT:

SERVER_GETFEATURELIMIT
----------------------

Define default limit for WFS/GetFeature requests.
A negative value set no limit; this may be a concern
with requests returning a high number of values.


:Type: int
:Default: -1
:Version Added: 1.8.1
:Section: server
:Key: getfeaturelimit
:Env: QGSRV_SERVER_GETFEATURELIMIT




.. _LOGGING_LEVEL:

LOGGING_LEVEL
-------------

Set the logging level

:Type: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
:Default: DEBUG
:Section: logging
:Key: level
:Env: QGSRV_LOGGING_LEVEL




.. _QGIS_INFO:

QGIS_INFO
---------

Log out qgis 'Info' message logs

:Type: boolean
:Default: no
:Section: logging
:Key: level
:Env: QGSRV_QGIS_INFO




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
Preloaded projects are stored in a static cache, i.e they are not subject to lru eviction. 


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




.. _CACHE_FORCE_ETAG:

CACHE_FORCE_ETAG
----------------

Force etag header even if 'TRUST_LAYER_METADATA' is not set.
By default etags are set only when 'TRUST_LAYER_METADATA' is set because
capabilities rely only on qgis project data and not on the underlying layer
data. 


:Type: boolean
:Default: no
:Version Added: 1.7.13
:Section: projects.cache
:Key: force_etag
:Env: QGSRV_CACHE_FORCE_ETAG




.. _CACHE_DEFAULT_HANDLER:

CACHE_DEFAULT_HANDLER
---------------------

Set the default handler for MAP parameters


:Type: string
:Section: projects.cache
:Key: preload_config
:Env: QGSRV_CACHE_DEFAULT_HANDLER




.. _CACHE_ALLOW_STORAGE_SCHEMES:

CACHE_ALLOW_STORAGE_SCHEMES
---------------------------

Restrict authorized project storage scheme for projects uri to
those listed - The value must be a comma separated list of allowed
schemes. The value '*' allow any scheme.
Note that aliases are resolved before applying restrictions.


:Type: str
:Default: \*
:Section: projects.cache
:Key: allow_storage_schemes
:Env: QGSRV_CACHE_ALLOW_STORAGE_SCHEMES




.. _CACHE_CHECK_INTERVAL:

CACHE_CHECK_INTERVAL
--------------------

Set the time interval in seconds between two check for invalidation/refresh of the cache content.
If set to a value > 0 then the cache is checked for invalidation/refresh asynchronously every 
seconds defined by the option.
If set to 0 (or negative value), the cache is checked for invalidation synchronously at each request. 
When set to 0 with slow projects to load, user may experience latency, so it is recommended
to use asynchronous check with such projects in conjunction with a static cache.


:Type: int
:Section: projects.cache
:Key: refresh_interval
:Env: QGSRV_CACHE_CHECK_INTERVAL




.. _API_ENABLED_LANDING_PAGE:

API_ENABLED_LANDING_PAGE
------------------------

Enable access to qgis 'landing page' api


:Type: boolean
:Default: no
:Version Added: 1.7.2
:Section: api.enabled
:Key: landing_page
:Env: QGSRV_API_ENABLED_LANDING_PAGE




.. _API_ENDPOINTS_LANDING_PAGE:

API_ENDPOINTS_LANDING_PAGE
--------------------------

Define endpoint access to the 'landing page' service


:Type: str
:Default: /ows/catalog
:Version Added: 1.7.2
:Section: api.endpoints
:Key: landing_page
:Env: QGSRV_API_ENDPOINTS_LANDING_PAGE




.. _MANAGEMENT_ENABLED:

MANAGEMENT_ENABLED
------------------

Activate management API service. The management API is REST api for controlling and inspecting
the server behavior, plugins and cached projects.
Starting from 1.7.0, this is a experimental feature and will be subject to change. The api will
be considered as 'stable' from the 1.8.0 version.


:Type: boolean
:Default: no
:Version Added: 1.7.0
:Section: management
:Key: enabled
:Env: QGSRV_MANAGEMENT_ENABLED




.. _MANAGEMENT_INTERFACES:

MANAGEMENT_INTERFACES
---------------------

Network interfaces to listen to. The management API service will listen on this interface



:Type: string
:Default: 127.0.0.1
:Version Added: 1.7.0
:Section: management
:Key: interfaces
:Env: QGSRV_MANAGEMENT_INTERFACES




.. _MANAGEMENT_PORT:

MANAGEMENT_PORT
---------------

Port to listen to

:Type: int
:Default: 19876
:Section: management
:Key: port
:Env: QGSRV_MANAGEMENT_PORT




.. _MANAGEMENT_SSL:

MANAGEMENT_SSL
--------------

Enable SSL endpoint for API management

:Type: boolean
:Default: no
:Section: management
:Key: ssl
:Env: QGSRV_MANAGEMENT_SSL




.. _MANAGEMENT_SSL_CERT:

MANAGEMENT_SSL_CERT
-------------------

Path to the SSL certificat file for the management API

:Type: path
:Section: management
:Key: ssl_cert
:Env: QGSRV_MANAGEMENT_SSL_CERT




.. _MANAGEMENT_SSL_KEY:

MANAGEMENT_SSL_KEY
------------------

Path to the SSL key file for the management API

:Type: path
:Section: management
:Key: ssl_key
:Env: QGSRV_MANAGEMENT_SSL_KEY




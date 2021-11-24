.. _cache:

Cache
=====

Py-qgis-server has two cache for Qgis projects: a LRU cache and a Static cache.

.. _lru_cache:

LRU cache
---------

The lru cache store projects and use a lru (last-recent-use) eviction scheme. This cache has a fixed size controlled by the :ref:`CACHE_SIZE` configuration setting.

The lru cache will prevent to bloat the memory with too many projects (remember that projects are loadedin memory for each worker).

If you have many project that are accessed frequently then you may experience many eviction/reloading. This may be not desirable with big projects that may take long loading time, in this situation you may consider using the static cache.

.. _static_cache:

Static cache
------------

The static cache is not subject to LRU eviction and has no limitation in the number of project you may store.

Projects stored in the static cache are preloaded at startup from a configuration file.  
The file must have one project uri per line. Each uri is similar to the project uri passed in the 'MAP' query parameter of OWS requests.

The path of the cache configuration file is given in the :ref:`CACHE_PRELOAD_CONFIG` configuration seting. 



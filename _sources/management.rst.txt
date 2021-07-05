.. _management_api:

Management API (experimental)
=============================

The management API is a REST api for inspecting the server state and controlling some of the server
behavior. 

Starting from version 1.7.0, this is an **experimental** feature and it will be subject to change.
The api will be considered as *stable* from the 1.8.0 version.

.. _plugins_api:

Plugins API
-----------

The *plugins* api enable inspecting and managing Qgis server plugins.  

* :http:get:`/plugins/(name)`


 .. http:get:: /plugins/(name)

    Return plugin status from its name `name`

    If `name` is not given, return a summary of plugins that the worker has attempted to load 

    :statuscode 200: no error
    :statuscode 404: the plugin does not exists

    **example**:

    .. sourcecode:: http

       GET /plugins/myplugin HTTP/1.1
       Host: example.com
       Accept: application/json

    **response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: *
       Content-Type: application/json    

       {
         "metadata": {
            "general": {
                "author": "3liz",
                "description": "Test plugin",
                "email": "",
                "name": "myplugin",
                "qgisminimumversion": "3.0",
                "server": "True",
                "version": "1.0.0",
            },
            "path"   : "/plugins/myplugin/__init__.py"
         },
         "name": "myplugin",
         "status": "loaded"
       }


.. _cache_api:

Cache API
---------

The *cache* api allow qgis project introspection

* :http:get:`/cache/(project_uri)`


 .. http:get:: /cache/(project_uri)

    Return the project informations 

    :statuscode 200: no error
    :statuscode 404: the project does not exists

    **example**:

    .. sourcecode:: http

       GET /cache/myproject HTTP/1.1
       Host: example.com
       Accept: application/json

    **response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: *
       Content-Type: application/json    

       {
         "bad_layers_count": 0,
         "cache_key": "myproject",
         "crs": "EPSG:4326 - WGS 84",
         "last_modified": "2021-06-24T08:04:26",
         "layers" : [
            {
                "crs": "EPSG:4326 - WGS 84",
                "id": "myproject_8d8d649f_7748_43cc_8bde_b013e17ede29",
                "name": "my project layer",
                "source": "/src/tests/data/myproject/myproject.shp"
            }
         ]
       }


.. _pool_api:

Pool API
--------

The *pool* api allow inspecting workers and projects cache associated to them.

* :http:get:`/pool/`
* :http:post:`/pool/restart`


 .. http:get:: /pool/

    Return the list of worker state and the cache for each of them.

    :statuscode 200: no error

    **example**:

    .. sourcecode:: http

       GET /cache/pool/ HTTP/1.1
       Host: example.com
       Accept: application/json

    **response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: *
       Content-Type: application/json    

       {
         "num_workers": 2, 
         "workers": [
             {
               "cache": [
                 {
                   "filename": 
                   "/tests/data/myporject.qgs", 
                   "key": "myproject", 
                   "last_modified": "2021-06-24T08:04:26", 
                   "link": "http://localhost:19876/cache/myproject", 
                   "num_layers": 1
                 }
               ], 
               "mem_percent": 0.4297396825334563, 
               "mem_usage": 143597568, 
               "pid": 34
             },
             {
               "cache": [], 
               "mem_percent": 0.41044564806749534, 
               "mem_usage": 137150464, 
               "pid": 31
             }
         ]
       }

 .. http:post:: /pool/restart

    Restart workers gracefully.

    :statuscode 200: no error

    
.. _qgis_api:

Qgis API
---------

The `/qgis/` api endpoint is a passthrough for accessing directly the Qgis server api and services. Some services may install some management api that will be accessible from this endpoint.


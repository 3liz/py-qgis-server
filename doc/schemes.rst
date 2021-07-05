.. _loader_schemes:

Loader schemes
==============

Py-qgis-server support custom loaders schemes definitions

Qgis projects path are passed in the ``MAP`` query parameter of the request. By default this parameter
is interpreted as an url.

If no scheme is specified, the ``MAP`` parameter is interpreted as a file path relative to the ``CACHE_ROOTDIR`` setting and is 
handled with the ``file`` protocol handler.

.. _default handlers:

Default handlers
================

Py-qgis-server supports natively the following default schemes:

.. _file_protocol:

File protocol
-------------

Handle projects file stored on local media. The ``file:`` protocol is aliased by default for using
the ``CACHE_ROOTDIR`` as base path for when looking for projects.

:Secure mode: No special limitation


.. _postgres_protocol:

Postgres protocol
-----------------

The `postgres` protocol handle file stored in postgres database as supported by Qgis.

:Secure mode: Only ``dbname``, ``schema``, ``authcfg`` and ``service`` query params are allowed.
              Only the ``user@`` in the netloc part is allowed.


.. _scheme_aliases:

Scheme aliases
===============

Py-qgis-server allow defining custom scheme as scheme aliases. Scheme aliases defines base urls
for existing schemes with overrides rules on path and query params:

Schemes aliases are defined by adding the scheme definition in the ``projects.schemes`` section::

    [projects.schemes]
    my_relative_scheme=file:relative/path/
    my_absolute_scheme=file:/absolute/path/

.. note::

    The trailing ``/`` is important for the substitution rules. Otherwise
    the path will interpreted as a base name which is not what you usually want.


In the previous exemple, the ``MAP=my_relative_scheme:myproject`` will be substituted with ``file:relative/path/myproject``
and searched relatively to the ``CACHE_ROOTDIR`` option. 

On the other hand, the ``MAP=my_absolute_scheme:myproject`` will be substituted with ``file:/absolute/path/myproject``
and the file will be searched at ``/absolute/path/myproject.qgs``

Important notes:

* For security reason, only file path defined from alias may be absolute path: all paths used 
  in the request parameters will be interpreted as *relative* path.

* Query parameters defined in the alias scheme take precedence over the query parameters from the ``MAP`` parameter.

  There is a special exception when using the ``{path}`` expression in the target of alias: only the path of the alias URL
  will be used in the target url.

  i.e, with the following definition::
        
        [projects.schemes]
        postgres=postgres:///?service=myservice&project={path}

  Enable you to protect the `postgres` scheme from any parameter injection, only the path of the original url will be used. 

* Target of alias cannot be alias

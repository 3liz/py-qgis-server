.. _expose_qgis_api:

Expose Qgis Api
===============

Qgis server enable defining `custom api <https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/server.html#custom-apis>`_.

Py-qgis-server allow you to control public access to the qgis services apis while still allowing access
throught the management api.

This may be useful if you plan to have some api doing some backoffice management and do not want these api beeing accessed
publicly.

.. _api_endpoints:

Api endpoint
-----------------

Apis may be accessed by the management api by configuring the api endpoint::

    [api.endpoints]
    <api_name>=/endpoint

The endpoint should match the root path of the api as defined in the `qgis server api entrypoint <https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/server.html#custom-apis>`_


.. _enabling_api:

Enabling api public access
-------------------------------

Apis are publicly enabled with the following configuration::
    
    [api.enabled]
    <api_name>=yes


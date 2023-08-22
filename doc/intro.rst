.. highlight:: python
.. highlight:: sh

.. _server_description:

Description
===========

Py-qgis-server is a asynchronous HTTP Qgis server written in python on top of the `tornado <http://www.tornadoweb.org/en/stable/>`_ framework and the 0MQ messaging framework for distributing requests workers.

It is based on the new Qgis 3 server API for efficiently passing requests/responses using 0MQ messaging framework to workers.

The server may be run as a self-contained single service or as a proxy server with an arbitrary number of workers running
remotely or locally. Independent workers connect automatically to the front-end proxy with no need of special configuration
on the proxy side. Thus, this is ideal for auto-scaling configuration for use with container orchestrator as Rancher, Swarm or Kubernetes.

The server is aimed at solving some real situations encountered in production environment: zero conf scalability, handle long-running request situation, auto restart...


.. _server_features:

Features
--------

- Multiples workers
- Fair queuing request dispatching
- Timeout for long running/stalled requests
- Full support of qgis server plugins
- Auto-restart trigger for workers
- Support streamed/chunked responses
- SSL support


.. _server_requirements:

Requirements
------------

- OS: Unix/Posix variants (Linux or OSX) (Windows not officially supported)
- Python >= 3.5
- QGIS >= 3.10 installed
- libzmq >= 4.0.1 and pyzmq >= 17


.. _server_installation:

Installation
============


.. _server_source_install:

Install from source
-------------------

* Install from pypi.org::

    pip install py-qgis-server

* Install from sources::

    pip install -e .

* Install from build version X.Y.Z::

    make dist
    pip install py-qgis-server-X.Y.Z.tar.gz


.. _server_running:

Running the server
==================

The server does not run as a daemon by itself, there is several way to run a command as a daemon.

For example:

* Use `Supervisor <http://supervisord.org/>`_. Will gives you full control over logs and server status notifications.
* Use the ``daemon`` command.
* Use systemd
* ...

Synopsis
--------

**qgisserver** [*options*]


Options
-------

.. program: qgisserver

.. option:: -d, --debug

    Force debug mode. This is the same as setting the :ref:`LOGGING_LEVEL <LOGGING_LEVEL>` option to ``DEBUG``

.. option:: -c, --config path

    Use the configuration file located at ``path``

.. option:: --proxy

    Run only as proxy.


Running proxy and workers separately
------------------------------------

If the ``--proxy`` option is set  the server will act as a proxy server to talk to independent qgis workers.

QGIS workers can be run using the command:

**qgisserver-worker** [*options*]

The options are the same as


.. _server_docker_running:

Running with Docker
-------------------

Docker image is available on `docker-hub <https://hub.docker.com/r/3liz/qgis-map-server>`_.

All options are passed with environment variables. See the :ref:`Configuration settings <configuration_settings>`
for a description of the options.


.. _install_plugin:

Install server plugins with the Docker container
------------------------------------------------

The docker image is shipped with the `qgis-plugin-manager <https://www.3liz.com/news/qgis-plugin-manager.html>`_.

To install or manage your server plugins, use the docker `exec` command into your container, the plugins will install in the folder defined by the :ref:`SERVER_PLUGINPATH <SERVER_PLUGINPATH>` option.

Example::

    docker exec myserver -it qgis-plugin-manager install "Lizmap server"

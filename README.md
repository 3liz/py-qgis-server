# QGIS embbeded WMS/WFS/WCS asynchronous scalable server.

## Description

This is a asynchronous HTTP Qgis server written in python on top of the [tornado](http://www.tornadoweb.org/en/stable/) framework and the
0MQ messaging framework for distributing requests workers.

It is based on the new Qgis 3 server API for efficiently passing requests/responses using 0MQ messaging framework to workers.

The server may be run as a self-contained single service or as a proxy server with an arbitrary number of workers running
remotely or locally. Independant workers connect automatically to the front-end proxy with no need of special configuration
on the proxy side. Thus, this is ideal for auto-scaling configuration for use with container orchestrator as Rancher, Swarm or Kubernetes.

The server is aimed at solving some real situations encountered in production environment: zero conf scalability, handle long-running request situation, auto restart...

## Features

- Multiples workers
- Fair queuing request dispatching
- Timeout for long running/stalled requests
- Full support of qgis server plugins
- Auto-restart trigger for workers
- Support streamed/chunked responses 
- SSL support
- Support for access control extensions
- Support for Qgis project stored in postgres database
- Support adding new projects cache handlers as python extension 
- Preloading of Qgis projects.

## Requirements:

- OS: Unix/Posix variants (Linux or OSX) (Windows not officialy supported)
- Python >= 3.5
- QGIS > 3.0 installed
- Some python knowledge about python virtualenv and package installation.
- libzmq >= 4.0.1 and pyzmq >= 17

## Documentation:

Latest documentation is available on [ReadTheDoc](https://py-qgis-server.readthedocs.io/en/latest/index.html)

## Installation

### From docker

Follow the readme in the [docker/](./docker) folder.

### From source 

Install in development mode
```
pip install -e .
```

### Version X.Y.Z From python package archive

```
pip install py-qgis-server-X.Y.Z.tar.gz
```

## Running the server

The server does not run as a daemon by itself, there is several way to run a command as a daemon.

For example:

* Use Supervisor http://supervisord.org/. Will gives you full control over logs and server status notifications.
* Use the `daemon` command.
* Use systemd
* ...


### Running the server

```
usage: qgisserver [-h] [-d] [-c [PATH]]
                  [--version] [-p PORT] [-b IP] [-w NUM] [-j NUM] [-u SETUID]
                  [--rootdir PATH] [--proxy] [--timeout SECONDS]

qgis/HTTP/0MQ scalable server

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           debug mode
  -c [PATH], --config [PATH]
                        Configuration file
  --version             Return version number and exit
  -p PORT, --port PORT  http port
  -b IP, --bind IP      Interface to bind to
  -w NUM, --workers NUM
                        Num workers
  -j NUM, --jobs NUM    Num server instances
  -u SETUID, --setuid SETUID
                        uid to switch to
  --rootdir PATH        Path to qgis projects
  --proxy               Run only as proxy
  --timeout SECONDS     Set client timeout in seconds
```

By default the command will run server instances with workers and use unix sockets to communicate. This can 
be used to run the server as a single command.

#### Running proxy and workers separately

If the `--proxy` option the server will act as a proxy server to talk to independant qgis workers. 

Qgis workers can be run using the command:

```
qgisserver-worker --host=localhost --rootdir=path/to/projects
```


### Requests to OWS services

The OWS requests use the following format:  `/ows/?<ows_query_params>`

Example:

```
http://myserver:8080/ows/?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetCapabilities
```

#### Using with lizmap

In order to use the server with lizmap, you must set the following configuration
in your `lizmapConfig.ini.php`:

```
[services]
wmsServerURL="http://my.domain:<port>/ows/"
...

; Use relative path
relativeWMSPath=true
```

### Configuration

The configuration can be done either as configuration .ini file in or as environment variables.

The precedences of the gonfiguration parameters is the following (from lowest to highest)

- Defaults values
- Environment variables
- Config file
- Command line options

#### Configuration parameters

Please look at [the documentation](https://py-qgis-server.readthedocs.io/en/latest/index.html) for configuration options

## Logging

By default, the server log on stdout/stderr and you have to configure redirection and log rotation 
on your infrastructure environment






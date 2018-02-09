# QGIS embbeded WMS/WFS server in Tornado http server.

## Requirements:

- OS: Unix/Posix variants (Linux or OSX) (Windows not supported)
- Python >= 3.5
- QGIS3 installed
- Some python knowledge about python virtualenv and package installation.

## Installation

*ADVICE*: You always should install in a python virtualenv. If you want to use system packages, setup your environment 
with the `--system-site-packages` option.

See the official documentation for how to setup a python virtualenv:  https://virtualenv.pypa.io/en/stable/. 

### From source 

Install in development mode
```
pip install -e .
```

### From python package archive

```
pip install py-qgis-server-0.1.4.tar.gz
```

## Running the server

The server with a command line interface:

The server does not run as a daemon by itself, there is several way to run a command as a daemon.

For example:

* Use Supervisor http://supervisord.org/. Will gives you full control over logs and server status notifications.
* Use the `daemon` command.


### Usage
```
usage: qgisserver [-h] [--logging {debug,info,warning,error}] [-c [PATH]]
                  [--version] [-p PORT] [-b IP] [-w NUM] [-u SETUID]
                  [--rootdir PATH]

qgis/HTTP/AMQP scalable server

optional arguments:
  -h, --help            show this help message and exit
  --logging {debug,info,warning,error}
                        set log level
  -c [PATH], --config [PATH]
                        Configuration file
  --version             Return version number and exit
  -p PORT, --port PORT  http port
  -b IP, --bind IP      Interface to bind to
  -w NUM, --workers NUM
                        Num workers
  -u SETUID, --setuid SETUID
                        uid to switch to
  --rootdir PATH        Path to qgis projects
```

### Configuration

The configuration can be done either as configuration .ini file in or as environment variables.

The precedences of the gonfiguration parameters is the following (from lowest to highest)

- Defaults values
- Environment variables
- Config file
- Command line options

#### Configuration parameters

Here is a sample config file with the default values and the corresponding env variables

```
[server]
port=8080          # QGSRV_SERVER_HTTP_PORT
interfaces=0.0.0.0 # QGSRV_SERVER_INTERFACES
workers=2          # QGSRV_SERVER_WORKERS 

[logging]
level=DEBUG # QGSRV_LOGGING_LEVEL

[cache]
size=10    # QGSRV_CACHE_SIZE
rootdir=   # QGSRV_CACHE_ROOTDIR
```

## Logging

By default, the server log on stdout/stderr and you have to configure redirection and log rotation 
on your infrastructure environment






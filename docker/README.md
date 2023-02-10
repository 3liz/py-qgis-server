# QGIS 3 map  server

Setup a OGC WWS/WFS/WCS service.

Run the python QGIS server from https://github.com/3liz/py-qgis-server in a docker container.

Versions are published on Docker Hub https://hub.docker.com/r/3liz/qgis-map-server

To know the QGIS version used in an image:
```bash
docker run -it 3liz/qgis-map-server:3.10 version
```
will return the full QGIS version used.

## Quick start 

```
docker run -p 8080:8080 [--user <uid>[:<gid>]] -v /path/to/qgis/projects:/qgis-data 3liz/qgis-map-server
```

## Run example with config

```bash
docker run -p 8080:8080 \
       -v /path/to/qgis/projects:/projects \
       -e QGSRV_SERVER_WORKERS=2 \
       -e QGSRV_LOGGING_LEVEL=DEBUG  \
       -e QGSRV_CACHE_ROOTDIR=/projects \
       -e QGSRV_CACHE_SIZE=10 \
       3liz/qgis-map-server
```

## Requests to OWS services

The OWS requests use the following format:  `/ows/?<ows_query_params>`

Example:

```
http://myserver:8080/ows/?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetCapabilities
```

### Passing MAP arguments

MAP arguments are treated as relative to the location given by  `QYWPS_CACHE_ROOTDIR`

## Configuration

The server is configured via environment variables or configuration file as
described [here](https://github.com/3liz/py-qgis-server/blob/master/README.md#configuration)

### Running the server as specific user 

By default, the server ren as user and group id 9001. The user id may be customized by setting
the `QGSRV_USER` environment variable to the - numerical - user ID of your choice 


### QGIS project Cache configuration

- QGSRV\_CACHE\_ROOTDIR: Absolute path to the qgis projects root directory
- QGSRV\_CACHE\_SIZE: Qgis projects cache size
- QGSRV\_LOGGING\_LEVEL: Logging level (DEBUG,INFO)
- QGSRV\_SERVER\_WORKERS: Number of QGIS server instances

The cache hold projects, if the project timestamp change on disk then the project will be reloaded.

### Xvfb and Display support

Xvfb display support can be activated with `QGSRV_DISPLAY_XVFB=ON` which is the default behavior.

### Plugin path

Plugins can be used from a host mounted volume; use the `QGSRV_SERVER_PLUGINPATH` environment
variables to set the path inside the container.

### Pass QGIS environment variables 

You may pass QGIS server environment variables by defining them as docker environment variables.

Useful variables are:

```
QGIS_OPTIONS_PATH              # Path to look for qgis settings ini file
QGIS_SERVER_PARALLEL_RENDERING # Enable/Disable QGIS_SERVER_PARALLEL_RENDERING (default to false)
QGIS_SERVER_MAX_THREADS        # Max num rendering threads (per processes) - default unlimited
QGIS_SERVER_WMS_MAX_HEIGHT     # Maximum height for a WMS request - default not set
QGIS_SERVER_WMS_MAX_WIDTH      # Maximum width for a WMS request  - default not set
```

## Using with Lizmap

In order to use the server with Lizmap, you must set the following configuration
in your `lizmapConfig.ini.php`:

```ini
[services]
wmsServerURL="http://my.domain:<port>/ows/"
...

; Use relative path
relativeWMSPath=true
```

## Notes

* GeoPackages is not multiprocessing friendly and are not working well with read-only volumes.
Avoid them if you intend to use your data with read-only volumes.
* Qgis requires Qt5  minimum, there is [known issues](https://askubuntu.com/questions/1034313/ubuntu-18-4-libqt5core-so-5-cannot-open-shared-object-file-no-such-file-or-dir) with too old kernel. As a matter of fact, you should use a kernel 4.19 or superior.

# Changelog

<!--
All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).
-->

## Unreleased

## 1.9.6 - 2025-06-10

### Added

* Enable debug logging on specific request

## 1.9.5 - 2025-03-17

* Change worker OOM handling strategy
* Log incoming request id in worker

## 1.9.4 - 2025-03-15

### Added

* Log request id for all output logs

## 1.9.3 - 2025-01-24

### Added

* Support for `X-Request-Id` header

## 1.9.2 - 2024-11-07

### Fixed

* Fix WFS3 GeoJSON support and feature url support
    - https://github.com/3liz/py-qgis-server/pull/76/files

## 1.9.1 - 2024-09-27

### Added

* Restore support for python 3.8/3.9

## 1.9.0 - 2024-09-27

### Removed

* Remove support for QGIS < 3.28
* Remove dependency on Docker 3liz/qgis-platform image for tests.
* Remove deprecated features for 1.9+

### Added

* Use Mypy and Ruff for lint and typecheck
* Mark QGIS plugin package

### Fixed 

* Fix `cross_origin` documentation according to the actual 
  default value
* Pass Accept Header to properly handle WFS3 requests
    - https://github.com/3liz/py-qgis-server/pull/75

## 1.8.8 - 2023-04-04

### Added

* Add documentation for `SERVER_ALLOW_HEADERS` config option.
* Supports for header 'Access-Control-Allow-Headers'='Authorization' in OPTIONS method, 
  is required if the request has an Authorization header (04/04/2023, contribution from @TANK2003)

### Fixed

* Docker: Fix removing Xvfb lock file when running with `QGSRV_USER`
    - Display comprehensive message when attempting to restart container
      started with `--user` option.
* Changed '/ows/catalog' default entry point to '/catalog'
* Use request path when logging QGIS request.

## 1.8.7 - 2023-02-10

### Added

* Set default logging mode to INFO instead of DEBUG
* Allow quickstart docker run (https://github.com/3liz/py-qgis-server/issues/55)
    - Support for '--user' option
    - Comprehensive error messages
* Supports for 'X-Forwarded-Host/Forwarded' headers when behind a proxy
* Allow 'X-Qgis-Project' header for passing project path

### Fixed

* Fix code style (PEP8)
* Fix wrong url for documentation link

## 1.8.6 - 2022-12-04

### Fixed

* Fix missing http_proxy in management handler

### Added

* Add informative warning on dangling plugin symlink
  - Fix https://github.com/3liz/py-qgis-server/issues/51
* Allow building docker image from local source

## 1.8.5 - 2022-10-19

### Fixed

* Fix broken file watcher (regression from 1.8.4)

### Changed

* `/ows/wfs3` is now a redirection

## 1.8.4 - 2022-10-08

### Deprecated

* Deprecate `/ows/wfs3/` endpoint in favor of `/wfs3/`
    - `/ows/wfs3/` will be removed in 1.9
* Better logging about plugins
* Configure Lizmap API with a new environment variable `QGSRV_API_ENDPOINTS_LIZMAP=yes`
* Replace calls to `asyncio.get_event_loop()`

## 1.8.3 - 2022-08-02

* Fix for python >= 3.10
    - See https://github.com/3liz/py-qgis-server/pull/43
* Deactivate capabilities options for Qgis >= 3.26.1
    - See https://github.com/qgis/QGIS/pull/49266
* Prune docker environment after running tests
* Fix cache observer initialization

## 1.8.2 - 2022-06-16

* Fix Installation of qgis-plugin-manager

## 1.8.1 - 2022-05-25

* Use qgis-plugin-manager for installing qgis server plugins
    - See https://github.com/3liz/qgis-plugin-manager
* Support `QGIS_PLUGINPATH` environment variable
* Add `getfeaturelimit` config option
    - Set maximum value for WFS/GetFeature requests

## 1.8.0 - 2022-05-16

* Bump version 1.8
* Refactor middleware management
* Root access '/' return 403 instead of 404
* Management api `/cache/` now return the collection of cached projects.
* Add `memory_high_water_mark` configuration option
    - Restart workers gracefully on high memory usage

## 1.7.20 - 2022-05-02

* Fix attribute dereference on undefined response
* Fix invalid url in management cache api

## 1.7.19 - 2022-03-31

* Fix extra argument in logging format string when handling
  worker exception
* Enhanced request metrics returned from workers
* Fix regression in management api
* Fix proxy/worker runtime configuration
   - The configuration was broken since supervision was implemented
* Change entrypoint for access policy extension

## 1.7.18 - 2022-03-04

* Fix regression on response time in monitor response

## 1.7.17 - 2022-03-03

* Output 'version' infos to stdout
* Fix handler arguments when using ACL filters
* Increase cache manager logging verbosity
* Add more information in the `--version` to display all versions related to QGIS Server : GDAL, PROJ, Qt…

## 1.7.16 - 2022-02-16

* Add BAN cache observer
* Fix parameter's case in OGC API requests
   - Fix https://github.com/3liz/py-qgis-server/issues/34
* Implement configurable cache observers
* Add 'Last-Modified' header
* Support Etag in HEAD methods for OWS requests
* Implement configurable monitor backend
* Remove `maxcycle` option.

## 1.7.15 - 2022-02-02

* Install server in venv in docker image
* Ensure that exit code is non-zero on pool failure
* Set option to check for cache invalidation/refresh asynchronously
* Use QgsProjectStorage for unhandled uri schemes
    - This allows support for all QgsProjectStorage extensions
* Add `ALLOW_STORAGE_SCHEMES` configuration for restricting allowed project schemes
* Fix api management:
    - Follow backport for https://github.com/qgis/QGIS/issues/45439
    - Fix regression from static cache implementation

## 1.7.14 - 2022-01-18

* Define explicit `CACHE_DEFAULT_HANDLER` configuration option
* Monitoring: define default routing key as fallback when using dynamic key

## 1.7.13 - 2022-01-03

* Do not require `api:<name>` config section when granting api access
* Compute etag for ows `getcapabilities` requests
* Disable project's WMTSUrl

## 1.7.12 - 2021-12-10

* Fix the wrong tag in Makefile

## 1.7.11 - 2021-12-10

* Fix the release process on https://pypi.org

## 1.7.10 - 2021-12-06

* Add `install-lizmap-plugin` script
* Preloaded files are now stored in static cache
* Minimal support for HEAD requests.

## 1.7.9 - 2021-11-05

* Fix landing page regression (from 1.7.7)

## 1.7.8 - 2021-11-04

* Fix Management API for Qgis >= 3.22
    - See https://github.com/qgis/QGIS/issues/45439
* Fix critical failure handling
* Fix 'cache' api handler
* Do not call 'initQgis' when initialising Qgis server
* [API]: Forward OPTION request to api handlers
* Tests: abort on container exit with proper return code
* Remove claiming support for Qgis 3.10

## 1.7.7 - 2021-09-30

* Configurable forwarded header list
    - Configure whitelist of Header's prefix allowed
      to be forwarded to Qgis api/services
* Add condition when preprocessing POST requests
* Handle `QGIS_PROJECT_FILE` environment variable
    - Return 400 on invalid OWS service request (no Map)

## 1.7.6 - 2021-09-28

* Fix wrong type for AMQP Logger variable `connection_delay`
* Pass `X-Qgis-*` headers
    - Allow custom headers from https://github.com/qgis/QGIS/pull/41333

## 1.7.5 - 2021-09-21

* Fix streamed GetFeature requests
    - Refactor streamed response
    - Allow empty chunk
* Logging: raise from debug to error if invalid layers are found
* Use docker-compose for running tests

## 1.7.4 - 2021-09-07

* Enforce required python version in setup.py
* Fix supports for PUT/DELETE/PATCH/HEAD HTTP methods for qgis API

## 1.7.3 - 2021-08-13

* Fix Qgis server api call in management
* Add specific option for logging qgis info message logs
* Print extended version information
* Use setup.cfg for flake8 options
* Handle 0 length response from qgis server
* Expose Qgis api to public interface:
* Expose landing page (https://github.com/3liz/py-qgis-server/issues/29)

## 1.7.2 - 2021-07-05

* Release on https://pypi.org

## 1.7.1 - 2021-06-30

* Revert bad consistency check for postgres handler

## 1.7.0 - 2021-06-24

* Add management API
* Fix `postgres` protocol (broken in 1.6 branch)
* Add `server:maxcycle` option for controlling worker lifetime
* Log failed requests (allow auditing timeout errors)

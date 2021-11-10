# Changelog

## Unreleased

* Minimal support for HEAD requests.

## 1.7.9 - 2021-11-05

* Fix landing page regression (from 1.7.7)

## 1.7.8 - 2021-11-04

* Fix Managment API for Qgis >= 3.22
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
    - Refactorize streamed response 
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

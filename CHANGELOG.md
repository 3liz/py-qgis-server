# Changelog

## Unreleased

## 1.7.2 - 2021-07-05

* Release on https://pypi.org

## 1.7.1 - 2021-06-30

* Revert bad consistency check for postgres handler

## 1.7.0 - 2021-06-24

* Add management API
* Fix `postgres` protocol (broken in 1.6 branch)
* Add `server:maxcycle` option for controlling worker lifetime
* Log failed requests (allow auditing timeout errors)

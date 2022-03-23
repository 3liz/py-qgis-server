SHELL:=bash
.ONESHELL:
.PHONY: env

# 
#  Makefile for running server in docker containers
#
COMMITID=$(shell git rev-parse --short HEAD)

FLAVOR:=ltr

REGISTRY_URL ?= 3liz
REGISTRY_PREFIX=$(REGISTRY_URL)/

QGIS_IMAGE:=$(REGISTRY_PREFIX)qgis-platform:$(FLAVOR)

WITH_SSL:=no

SERVER_HTTP_PORT:=127.0.0.1:8888
MANAGEMENT_HTTP_PORT:=127.0.0.1:19876

BECOME_USER:=$(shell id -u)

SRCDIR=$(shell realpath ..)

PLUGINPATH:=$(SRCDIR)/tests/plugins

local:
	mkdir -p $$(pwd)/.local  $$(pwd)/.cache

clean:
	rm -rf $$(pwd)/.local $$(pwd)/.cache

PGUSER ?= $(USER)
PGDATABASE ?= $(USER)
PGAPPNAME ?= py-qgis-server-tests

ifdef PGPASSFILE
PGPASSFILE_VOL=-v $(PGPASSFILE):/.pgpass
PGPASSFILE_ENV=-e PGPASSFILE:/.pgpass
endif

ifdef PG_RUN
PG_RUN_VOL=-v $(PG_RUN):/var/run/postgresql
endif

TESTS_CPU_LIMITS:=2.0
TESTS_MEMORY_LIMITS:=2g

REQUEST_TIMEOUT:=20
STRICT_CHECK:=yes
WORKERS:=1
PROJECTPATH:=$(SRCDIR)/tests/data

env: local
	@echo "Creating environment file for docker-compose"
	@cat <<-EOF > .env
		SRCDIR=$(SRCDIR)
		WORKERS=$(WORKERS)
		BECOME_USER=$(BECOME_USER)
		QGIS_IMAGE=$(QGIS_IMAGE)
		USER=$(USER)
		PWD=$(shell pwd)
		PLUGINPATH=$(PLUGINPATH)
		PROJECTPATH=$(PROJECTPATH)
		SERVER_HTTP_PORT=$(SERVER_HTTP_PORT)
		MANAGEMENT_HTTP_PORT=$(MANAGEMENT_HTTP_PORT)
		CPU_LIMITS=$(TESTS_CPU_LIMITS)
		MEMORY_LIMITS=$(TESTS_MEMORY_LIMITS)
		WITH_SSL=$(WITH_SSL)
		PGDATABASE=$(PGDATABASE)
		PGPASSFILE=${PGPASSFILE}
		PGAPPNAME=$(PGAPPNAME)
		PGHOST=$(PGHOST)
		PG_RUN=$(PG_RUN)
		REQUEST_TIMEOUT=$(REQUEST_TIMEOUT)
		STRICT_CHECK=$(STRICT_CHECK)
		PYTEST_ADDOPTS=$(PYTEST_ADDOPTS)
		EOF

test: export RUN_COMMAND=./tests/run_tests.sh
test: env up 

run: export RUN_COMMAND=./tests/run_server.sh
run: up

up:
	docker compose up -V  --remove-orphans --force-recreate --exit-code-from qgis-server

stop:
	docker compose down -v --remove-orphans

#
# Run server with extra services
#
%-run: export RUN_COMMAND=./tests/run_server.sh
%-run:
	docker compose \
	-f docker-compose.yml \
	-f docker-compose.$*.yml up -V --remove-orphans --force-recreate -d

run-proxy: 
	docker compose -f docker-compose.proxy.yml \
		up -V --remove-orphans --force-recreate -d

stop-proxy:
	docker compose -f docker-compose.proxy.yml down -v --remove-orphans



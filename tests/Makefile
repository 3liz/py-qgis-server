SHELL:=bash
.ONESHELL:
.PHONY: env

DEPTH=..

include $(DEPTH)/config.mk

# 
#  Makefile for running server in docker containers
#
FLAVOR:=release

REGISTRY_URL ?= 3liz
REGISTRY_PREFIX=$(REGISTRY_URL)/

QGIS_IMAGE:=$(REGISTRY_PREFIX)qgis-platform:$(FLAVOR)

WITH_SSL:=no

SERVER_HTTP_PORT:=127.0.0.1:8888
MANAGEMENT_HTTP_PORT:=127.0.0.1:19876

BECOME_USER:=$(shell id -u)

SRCDIR=$(topsrcdir)

PLUGINPATH:=$(SRCDIR)/tests/plugins

PGUSER ?= $(USER)
PGDATABASE ?= $(USER)
PGAPPNAME ?= py-qgis-server-tests

TESTS_CPU_LIMITS:=2.0
TESTS_MEMORY_LIMITS:=2g

REQUEST_TIMEOUT:=20
STRICT_CHECK:=yes
WORKERS:=1
PROJECTPATH:=$(SRCDIR)/tests/data

env:
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
		PGPASSFILE=${PGPASSFILE}
		PGAPPNAME=$(PGAPPNAME)
		PGUSER=$(PGAPPNAME)
		PGDATABASE=$(PGDATABASE)
		PG_RUN=$(PG_RUN)
		REQUEST_TIMEOUT=$(REQUEST_TIMEOUT)
		STRICT_CHECK=$(STRICT_CHECK)
		PYTEST_ADDOPTS=$(PYTEST_ADDOPTS)
		COMPOSE_PROJECT_NAME=test-py-qgis-server
		EOF

test: 
	SRCDIR=$(SRCDIR) source tests.env \
	&& export $$(cut -d= -f1 tests.env) \
	&& cd unittests \
	&& pytest -v $(ADDOPTS)

%-test: export RUN_COMMAND=./tests/run_tests.sh
%-test: env
	docker compose \
	-f docker-compose.yml \
	-f docker-compose.$*.yml up -V --quiet-pull --remove-orphans \
		--force-recreate --exit-code-from qgis-server
	docker compose down -v --remove-orphans

run:
	SRCDIR=$(SRCDIR) source tests.env \
	&& export $$(cut -d= -f1 tests.env) \
	&& qgisserver


up: env
	docker compose up -V --quiet-pull  --remove-orphans \
		--force-recreate --exit-code-from qgis-server

stop:
	docker compose down -v --remove-orphans

#
# Run server with extra services
#
%-run: export RUN_COMMAND=./tests/run_server.sh
%-run: env
	docker compose \
	-f docker-compose.yml \
	-f docker-compose.$*.yml up -V --quiet-pull --remove-orphans --force-recreate -d

run-proxy: env
	docker compose -f docker-compose.proxy.yml \
		up -V --quiet-pull --remove-orphans --force-recreate -d

stop-proxy:
	docker compose -f docker-compose.proxy.yml down -v --remove-orphans



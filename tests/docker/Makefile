SHELL:=bash
# 
#  Makefile for running server in docker containers
#
COMMITID=$(shell git rev-parse --short HEAD)

FLAVOR:=ltr

REGISTRY_URL ?= 3liz
REGISTRY_PREFIX=$(REGISTRY_URL)/

QGIS_IMAGE:=$(REGISTRY_PREFIX)qgis-platform:$(FLAVOR)

SERVER_HTTP_PORT:=127.0.0.1:8888
SERVER_HTTPS_PORT:=127.0.0.1:8443

BECOME_USER:=$(shell id -u)

SRCDIR=$(shell realpath ../..)

PLUGINPATH:=$(SRCDIR)/tests/plugins

SCRIPTS=./tests/docker


local:
	rm -rf $$(pwd)/.local
	mkdir -p $$(pwd)/.local  $$(pwd)/.pipcache


PGUSER ?= $(USER)
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

test: local
	echo -n "Restart qgis" > .qgis-restart
	docker run --rm --name qgis-py-server-test-$(FLAVOR)-$(COMMITID) -w /src \
		--cpus $(TESTS_CPU_LIMITS) \
		--memory $(TESTS_MEMORY_LIMITS) \
		-u $(BECOME_USER) \
		-v $(SRCDIR):/src \
		-v $$(pwd)/.local:/.local \
		-v $$(pwd)/.pipcache:/.cache \
		-e USER=$(USER) \
		-e PGUSER=$(PGUSER) \
		-e PGAPPNAME=$(PGAPPNAME) \
		-e PGHOST=$(PGHOST) \
		$(PG_RUN_VOL) \
		$(PGPASSFILE_VOL) \
		$(PGPASSFILE_ENV) \
		-e PGSERVICEFILE=/src/tests/.pg_service.conf \
		-e PIP_CACHE_DIR=/.cache \
		-e QGSRV_PROJECTS_SCHEMES_TEST=/src/tests/data/ \
		-e QGSRV_PROJECTS_SCHEMES_FOO=file:foobar/ \
		-e QGSRV_PROJECTS_SCHEMES_BAR=file:foobar?data={path} \
		-e QGSRV_SERVER_PROFILES=/src/tests/profiles.yml \
		-e QGSRV_SERVER_RESTARTMON=/src/.qgis-restart \
		-e QGSRV_SERVER_HTTP_PROXY=yes \
		-e QGSRV_SERVER_PLUGINPATH=/src/tests/plugins \
		-e QGSRV_CACHE_ROOTDIR=/src/tests/data \
		-e QGIS_OPTIONS_PATH=/src/tests/qgis \
		-e PYTEST_ADDOPTS="$(PYTEST_ADDOPTS)" \
		$(QGIS_IMAGE) $(SCRIPTS)/run_tests.sh


WORKERS:=1

PROJECTS_ROOTDIR:=$(SRCDIR)/tests/data

run: local
	echo -n "Restart qgis" > .qgis-restart
	docker run -it --rm -p $(SERVER_HTTP_PORT):8080 --name qgis-py-server-run-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $(SRCDIR):/src \
		-v $$(pwd)/.local:/.local \
		-v $$(pwd)/server.conf:/server.conf \
		-v $(PLUGINPATH):/plugins \
		-v $$(pwd)/.pipcache:/.cache \
		-v $(PROJECTS_ROOTDIR):/src/tests/data \
		-e PIP_CACHE_DIR=/.cache \
		-e QGSRV_SERVER_WORKERS=$(WORKERS) \
		-e QGSRV_CACHE_ROOTDIR=/src/tests/data \
		-e QGSRV_PROJECTS_SCHEMES_TEST=/src/tests/data/ \
		-e QGSRV_SERVER_PROFILES=/src/tests/profiles.yml \
		-e QGSRV_SERVER_RESTARTMON=/src/.qgis-restart \
		-e QGSRV_SERVER_HTTP_PROXY=yes \
		-e QGSRV_LOGGING_LEVEL=DEBUG \
		-e QGSRV_SERVER_PLUGINPATH=/plugins \
		-e PYTHONWARNINGS=d \
		-e QGIS_OPTIONS_PATH=/src/tests/qgis \
		-e QGSRV_DATA_PATH=/.local/share/qgis-server \
		$(QGIS_IMAGE) $(SCRIPTS)/run_server.sh 


run-https: local
	echo -n "Restart qgis" > .qgis-restart
	docker run -it --rm -p $(SERVER_HTTPS_PORT):8080 --name qgis-py-server-run-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $(SRCDIR):/src \
		-v $$(pwd)/.local:/.local \
		-v $(PLUGINPATH):/plugins \
		-e QGSRV_SERVER_WORKERS=$(WORKERS) \
		-e QGSRV_CACHE_ROOTDIR=/src/tests/data \
		-e QGSRV_PROJECTS_SCHEMES_TEST=/src/tests/data/ \
		-e QGSRV_SERVER_PROFILES=/src/tests/profiles.yml \
		-e QGSRV_SERVER_RESTARTMON=/src/.qgis-restart \
		-e QGSRV_LOGGING_LEVEL=DEBUG \
		-e QGSRV_SERVER_PLUGINPATH=/plugins \
		-e QGSRV_SERVER_SSL=true \
		-e QGSRV_SERVER_SSL_CERT=/src/tests/certs/localhost.crt \
		-e QGSRV_SERVER_SSL_KEY=/src/tests/certs/localhost.key \
		-e PYTHONWARNINGS=d \
		-e QGIS_OPTIONS_PATH=/src/tests/qgis \
		$(QGIS_IMAGE) $(SCRIPTS)/run_server.sh 



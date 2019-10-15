SHELL:=bash
# 
#  Makefile for running server in docker containers
#
COMMITID=$(shell git rev-parse --short HEAD)

FLAVOR:=ltr

ifdef REGISTRY_URL
	REGISTRY_PREFIX=$(REGISTRY_URL)/
endif

QGIS_IMAGE=$(REGISTRY_PREFIX)qgis-platform:$(FLAVOR)

SERVER_HTTP_PORT:=127.0.0.1:8888
SERVER_HTTPS_PORT:=127.0.0.1:8443


BECOME_USER:=$(shell id -u)

ifndef LOCAL_HOME
	LOCAL_HOME=$(shell pwd)
endif

SRCDIR=$(shell realpath ../..)

PLUGINPATH:=$(SRCDIR)/tests/plugins

SCRIPTS=./tests/docker

test:
	mkdir -p $$(pwd)/.local $(LOCAL_HOME)/.cache
	echo -n "Restart qgis" > .qgis-restart
	docker run --rm --name qgis-py-server-test-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $(SRCDIR):/src \
		-v $$(pwd)/.local:/.local \
		-v $(LOCAL_HOME)/.cache:/.cache \
		-e PIP_CACHE_DIR=/.cache \
		-e QGSRV_TEST_PROTOCOL=/src/tests/data \
		-e QGSRV_SERVER_PROFILES=/src/tests/profiles.yml \
		-e QGSRV_SERVER_RESTARTMON=/src/.qgis-restart \
		-e QGSRV_SERVER_HTTP_PROXY=yes \
		-e QGSRV_SERVER_PLUGINPATH=/src/tests/plugins \
		-e QGSRV_CACHE_ROOTDIR=/src/tests/data \
		-e QGIS_OPTIONS_PATH=/src/tests/qgis \
		-e PYTEST_ADDOPTS="$(PYTEST_ADDOPTS)" \
		$(QGIS_IMAGE) $(SCRIPTS)/run_tests.sh


WORKERS:=1

run:
	mkdir -p $$(pwd)/.local $(LOCAL_HOME)/.cache
	echo -n "Restart qgis" > .qgis-restart
	docker run -it --rm -p $(SERVER_HTTP_PORT):8080 --name qgis-py-server-run-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $(SRCDIR):/src \
		-v $$(pwd)/.local:/.local \
		-v $$(pwd)/server.conf:/server.conf \
		-v $(LOCAL_HOME)/.cache:/.cache \
		-v $(PLUGINPATH):/plugins \
		-e PIP_CACHE_DIR=/.cache \
		-e QGSRV_SERVER_WORKERS=$(WORKERS) \
		-e QGSRV_CACHE_ROOTDIR=/src/tests/data \
		-e QGSRV_TEST_PROTOCOL=/src/tests/data \
		-e QGSRV_SERVER_PROFILES=/src/tests/profiles.yml \
		-e QGSRV_SERVER_RESTARTMON=/src/.qgis-restart \
		-e QGSRV_SERVER_HTTP_PROXY=yes \
		-e QGSRV_LOGGING_LEVEL=DEBUG \
		-e QGSRV_SERVER_PLUGINPATH=/plugins \
		-e PYTHONWARNINGS=d \
		-e QGIS_OPTIONS_PATH=/src/tests/qgis \
		-e QGSRV_DATA_PATH=/.local/share/qgis-server \
		$(QGIS_IMAGE) $(SCRIPTS)/run_server.sh 

run-https:
	mkdir -p $$(pwd)/.local $(LOCAL_HOME)/.cache
	echo -n "Restart qgis" > .qgis-restart
	docker run -it --rm -p $(SERVER_HTTPS_PORT):8080 --name qgis-py-server-run-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $(SRCDIR):/src \
		-v $$(pwd)/.local:/.local \
		-v $(LOCAL_HOME)/.cache:/.cache \
		-v $(PLUGINPATH):/plugins \
		-e PIP_CACHE_DIR=/.cache \
		-e QGSRV_SERVER_WORKERS=$(WORKERS) \
		-e QGSRV_CACHE_ROOTDIR=/src/tests/data \
		-e QGSRV_TEST_PROTOCOL=/src/tests/data \
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



# Run rabbitmq as
# docker run -it --rm --name rabbitmq -p 127.0.0.1:5672:5672 -p 127.0.0.1:15672:15672 --net mynet rabbitmq:3.6-management

run-amqp:
	mkdir -p $$(pwd)/.local $(LOCAL_HOME)/.cache
	docker run -it --rm -p $(SERVER_HTTP_PORT):8080 --net mynet --name qgis3-py-server-run-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $(SRCDIR):/src \
		-v $$(pwd)/.local:/.local \
		-v $(LOCAL_HOME)/.cache:/.cache \
		-v $(shell realpath ../py-amqp-client):/amqp_src \
		-e AMQP_HOST=rabbitmq \
		-e AMQP_ROUTING=local.test \
		-e PIP_CACHE_DIR=/.cache \
		-e QGSRV_TEST_PROTOCOL=/src/tests/data \
		-e QGSRV_LOGGING_LEVEL=DEBUG \
		$(QGIS_IMAGE) $(SCRIPTS)/run_server.sh



run-worker:
	mkdir -p $$(pwd)/.local $(LOCAL_HOME)/.cache
	docker run -it --rm --net mynet --name qgis-py-worker-run-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $(SRCDIR):/src \
		-v $$(pwd)/.local:/.local \
		-v $(LOCAL_HOME)/.cache:/.cache \
		-e PIP_CACHE_DIR=/.cache \
		-e QGSRV_TEST_PROTOCOL=/src/tests/data \
		-e QGSRV_LOGGING_LEVEL=DEBUG \
		-e ROUTER_HOST=qgis-py-proxy-run-$(COMMITID) \
		$(QGIS_IMAGE) $(SCRIPTS)/run_worker.sh



# Run proxy in a alpine container with precompiled wheels.
run-proxy:
	mkdir -p $$(pwd)/.local $(LOCAL_HOME)/.cache
	echo -n "Restart qgis" > .qgis-restart
	docker run -it --rm -p $(SERVER_HTTP_PORT):8080 --net mynet --name qgis-py-proxy-run-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $(SRCDIR):/src \
		-v $$(wd)/.local:/.local \
		-v $(LOCAL_HOME)/.cache:/.cache \
		-e PIP_CACHE_DIR=/.cache \
		-e QGSRV_TEST_PROTOCOL=/src/tests/data \
		-e QGSRV_LOGGING_LEVEL=DEBUG \
		-e QGSRV_SERVER_RESTARTMON=/src/.qgis-restart \
		$(QGIS_IMAGE) $(SCRIPTS)/run_proxy.sh 


SHELL:=bash
# 
# qgis server makefile
#

BUILDID=$(shell date +"%Y%m%d%H%M")
COMMITID=$(shell git rev-parse --short HEAD)

BUILDDIR=build
DIST=${BUILDDIR}/dist

MANIFEST=factory.manifest

PYTHON:=python3

ifdef REGISTRY_URL
	REGISTRY_PREFIX=$(REGISTRY_URL)/
endif

FLAVOR:=ltr

QGIS_IMAGE=$(REGISTRY_PREFIX)qgis-platform:$(FLAVOR)

# This is necessary with pytest as long it is not fixed
# see also https://github.com/qgis/QGIS/pull/5337
export QGIS_DISABLE_MESSAGE_HOOKS := 1
export QGIS_NO_OVERRIDE_IMPORT := 1

dirs:
	mkdir -p $(DIST)

manifest:
	echo name=$(shell $(PYTHON) setup.py --name) > $(MANIFEST) && \
		echo version=$(shell $(PYTHON) setup.py --version) >> $(MANIFEST) && \
		echo buildid=$(BUILDID)   >> $(MANIFEST) && \
		echo commitid=$(COMMITID) >> $(MANIFEST)

SERVER_HOST:=localhost:8888

test:
	cd tests && py.test -v --host=$(SERVER_HOST)

PLUGINPATH:=$(shell pwd)/tests/plugins

BECOME_USER:=$(shell id -u)

ifndef LOCAL_HOME
	LOCAL_HOME=$(shell pwd)
endif

docker-test:
	mkdir -p $$(pwd)/.local $(LOCAL_HOME)/.cache
	echo -n "Restart qgis" > .qgis-restart
	docker run --rm --name qgis-py-server-test-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $$(pwd):/src \
		-v $$(pwd)/.local:/.local \
		-v $(LOCAL_HOME)/.cache:/.cache \
		-e PIP_CACHE_DIR=/.cache \
		-e QGSRV_TEST_PROTOCOL=/src/tests/data \
		-e QGSRV_SERVER_PROFILES=/src/tests/profiles.yml \
		-e QGSRV_SERVER_RESTARTMON=/src/.qgis-restart \
		-e QGSRV_SERVER_HTTP_PROXY=yes \
		-e QGSRV_SERVER_PLUGINPATH=/src/tests/plugins \
		-e QGSRV_CACHE_ROOTDIR=/src/tests/data \
		-e PYTEST_ADDOPTS="$(PYTEST_ADDOPTS)" \
		$(QGIS_IMAGE) ./tests/run_tests.sh


WORKERS:=1

docker-run:
	mkdir -p $$(pwd)/.local $(LOCAL_HOME)/.cache
	echo -n "Restart qgis" > .qgis-restart
	docker run -it --rm -p 127.0.0.1:8888:8080 --name qgis-py-server-run-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $$(pwd):/src \
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
		-e PYTHONWARNINGS=d \
		-e QGIS_OPTIONS_PATH=/src/tests/qgis \
		$(QGIS_IMAGE) ./run_server.sh 

docker-run-https:
	mkdir -p $$(pwd)/.local $(LOCAL_HOME)/.cache
	echo -n "Restart qgis" > .qgis-restart
	docker run -it --rm -p 127.0.0.1:8443:8080 --name qgis-py-server-run-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $$(pwd):/src \
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
		$(QGIS_IMAGE) ./run_server.sh 



# Run rabbitmq as
# docker run -it --rm --name rabbitmq -p 127.0.0.1:5672:5672 -p 127.0.0.1:15672:15672 --net mynet rabbitmq:3.6-management

docker-run-amqp:
	mkdir -p $$(pwd)/.local $(LOCAL_HOME)/.cache
	docker run -it --rm -p 127.0.0.1:8888:8080 --net mynet --name qgis3-py-server-run-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $$(pwd):/src \
		-v $$(pwd)/.local:/.local \
		-v $(LOCAL_HOME)/.cache:/.cache \
		-v $(shell realpath ../py-amqp-client):/amqp_src \
		-e AMQP_HOST=rabbitmq \
		-e AMQP_ROUTING=local.test \
		-e PIP_CACHE_DIR=/.cache \
		-e QGSRV_TEST_PROTOCOL=/src/tests/data \
		-e QGSRV_LOGGING_LEVEL=DEBUG \
		$(QGIS_IMAGE) ./run_server.sh



docker-run-worker:
	mkdir -p $$(pwd)/.local $(LOCAL_HOME)/.cache
	docker run -it --rm --net mynet --name qgis-py-worker-run-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $$(pwd):/src \
		-v $$(pwd)/.local:/.local \
		-v $(LOCAL_HOME)/.cache:/.cache \
		-e PIP_CACHE_DIR=/.cache \
		-e QGSRV_TEST_PROTOCOL=/src/tests/data \
		-e QGSRV_LOGGING_LEVEL=DEBUG \
		-e ROUTER_HOST=qgis-py-proxy-run-$(COMMITID) \
		$(QGIS_IMAGE) ./run_worker.sh



# Run proxy in a alpine container with precompiled wheels.
docker-run-proxy:
	mkdir -p $$(pwd)/.local $(LOCAL_HOME)/.cache
	echo -n "Restart qgis" > .qgis-restart
	docker run -it --rm -p 127.0.0.1:8080:8080 --net mynet --name qgis-py-proxy-run-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $$(pwd):/src \
		-v $$(wd)/.local:/.local \
		-v $(LOCAL_HOME)/.cache:/.cache \
		-e PIP_CACHE_DIR=/.cache \
		-e QGSRV_TEST_PROTOCOL=/src/tests/data \
		-e QGSRV_LOGGING_LEVEL=DEBUG \
		-e QGSRV_SERVER_RESTARTMON=/src/.qgis-restart \
		$(QGIS_IMAGE) ./run_proxy.sh 

run:
	qgisserver -b 127.0.0.1 -p 8080 --rootdir=$(shell pwd)/tests/data -w $(WORKERS)

# Build dependencies
wheel-deps: dirs
	pip wheel -w $(DIST) -r requirements.txt

wheel:
	mkdir -p $(DIST)
	$(PYTHON) setup.py bdist_wheel --dist-dir=$(DIST)

deliver:
	twine upload -r storage $(DIST)/*

dist: dirs manifest
	$(PYTHON) setup.py sdist --dist-dir=$(DIST)

clean:
	rm -rf $(BUILDDIR)



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

FLAVOR:=release

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

SERVER_HOST:=localhost:8080

test:
	cd tests && py.test -v --host=$(SERVER_HOST)


BECOME_USER:=$(shell id -u)

ifndef LOCAL_HOME
	LOCAL_HOME=$(shell pwd)
endif

docker-test:
	mkdir -p $(LOCAL_HOME)/.local $(LOCAL_HOME)/.cache
	echo -n "Restart qgis" > .qgis-restart
	docker run --rm --name qgis-py-server-test-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $(shell pwd):/src \
		-v $(LOCAL_HOME)/.local:/.local \
		-v $(LOCAL_HOME)/.cache/pip:/.pipcache \
		-e PIP_CACHE_DIR=/.pipcache \
		-e QGSRV_TEST_PROTOCOL=/src/tests/data \
		-e QGSRV_SERVER_PROFILES=/src/tests/profiles.yml \
		-e QGSRV_SERVER_RESTARTMON=/src/.qgis-restart \
		-e QGSRV_SERVER_HTTP_PROXY=yes \
		-e QGSRV_LOGGING_LEVEL=DEBUG \
		-e QGIS_PLUGINPATH=/src/tests/plugins \
		$(QGIS_IMAGE) ./run_tests.sh


docker-run:
	mkdir -p $(LOCAL_HOME)/.local $(LOCAL_HOME)/.cache
	echo -n "Restart qgis" > .qgis-restart
	docker run -it --rm -p 127.0.0.1:8080:8080 --name qgis-py-server-run-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $(LOCAL_HOME):/src \
		-v $(LOCAL_HOME)/.local:/.local \
		-v $(LOCAL_HOME)/.cache/pip:/.pipcache \
		-e PIP_CACHE_DIR=/.pipcache \
		-e QGSRV_TEST_PROTOCOL=/src/tests/data \
		-e QGSRV_SERVER_PROFILES=/src/tests/profiles.yml \
		-e QGSRV_SERVER_RESTARTMON=/src/.qgis-restart \
		-e QGSRV_LOGGING_LEVEL=DEBUG \
		-e QGIS_PLUGINPATH=/src/tests/plugins \
		-e PYTHONWARNINGS=d \
		$(QGIS_IMAGE) ./run_server.sh


# Run rabbitmq as
# docker run -it --rm --name rabbitmq -p 127.0.0.1:5672:5672 -p 127.0.0.1:15672:15672 --net mynet rabbitmq:3.6-management

docker-run-amqp:
	mkdir -p $(HOME)/.local
	docker run -it --rm -p 127.0.0.1:8080:8080 --net mynet --name qgis3-py-server-run-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $(shell pwd):/src \
		-v $(shell pwd)/.local:/.local \
		-v $(shell pwd)/.cache/pip:/.pipcache \
		-v $(shell realpath ../py-amqp-client):/amqp_src \
		-e AMQP_HOST=rabbitmq \
		-e AMQP_ROUTING=local.test \
		-e PIP_CACHE_DIR=/.pipcache \
		-e QGSRV_TEST_PROTOCOL=/src/tests/data \
		-e QGSRV_LOGGING_LEVEL=DEBUG \
		$(QGIS_IMAGE) ./run_server.sh



docker-run-worker:
	mkdir -p $(HOME)/.local
	docker run -it --rm --net mynet --name qgis-py-worker-run-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $(shell pwd):/src \
		-v $(shell pwd)/.local:/.local \
		-v $(shell pwd)/.cache/pip:/.pipcache \
		-e PIP_CACHE_DIR=/.pipcache \
		-e QGSRV_TEST_PROTOCOL=/src/tests/data \
		-e QGSRV_LOGGING_LEVEL=DEBUG \
		-e ROUTER_HOST=qgis-py-proxy-run-$(COMMITID) \
		$(QGIS_IMAGE) ./run_worker.sh



# Run proxy in a alpine container with precompiled wheels.
docker-run-proxy:
	mkdir -p $(HOME)/.local
	echo -n "Restart qgis" > .qgis-restart
	docker run -it --rm -p 127.0.0.1:8080:8080 --net mynet --name qgis-py-proxy-run-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $(shell pwd):/src \
		-v $(shell pwd)/.local:/.local \
		-v $(shell pwd)/.cache/pip:/.pipcache \
		-e PIP_CACHE_DIR=/.pipcache \
		-e PIP_CACHE_DIR=/.pipcache \
		-e QGSRV_TEST_PROTOCOL=/src/tests/data \
		-e QGSRV_LOGGING_LEVEL=DEBUG \
		-e QGSRV_SERVER_RESTARTMON=/src/.qgis-restart \
		$(QGIS_IMAGE) ./run_proxy.sh 



WORKERS:=1

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



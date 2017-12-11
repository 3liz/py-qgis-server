# 
# qgis server makefile
#

BUILDID=$(shell date +"%Y%m%d%H%M")
COMMITID=$(shell git rev-parse --short HEAD)

PYPISERVER:=storage

BUILDDIR=build
DIST=${BUILDDIR}/dist

MANIFEST=factory.manifest

PYTHON:=python3

ifdef REGISTRY_URL
	REGISTRY_PREFIX=$(REGISTRY_URL)/
endif

QGIS_IMAGE=$(REGISTRY_PREFIX)qgis3-server:latest

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


PIP_CONFIG_FILE:=pip.conf
BECOME_USER:=$(shell id -u)

docker-test:
	mkdir -p $(HOME)/.local
	docker run --rm --name qgis3-py-server-test-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $(shell pwd):/src \
		-v $(HOME)/.local:/.local \
		-v $(HOME)/.config/pip:/.pipconf  \
		-v $(HOME)/.cache/pip:/.pipcache \
		-e PIP_CONFIG_FILE=/.pipconf/$(PIP_CONFIG_FILE) \
		-e PIP_CACHE_DIR=/.pipcache \
		-e QGSRV_TEST_PROTOCOL=/src/tests/data \
		$(QGIS_IMAGE) ./run_tests.sh

docker-run:
	mkdir -p $(HOME)/.local
	docker run -it --rm -p 127.0.0.1:8080:8080 --name qgis3-py-server-run-$(COMMITID) -w /src \
		-u $(BECOME_USER) \
		-v $(shell pwd):/src \
		-v $(HOME)/.local:/.local \
		-v $(HOME)/.config/pip:/.pipconf  \
		-v $(HOME)/.cache/pip:/.pipcache \
		-e PIP_CONFIG_FILE=/.pipconf/$(PIP_CONFIG_FILE) \
		-e PIP_CACHE_DIR=/.pipcache \
		-e QGSRV_TEST_PROTOCOL=/src/tests/data \
		$(QGIS_IMAGE) ./run_setup.sh


WORKERS:=1

run:
	qgisserver -b 127.0.0.1 -p 8080 --rootdir=$(shell pwd)/tests/data -w $(WORKERS)

# Build dependencies
deps: dirs
	pip wheel -w $(DIST) -r requirements.txt

wheel: deps
	mkdir -p $(DIST)
	$(PYTHON) setup.py bdist_wheel --dist-dir=$(DIST)

deliver:
	twine upload -r $(PYPISERVER) $(DIST)/*

dist: dirs manifest
	$(PYTHON) setup.py sdist --dist-dir=$(DIST)

clean:
	rm -rf $(BUILDDIR)



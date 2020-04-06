SHELL:=bash
# 
# Build docker image
#
#

NAME=qgis-map-server

BUILDID=$(shell date +"%Y%m%d%H%M")
COMMITID=$(shell git rev-parse --short HEAD)

# QGIS platform version
FLAVOR:=ltr

ifdef PYPISERVER
PYPISERVER_SCHEME ?= https
PIP_OPTIONS="--extra-index-url=$(PYPISERVER_SCHEME)://$(PYPISERVER) --trusted-host=$(PYPISERVER) --pre"
DOCKERFILE=-f Dockerfile.pypi
BUILD_ARGS=--build-arg PIP_OPTIONS=$(PIP_OPTIONS)
endif

BUILD_ARGS += --build-arg QGIS_VERSION=$(FLAVOR)

REGISTRY_URL ?= 3liz
REGISTRY_PREFIX=$(REGISTRY_URL)/
BUILD_ARGS += --build-arg REGISTRY_PREFIX=$(REGISTRY_PREFIX)

export BUILDIMAGE:=$(NAME):$(FLAVOR)-$(COMMITID)

MANIFEST=factory.manifest

SERVER_VERSION:=$(shell cd .. && python3 setup.py --version)
BUILD_ARGS += --build-arg SERVER_VERSION=$(SERVER_VERSION)

all:
	@echo "Usage: make [build|test|deliver|clean]"

build: _build manifest

_build:
	docker build --rm --force-rm --no-cache $(DOCKER_BUILD_ARGS) \
		$(BUILD_ARGS)  -t $(BUILDIMAGE) $(DOCKERFILE) .

manifest: 
	{ \
	set -e; \
	version=`docker run --rm $(BUILDIMAGE) version`; \
	version_short=`echo $$version | cut -d. -f1-2`; \
	echo name=$(NAME) > $(MANIFEST) && \
    echo version=$$version >> $(MANIFEST) && \
    echo version_short=$$version_short >> $(MANIFEST) && \
    echo release_tag=$(FLAVOR) >> $(MANIFEST) && \
    echo buildid=$(BUILDID)   >> $(MANIFEST) && \
    echo commitid=$(COMMITID) >> $(MANIFEST); }

deliver: tag push

tag_version:
	{ set -e; source factory.manifest; \
	docker tag $(BUILDIMAGE) $(REGISTRY_PREFIX)$(NAME):$$version; \
	}

tag:
	{ set -e; source factory.manifest; \
	docker tag $(BUILDIMAGE) $(REGISTRY_PREFIX)$(NAME):$$version; \
	docker tag $(BUILDIMAGE) $(REGISTRY_PREFIX)$(NAME):$$version_short; \
	docker tag $(BUILDIMAGE) $(REGISTRY_PREFIX)$(NAME):$(FLAVOR); \
	}

push:
	{ set -e; source factory.manifest; \
	docker push $(REGISTRY_URL)/$(NAME):$$version; \
	docker push $(REGISTRY_URL)/$(NAME):$$version_short; \
	docker push $(REGISTRY_URL)/$(NAME):$(FLAVOR); \
	}

clean-all:
	docker rmi -f $(shell docker images $(BUILDIMAGE) -q)

clean:
	 docker rmi $(BUILDIMAGE)

TEST_HTTP_PORT:=8080
QGSRV_USER:=$(shell id -u)

ifndef LOCAL_HOME
LOCAL_HOME=$(shell pwd)
endif

run:
	docker run -it --rm -p $(TEST_HTTP_PORT):8080 -v $(shell pwd)/tests/data:/projects \
       -e QGSRV_CACHE_ROOTDIR=/projects \
       -e QGSRV_USER=$(QGSRV_USER) \
       -e QGSRV_LOGGING_LEVEL=DEBUG \
       $(BUILDIMAGE) 

run-proxy:
	docker run --rm -p $(TEST_HTTP_PORT):8080 --net mynet --name map-proxy-$(COMMITID) \
       -e QGSRV_USER=$(QGSRV_USER) \
       -e QGSRV_LOGGING_LEVEL=DEBUG \
       $(BUILDIMAGE) qgisserver-proxy

run-worker:
	docker run --rm --net mynet -v $(shell pwd)/tests/data:/projects \
       --name qgis3-worker-$(COMMITID) \
       -e QGSRV_CACHE_ROOTDIR=/projects \
       -e QGSRV_USER=$(QGSRV_USER) \
       -e QGSRV_LOGGING_LEVEL=DEBUG \
       -e ROUTER_HOST=map-proxy-$(COMMITID) \
       $(BUILDIMAGE) qgisserver-worker


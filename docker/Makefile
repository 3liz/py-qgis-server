SHELL:=bash
#
# Build docker image
#
#

DEPTH=..

include $(DEPTH)/config.mk

NAME=qgis-map-server

# QGIS platform version
FLAVOR:=release

ifdef PYPISERVER
PYPISERVER_SCHEME ?= https
PIP_OPTIONS="--extra-index-url=$(PYPISERVER_SCHEME)://$(PYPISERVER) --trusted-host=$(PYPISERVER)"
BUILD_ARGS=--build-arg PIP_OPTIONS=$(PIP_OPTIONS)
endif

BUILD_ARGS += --build-arg QGIS_VERSION=$(FLAVOR)

REGISTRY_URL ?= 3liz
REGISTRY_PREFIX=$(REGISTRY_URL)/
BUILD_ARGS += --build-arg REGISTRY_PREFIX=$(REGISTRY_PREFIX)

BUILDIMAGE:=$(NAME):$(FLAVOR)-$(COMMITID)

MANIFEST:=factory-$(FLAVOR).manifest

# Use buildkit
export DOCKER_BUILDKIT:=1

all:
	@echo "Usage: make [build|test|deliver|clean]"

BUILD_TARGET:=base

build: manifest
	docker build --rm --force-rm --no-cache $(DOCKER_BUILD_ARGS) --target $(BUILD_TARGET) \
		$(BUILD_ARGS) -t $(BUILDIMAGE) -f Dockerfile ..


QGIS_IMAGE=$(REGISTRY_PREFIX)qgis-platform:$(FLAVOR)

manifest:
	{ \
	set -e; \
	version=`docker run --rm -v $$(pwd)/scripts:/scripts $(QGIS_IMAGE)  /scripts/qgis-version.sh`; \
	echo name=$(NAME) > $(MANIFEST) && \
    echo version=$$version-$(VERSION) >> $(MANIFEST) && \
    echo version_short=$$version >> $(MANIFEST) && \
    echo release_tag=`echo $$version | cut -d- -f1 |cut -d. -f1-2` >> $(MANIFEST) && \
    echo buildid=$(BUILDID)   >> $(MANIFEST) && \
    echo commitid=$(COMMITID) >> $(MANIFEST); }

deliver: tag push

ifndef CI_COMMIT_TAG

GIT_BRANCH=$(shell git branch --show-current)
ifeq ($(GIT_BRANCH),)
GIT_BRANCH=$(CI_COMMIT_BRANCH)
endif

ifeq ($(GIT_BRANCH),master)
TAG_DEV=dev
else
TAG_DEV=$(GIT_BRANCH)-dev
endif

tag:
	{ set -e; source $(MANIFEST); \
	docker tag $(BUILDIMAGE) $(REGISTRY_PREFIX)$(NAME):$${release_tag}-$(TAG_DEV); \
	docker tag $(BUILDIMAGE) $(REGISTRY_PREFIX)$(NAME):$(FLAVOR)-$(TAG_DEV); \
	}

push:
	{ set -e; source $(MANIFEST); \
	docker push $(REGISTRY_URL)/$(NAME):$${release_tag}-$(TAG_DEV); \
	docker push $(REGISTRY_URL)/$(NAME):$(FLAVOR)-$(TAG_DEV); \
	}
else
tag:
	{ set -e; source $(MANIFEST); \
	docker tag $(BUILDIMAGE) $(REGISTRY_PREFIX)$(NAME):$$version; \
	docker tag $(BUILDIMAGE) $(REGISTRY_PREFIX)$(NAME):$$version_short; \
	docker tag $(BUILDIMAGE) $(REGISTRY_PREFIX)$(NAME):$$release_tag; \
	docker tag $(BUILDIMAGE) $(REGISTRY_PREFIX)$(NAME):$(FLAVOR); \
	}

push:
	{ set -e; source $(MANIFEST); \
	docker push $(REGISTRY_URL)/$(NAME):$$version; \
	docker push $(REGISTRY_URL)/$(NAME):$$version_short; \
	docker push $(REGISTRY_URL)/$(NAME):$$release_tag; \
	docker push $(REGISTRY_URL)/$(NAME):$(FLAVOR); \
	}
endif

clean-all:
	docker rmi -f $(shell docker images $(BUILDIMAGE) -q)

clean:
	 docker rmi $(BUILDIMAGE)

SRCDIR=$(shell realpath ..)

TEST_HTTP_PORT:=8888
QGSRV_USER:=$(shell id -u):$(shell id -g)

run:
	docker run -it --rm  -p $(TEST_HTTP_PORT):8080 --name py-qgis-server  \
   -v $(SRCDIR):/src  \
   -v $(SRCDIR)/tests/data:/projects \
   -e QGSRV_PROJECTS_SCHEMES_TEST=/src/tests/data/ \
   -e QGSRV_PROJECTS_SCHEMES_FOO=file:foobar/ \
   -e QGSRV_PROJECTS_SCHEMES_BAR=file:foobar?data={path} \
   -e QGSRV_SERVER_HTTP_PROXY=yes \
   -e QGSRV_CACHE_ROOTDIR=/projects \
   -e QGSRV_USER=$(QGSRV_USER) \
   -e QGSRV_LOGGING_LEVEL=DEBUG \
   -e QGSRV_MANAGEMENT_ENABLED=yes \
   -e QGSRV_MANAGEMENT_INTERFACES=127.0.0.1 \
   -e QGSRV_SERVER_PLUGINPATH=/src/tests/plugins \
   -e QGSRV_API_ENABLED_LANDING_PAGE=yes \
   -e DEBUG_ENTRYPOINT=yes \
   $(BUILDIMAGE)

run-proxy:
	docker run --rm -p $(TEST_HTTP_PORT):8080 --net mynet --name map-proxy-$(COMMITID) \
   -e QGSRV_USER=$(QGSRV_USER) \
   -e QGSRV_LOGGING_LEVEL=DEBUG \
   $(BUILDIMAGE) qgisserver-proxy

run-worker:
	docker run --rm --net mynet -v $(SRCDIR)/tests/data:/projects \
       --name qgis3-worker-$(COMMITID) \
       -e QGSRV_CACHE_ROOTDIR=/projects \
       -e QGSRV_USER=$(QGSRV_USER) \
       -e QGSRV_LOGGING_LEVEL=DEBUG \
       -e ROUTER_HOST=map-proxy-$(COMMITID) \
       $(BUILDIMAGE) qgisserver-worker


# Push to docker hub as rc version
pushrc:
ifdef CI_COMMIT_TAG
	@echo "This is a TAG commit"
else
	cat $(DOCKERPASS) | docker login -u 3liz --password-stdin
	docker tag $(BUILDIMAGE) 3liz/$(NAME):$(FLAVOR)-rc
	docker push 3liz/$(NAME):$(FLAVOR)-rc
endif

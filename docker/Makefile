
NAME=python-zeromq

BUILDID=$(shell date +"%Y%m%d%H%M")
COMMITID=$(shell git rev-parse --short HEAD)

FACTORY_REVISION=0

VERSION=3.6.5-$(FACTORY_REVISION)
VERSION_SHORT=3.6

VERSION_TAG=$(VERSION)

ifdef REGISTRY_URL
REGISTRY_PREFIX=$(REGISTRY_URL)/
endif

BUILDIMAGE=$(NAME):$(VERSION_TAG)-$(COMMITID)
ARCHIVENAME=$(shell echo $(NAME):$(VERSION_TAG)|tr '[:./]' '_')

FROM=$(REGISTRY_PREFIX)python:3.6-alpine3.6

MANIFEST=factory.manifest

all:
	@echo "Usage: make [build|test|archive|deliver|clean]"

manifest:
	echo name=$(NAME) > $(MANIFEST) && \
    echo version=$(VERSION)     >> $(MANIFEST) && \
    echo version_short=$(VERSION_SHORT) >> $(MANIFEST) && \
    echo buildid=$(BUILDID)     >> $(MANIFEST) && \
    echo commitid=$(COMMITID)   >> $(MANIFEST) && \
    echo archive=$(ARCHIVENAME) >> $(MANIFEST)

build: _build commit

TMPNAME=python-zeromq-$(COMMITID)

_build: manifest
	docker run --name $(TMPNAME) \
		-v $(HOME)/.alpine/wheels:/.wheels \
		-v $(shell pwd)/install.sh:/install.sh \
		-v $(shell pwd)/requirements.txt:/requirements.txt \
		$(FROM) /install.sh

commit:
	docker commit $(TMPNAME) $(BUILDIMAGE) &&\
		docker rm $(TMPNAME)

archive:
	docker save $(BUILDIMAGE) | bzip2 > $(FACTORY_ARCHIVE_PATH)/$(ARCHIVENAME).bz2

tag:
	docker tag $(BUILDIMAGE) $(REGISTRY_PREFIX)$(NAME):$(VERSION)
	docker tag $(BUILDIMAGE) $(REGISTRY_PREFIX)$(NAME):$(VERSION_SHORT)
	docker tag $(BUILDIMAGE) $(REGISTRY_PREFIX)$(NAME):latest

push:
	docker push $(REGISTRY_PREFIX)$(NAME):$(VERSION)
	docker push $(REGISTRY_PREFIX)$(NAME):$(VERSION_SHORT)
	docker push $(REGISTRY_PREFIX)$(NAME):latest

deliver: tag push

clean:
	docker rmi -f $(shell docker images $(BUILDIMAGE) -q)||true


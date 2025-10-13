
# Name to be set in the manifest
PROJECT_NAME:=py-qgis-server

# Project version
VERSION:=$(uv version --short)

ifndef CI_COMMIT_TAG
VERSION_TAG=$(VERSION)rc0
else
VERSION_TAG=$(VERSION)
endif

BUILDID=$(shell date +"%Y%m%d%H%M")
COMMITID=$(shell git rev-parse --short HEAD)

topsrcdir:=$(shell realpath $(DEPTH))


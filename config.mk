
# Name to be set in the manifest
PROJECT_NAME:=py-qgis-server

# Project version
VERSION:=1.9.6

ifndef CI_COMMIT_TAG
VERSION_TAG=$(VERSION)rc0
else
VERSION_TAG=$(VERSION)
endif

BUILDID=$(shell date +"%Y%m%d%H%M")
COMMITID=$(shell git rev-parse --short HEAD)

PYTHON=python3

topsrcdir:=$(shell realpath $(DEPTH))


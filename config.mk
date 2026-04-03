
# Name to be set in the manifest
PROJECT_NAME:=py-qgis-server

# Project version
VERSION:=$(shell uv version --short)
BUILDID=$(shell date +"%Y%m%d%H%M")
COMMITID=$(shell git rev-parse --short HEAD)

topsrcdir:=$(shell realpath $(DEPTH))


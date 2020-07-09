
PROJECT_NAME=py-qgis-server

BUILDDIR=${shell pwd}/build

main: html

html: build
	mkdir -p ${BUILDDIR}/html
	sphinx-build -b html ./  ${BUILDDIR}/html

pdf: build
	mkdir -p ${BUILDDIR}/latex
	sphinx-build -b latex ./  ${BUILDDIR}/latex
	cd ${BUILDDIR}/latex && pdflatex ${PROJECT_NAME}.tex

build: templates
templates: configuration.rst

configuration.rst: ../pyqgisserver/config.yml configuration.rst.j2
	./jtpl.py -c $^



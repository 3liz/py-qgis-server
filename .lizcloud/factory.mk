#
# Makefile for building/packaging qgis for lizmap hosting
#

VERSION=$(shell cd .. && python3 setup.py --version)

main:
	@echo "Makefile for packaging infra components: select a task"

export FACTORY_PRODUCT_NAME=py-qgis-server
export FACTORY_PACKAGE_TYPE=python

PACKAGE=py-qgis-server
FILES=../build/dist/$(PACKAGE)-$(VERSION).tar.gz
PACKAGEFILE=$(PACKAGE)-$(VERSION).tar.gz

build/$(PACKAGEFILE):
	@rm -rf build
	@mkdir -p build
	@cp -rLp $(FILES) build/

.PHONY: package
package: build/$(PACKAGEFILE)
	@echo "Building package $(PACKAGE)"
	$(FACTORY_SCRIPTS)/make-package $(PACKAGE) $(VERSION) $(PACKAGEFILE) ./build


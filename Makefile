# qgis server makefile
#
DEPTH=.

include $(DEPTH)/config.mk

BUILDDIR:=build
DIST:=${BUILDDIR}/dist

MANIFEST=pyqgisserver/build.manifest

FLAVOR:=release

# This is necessary with pytest as long it is not fixed
# see also https://github.com/qgis/QGIS/pull/5337
export QGIS_DISABLE_MESSAGE_HOOKS := 1
export QGIS_NO_OVERRIDE_IMPORT := 1

dirs:
	mkdir -p $(DIST)

version:
	echo $(VERSION_TAG) > VERSION

configure: manifest version

manifest: version
	echo name=$(shell $(PYTHON) setup.py --name) > $(MANIFEST) && \
		echo version=$(shell $(PYTHON) setup.py --version) >> $(MANIFEST) && \
		echo buildid=$(BUILDID)   >> $(MANIFEST) && \
		echo commitid=$(COMMITID) >> $(MANIFEST)

deliver:
	twine upload -r storage $(DIST)/*

dist: dirs configure
	rm -rf *.egg-info
	$(PYTHON) setup.py sdist --dist-dir=$(DIST)

clean:
	rm -rf $(BUILDDIR)

test: lint test-test

lint:
	@flake8 pyqgisserver pyqgisservercontrib


test-%:
	$(MAKE) -C tests env $* FLAVOR=$(FLAVOR)

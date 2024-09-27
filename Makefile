# qgis server makefile
#
DEPTH=.

include $(DEPTH)/config.mk

DIST:=dist

MANIFEST=pyqgisserver/build.manifest

PYTHON_PKG=pyqgisserver pyqgisservercontrib

TESTDIR=tests/unittests

PYPISERVER:=storage

# This is necessary with pytest as long it is not fixed
# see also https://github.com/qgis/QGIS/pull/5337
export QGIS_DISABLE_MESSAGE_HOOKS := 1
export QGIS_NO_OVERRIDE_IMPORT := 1

dirs:
	mkdir -p $(DIST)

version:
	echo $(VERSION_TAG) > VERSION

configure: manifest

manifest: version
	echo name=$(shell $(PYTHON) setup.py --name) > $(MANIFEST) && \
		echo version=$(shell $(PYTHON) setup.py --version) >> $(MANIFEST) && \
		echo buildid=$(BUILDID)   >> $(MANIFEST) && \
		echo commitid=$(COMMITID) >> $(MANIFEST)

deliver:
	twine upload $(TWINE_OPTIONS) -r $(PYPISERVER) $(DIST)/*

dist: dirs configure
	rm -rf *.egg-info
	$(PYTHON) setup.py sdist --dist-dir=$(DIST)

clean:
	rm -rf $(DIST)

test: lint
	make -C tests test PYTEST_ADDOPTS=$(PYTEST_ADDOPTS)

install:
	pip install -U --upgrade-strategy=eager -e .

install-tests:
	pip install -U --upgrade-strategy=eager -r tests/requirements.txt

install-doc:
	pip install -U --upgrade-strategy=eager -r doc/requirements.txt

install-dev: install-tests install-doc

lint:
	@ruff check $(PYTHON_PKG) $(TESTDIR)

lint-preview:
	@ruff check --preview $(PYTHON_PKG) $(TESTDIR)

lint-fix:
	@ruff check --preview --fix $(PYTHON_PKG) $(TESTDIR)

typing:
	mypy --config-file=$(topsrcdir)/mypy.ini -p pyqgisserver


# qgis server makefile
#
DEPTH=.

include $(DEPTH)/config.mk

DIST:=dist

MANIFEST=src/pyqgisserver/build.manifest

PYTHON_PKG=src

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
	echo name=$(PROJECT_NAME) > $(MANIFEST) && \
	echo version=$(VERSION_TAG) >> $(MANIFEST) && \
	echo buildid=$(BUILDID)   >> $(MANIFEST) && \
	echo commitid=$(COMMITID) >> $(MANIFEST)
	@echo "=== Written manifest ==="
	@cat $(MANIFEST)

deliver:
	twine upload $(TWINE_OPTIONS) -r $(PYPISERVER) $(DIST)/*

dist: dirs configure
	rm -rf *.egg-info
	$(PYTHON) -m build --no-isolation --sdist --outdir=$(DIST)

clean:
	rm -rf $(DIST)

test: manifest lint
	@make -C tests test PYTEST_ADDOPTS=$(PYTEST_ADDOPTS)
  

ifdef VIRTUAL_ENV
# Always prefer active environment
ACTIVE_VENV=--active
endif

install: manifest
	@uv sync --frozen $(ACTIVE_VENV)

upgrade-requirements: 
	@uv sync -U $(ACTIVE_VENV)

lint:
	@ruff check --output-format=concise $(PYTHON_PKG) $(TESTDIR)

lint-preview:
	@ruff check --preview $(PYTHON_PKG) $(TESTDIR)

lint-fix:
	@ruff check --preview --fix $(PYTHON_PKG) $(TESTDIR)

typecheck:
	@mypy --config-file=$(topsrcdir)/mypy.ini src


REQUIREMENT_GROUPS=\
  tests \
  lint \
  $(NULL)

REQUIREMENTS=requirements.txt $(patsubst %, update-requirements-%, $(REQUIREMENT_GROUPS))

requirements.txt:
	@echo "Updating requirements.txt"; \
	uv export --format requirements.txt \
		--no-annotate \
		--no-editable \
		--no-hashes -q -o requirements.txt;

update-requirements-%:
	@echo "Updating requirqments for '$*'"; \
	uv export --format requirements.txt \
		--no-annotate \
		--no-editable \
		--no-hashes \
		--only-group $* \
		-q -o requirements/$*.txt;

update-requirements: $(REQUIREMENTS)


# qgis server makefile
#
DEPTH=.

include $(DEPTH)/config.mk

MANIFEST=src/pyqgisserver/build.manifest

PYTHON_PKG=src

TESTDIR=tests/unittests


#
# Configure
#

# Check if uv is available
$(eval UV_PATH=$(shell which uv))
ifdef UV_PATH
# Use installed python
export UV_NO_MANAGED_PYTHON=true
ifdef VIRTUAL_ENV
# Always prefer active environment
UV_OPTS += --active
endif
UV=uv run $(UV_OPTS)
endif

-include .localconfig.mk

REQUIREMENT_GROUPS=\
  dev \
  tests \
  lint \
  $(NULL)

.PHONY: update-requirements

REQUIREMENTS=requirements.txt $(patsubst %, update-requirements-%, $(REQUIREMENT_GROUPS))

update-requirements: $(REQUIREMENTS)

requirements.txt: uv.lock
	@echo "Updating requirements.txt"; \
	uv export --no-dev  --format requirements.txt \
		--no-annotate \
		--no-editable \
		--no-hashes -q -o requirements.txt;

update-requirements-%: uv.lock
	@echo "Updating requirqments for '$*'"; \
	uv export --format requirements.txt \
		--no-annotate \
		--no-editable \
		--no-hashes \
		--only-group $* \
		-q -o requirements/$*.txt;


# Install all dev requirements using frozen packagess
install:
	@ uv sync --all-groups --frozen $(UV_OPTS)

version:
	echo $(VERSION) > VERSION

configure: manifest

manifest: version
	echo name=$(PROJECT_NAME) > $(MANIFEST) && \
	echo version=$(VERSION) >> $(MANIFEST) && \
	echo buildid=$(BUILDID)   >> $(MANIFEST) && \
	echo commitid=$(COMMITID) >> $(MANIFEST)
	@echo "=== Written manifest ==="
	@cat $(MANIFEST)
#
# Release
#

bump-release-version:
	@echo "Bumping to release version"
	@ uv version --bump stable $(UV_OPTS)

#
# Static analysis
#

LINT_TARGETS=$(PYTHON_PKG) $(TESTDIR)

lint::
	@ $(UV) ruff check --output-format=concise $(LINT_TARGETS)

lint-preview:
	@ $(UV) ruff check --preview $(LINT_TARGETS)

lint-fix:
	@ $(UV) ruff check --fix $(LINT_TARGETS)

format:
	@ $(UV) ruff format $(LINT_TARGETS) 

format-diff:
	@ $(UV) ruff format --diff $(LINT_TARGETS) 

typecheck:
	@ $(UV) mypy --config-file=$(topsrcdir)/mypy.ini src

#
# Tests
#

test: manifest
	$(UV) pytest -v $(TESTDIR)
  
#
# Packaging
#

ifeq ($(DIST_RELEASE), true)
dist:: bump-release-version
endif

dist:: clean
	@uv build --sdist --wheel

clean:
	rm -rf *.egg-info ./dist

#
# Deprecated
#

PYPISERVER:=storage

deliver:
	twine upload $(TWINE_OPTIONS) -r $(PYPISERVER) dist/*.tar.gz



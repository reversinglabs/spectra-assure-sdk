# makefile; ts=4
# supported: 3.10, 3.11, 3.12, 3.13
# 3.10 last dat Oct 31 2026
MIN_PYTHON_VERSION := python3.10
export MIN_PYTHON_VERSION

VENV := ./vtmp/
export VENV

PACKAGE_NAME := spectra_assure_api_client
LINE_LENGTH := 120
PY_FILES := examples tests $(PACKAGE_NAME)

DOC_DIR := ./doc/
STUBS_DIR := ./stubs/

COMMON_VENV := rm -rf $(VENV); \
	$(MIN_PYTHON_VERSION) -m venv $(VENV); \
	source ./$(VENV)/bin/activate;

PIP_INSTALL := pip3 -q \
	--require-virtualenv \
	--disable-pip-version-check \
	--no-color install --no-cache-dir

README_REQUESTS_VERSION := $(shell grep requests README.md | grep 'version:' | awk '{ print $$NF }' )
TOML_REQUESTS_VERSION := $(shell grep 'requests==' *.toml | awk '{ r =gensub(/.*requests==([0-9\.]+).*/,"\\1", "g") ; print r }' )
ASSERT_REQUESTS_VERSION := $(shell echo 1 | awk '{ if( "$(README_REQUESTS_VERSION)" != "$(TOML_REQUESTS_VERSION)" ) { print 1 } else { print 0 } }' )

.PHONY: prep all tests format check mypy testLocalInstall build

# ========================================
# ========================================
simple: ASSERT prep

all: ASSERT prep tests

ASSERT: README.md pyproject.toml
	if (( $(ASSERT_REQUESTS_VERSION) == 1 )) ; then \
		echo README_REQUESTS_VERSION is $(README_REQUESTS_VERSION); \
 		echo TOML_REQUESTS_VERSIONis $(TOML_REQUESTS_VERSION); \
 		echo Please update the readme to match the toml requirement; \
		exit $(ASSERT_REQUESTS_VERSION); \
	fi

prep: clean format check mypy makeStubs pyreverse

clean: cleanupVenv
	rm -rf stubs out
	rm -rf dist
	rm -rf .mypy_cache */.mypy_cache
	rm -rf __pycache__ */__pycache__
	rm -f *.1 *.2
	rm -f classes.dot
	rm -f *.pyi */*.pyi */*/*.pyi
	(cd tests; make test_clean)

cleanupVenv:
	rm -rf $(VENV)
	rm -rf ./tests/$(VENV)

format:
	ruff format $(PY_FILES)

check:
	ruff check --fix $(PY_FILES)

mypy:
	$(COMMON_VENV) \
	$(PIP_INSTALL) mypy; \
	$(PIP_INSTALL) types-requests; \
	mypy --strict --no-incremental $(PACKAGE_NAME)

makeStubs:
	rm -rf $(STUBS_DIR) out */*.pyi */*/*.pyi
	mkdir $(STUBS_DIR)
	$(COMMON_VENV) \
	$(PIP_INSTALL) mypy; \
	$(PIP_INSTALL) types-requests; \
	stubgen $(PACKAGE_NAME) -o $(STUBS_DIR)

pyreverse:
	$(COMMON_VENV) \
	$(PIP_INSTALL) pylint; \
	$(PIP_INSTALL) types-requests; \
	pyreverse $(PACKAGE_NAME); \
	pyreverse -o svg $(PACKAGE_NAME); \
	mv *.svg *.dot $(DOC_DIR)

# ========================================
# ========================================
testpypi: build
	twine upload \
		--config-file=$${HOME}/.pypirc_testing \
		--repository=testpypi \
		dist/*

# ========================================
# ========================================
build: clean
	$(COMMON_VENV) \
	python3 --version ; \
	which $(MIN_PYTHON_VERSION) ; \
	$(PIP_INSTALL) build; \
	$(MIN_PYTHON_VERSION) -m build;
	ls -l dist

testLocalInstall: build
	./testLocalWhl.sh

tests: tests-simple
# tests: tests-staging

tests-staging: testLocalInstall
	( cd tests && TEST_STAGING=1 make tests )

tests-simple: testLocalInstall
	( cd tests && TEST_PLAYGROUND1=1 make tests )
	( cd tests && TEST_PLAYGROUND2=1 make tests )
	cp tests/api_client_example.py examples/

tests-all: testLocalInstall
	( cd tests && TEST_MY=1 		 make tests )
	( cd tests && TEST_PLAYGROUND1=1 make tests )
	( cd tests && TEST_PLAYGROUND2=1 make tests )
	( cd tests && TEST_CANADA=1 	 make tests )

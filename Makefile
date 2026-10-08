# makefile; ts=4
# supported: 3.10, 3.11, 3.12, 3.13
# 3.10 last dat Oct 31 2026
SHELL := /bin/bash
export SHELL

MIN_PYTHON_VERSION := python3.10
export MIN_PYTHON_VERSION

VENV := ./vtmp/
export VENV

PACKAGE_NAME := spectra_assure_api_client
LINE_LENGTH := 120
PY_FILES := examples tests tests_unit tools $(PACKAGE_NAME)

DOC_DIR := ./doc/
STUBS_DIR := ./stubs/

COMMON_VENV := rm -rf $(VENV); \
	$(MIN_PYTHON_VERSION) -m venv $(VENV); \
	source ./$(VENV)/bin/activate;

PIP_INSTALL := pip3 -q \
	--require-virtualenv \
	--disable-pip-version-check \
	--no-color install --no-cache-dir

PY := $(VENV)/bin/python

.PHONY: prep all tests format check mypy testLocalInstall build
.PHONY: test tests-staging tests-playground1 tests-playground2 tests-production tests-canada tests-all tests-simple

# ---------------------------------------
simple:  prep

all: prep tests

# ---------------------------------------
# prep: clean format check mypy mypy2 unit_test makeStubs pyreverse build
prep: clean format check mypy mypy2 makeStubs pyreverse build

unit_test:
	make -f Makefile.unit_test

clean: cleanupVenv
	rm -rf stubs out
	rm -rf dist
	rm -rf .mypy_cache */.mypy_cache
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -f *.1 *.2
	rm -f classes.dot
	rm -f *.pyi */*.pyi */*/*.pyi
	(cd tests; make test_clean)
	rm -rf .ruff_cache */.ruff_cache .pytest_cache
	find . -type d -name __pycache__
	find . -type d -name .mypy_cache
	find . -type d -name .ruff_cache

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

mypy2:
	$(COMMON_VENV) \
	$(PIP_INSTALL) mypy; \
	$(PIP_INSTALL) types-requests  types-PyYAML pytest; \
	mypy --strict --no-incremental tests tests_unit tools $(PACKAGE_NAME)

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

build: clean
	$(COMMON_VENV) \
	python3 --version ; \
	which $(MIN_PYTHON_VERSION) ; \
	$(PIP_INSTALL) build; \
	$(MIN_PYTHON_VERSION) -m build;
	ls -l dist

# ---------------------------------------
testpypi: build
	$(PY) -m twine upload --repository=testpypi dist/*.whl

test: tests

# tests: tests-simple
tests: tests-staging

testLocalInstall: build
	./bin/testLocalWhl.sh $$( realpath . )

# One target per endpoint; the endpoint table is in tests/Makefile.
# Production and Canada run only on demand.
tests-staging tests-playground1 tests-playground2 tests-production tests-canada: tests-%: testLocalInstall
	( cd tests && $(MAKE) ENDPOINT=$* )

# The regular endpoints, one after the other: the first failing test stops the
# run, endpoints not yet run included. Only when all have passed is the example
# copied to examples/.
tests-all: testLocalInstall
	( cd tests && $(MAKE) ENDPOINT=staging ) && \
	( cd tests && $(MAKE) ENDPOINT=playground1 ) && \
	( cd tests && $(MAKE) ENDPOINT=playground2 )
	cp tests/api_client_example.py examples/

tests-simple: tests-staging

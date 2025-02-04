# makefile; ts=4

# supported: 3.10, 3.11 3.12 3.13
MIN_PYTHON_VERSION := python3.10
export MIN_PYTHON_VERSION

VENV := ./vtmp/
export VENV

PACKAGE_NAME := spectra_assure_api_client
LINE_LENGTH := 120
PY_FILES := examples tests $(PACKAGE_NAME)

DOC_DIR := ./doc/
STUBS_DIR := ./stubs/


PL_LINTERS := eradicate,mccabe,pycodestyle,pyflakes,pylint

# C0103 Variable name "%s" doesn't conform to snake_case naming style [pylint]
# C0114 Missing module docstring [pylint]
# C0115 Missing class docstring [pylint]
# C0116 Missing function or method docstring [pylint]
# C0301 Line too long (%s/%s) [pylint] :: add :: # pylint: disable=line-too-long
# E203 whitespace before ':' [pycodestyle]
# E402 module level import not at top of file [pycodestyle]

PL_IGNORE="C0103,C0114,C0115,C0116,C0301,E203,E402,C901"

COMMON_VENV := rm -rf $(VENV); \
	$(MIN_PYTHON_VERSION) -m venv $(VENV); \
	source ./$(VENV)/bin/activate;


.PHONY: prep all tests black pylama mypy testLocalInstall build

all: prep tests

prep: clean black pylama mypy makeStubs pyreverse

clean: cleanupVenv
	rm -rf stubs out
	rm -rf dist
	rm -rf .mypy_cache */.mypy_cache
	rm -rf __pycache__ */__pycache__
	rm -f *.1 *.2
	rm -f classes.dot
	rm -f *.pyi */*.pyi */*/*.pyi
	cd tests; make clean

cleanupVenv:
	rm -rf $(VENV)
	rm -rf ./tests/$(VENV)

black:
	$(COMMON_VENV) \
	pip3 install black; \
	black \
		--line-length $(LINE_LENGTH) \
		$(PY_FILES)

pylama:
	$(COMMON_VENV) \
	pip3 install pylama; \
	pylama \
		--max-line-length $(LINE_LENGTH) \
		--linters "${PL_LINTERS}" \
		--ignore "${PL_IGNORE}" \
		$(PY_FILES)

mypy:
	$(COMMON_VENV) \
	pip3 install mypy; \
	pip3 install types-requests; \
	mypy --strict --no-incremental $(PACKAGE_NAME)

makeStubs:
	rm -rf $(STUBS_DIR) out */*.pyi */*/*.pyi
	mkdir $(STUBS_DIR)
	$(COMMON_VENV) \
	pip3 install mypy; \
	pip3 install types-requests; \
	stubgen $(PACKAGE_NAME) -o $(STUBS_DIR)

tests: testLocalInstall
	cd tests && make tests
	cp tests/api_client_example.py examples/

testLocalInstall: build
	./testLocalWhl.sh

build: clean
	$(COMMON_VENV) \
	python3 --version ; \
	which $(MIN_PYTHON_VERSION) ; \
	pip3 install --no-cache-dir build; \
	$(MIN_PYTHON_VERSION) -m build;
	ls -l dist

testpypi: build
	twine upload \
		--config-file=$${HOME}/.pypirc_testing \
		--repository=testpypi \
		dist/*

pyreverse:
	$(COMMON_VENV) \
	pip3 install pylint; \
	pip3 install types-requests; \
	pyreverse $(PACKAGE_NAME); \
	pyreverse -o svg $(PACKAGE_NAME); \
	mv *.svg *.dot $(DOC_DIR)

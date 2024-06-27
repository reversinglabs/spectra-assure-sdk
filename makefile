# makefile; ts=4

MIN_PYTHON_VERSION	:= python3.10
VENV				:= ./vtmp/

PACKAGE_NAME		:= spectra_assure_api_client
LINE_LENGTH 		:= 120
PY_FILES 			:= tests $(PACKAGE_NAME)

export MIN_PYTHON_VERSION
export VENV

PL_LINTERS			:=	eradicate,mccabe,pycodestyle,pyflakes,pylint

# C0103 Variable name "%s" doesn't conform to snake_case naming style [pylint]
# C0114 Missing module docstring [pylint]
# C0115 Missing class docstring [pylint]
# C0116 Missing function or method docstring [pylint]
# C0301 Line too long (%s/%s) [pylint] :: add :: # pylint: disable=line-too-long
# E203 whitespace before ':' [pycodestyle]
# E402 module level import not at top of file [pycodestyle]

PL_IGNORE="C0103,C0114,C0115,C0116,C0301,E203,E402"

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
	rm -rf $(VENV)
	$(MIN_PYTHON_VERSION) -m venv $(VENV); \
	source ./$(VENV)/bin/activate; \
	pip3 install black; \
	black \
		--line-length $(LINE_LENGTH) \
		$(PY_FILES)

pylama:
	rm -rf $(VENV)
	$(MIN_PYTHON_VERSION) -m venv $(VENV); \
	source ./$(VENV)/bin/activate; \
	pip3 install pylama; \
	pylama \
		--max-line-length $(LINE_LENGTH) \
		--linters "${PL_LINTERS}" \
		--ignore "${PL_IGNORE}" \
		$(PY_FILES)

mypy:
	rm -rf $(VENV)
	$(MIN_PYTHON_VERSION) -m venv $(VENV); \
	source ./$(VENV)/bin/activate; \
	pip3 install mypy; \
	pip3 install types-requests; \
	mypy --strict --no-incremental $(PACKAGE_NAME)

makeStubs:
	rm -rf stubs out */*.pyi */*/*.pyi
	mkdir stubs
	stubgen $(PACKAGE_NAME) -o stubs
	# stubgen $(PACKAGE_NAME) -o .

tests: testLocalInstall
	cd tests && make tests
	cp tests/api_client_example.py examples/

testLocalInstall: build
	./testLocalWhl.sh

build:
	rm -rf $(VENV)
	$(MIN_PYTHON_VERSION) -m venv $(VENV); \
	source ./$(VENV)/bin/activate; \
	pip3 install build; \
	$(MIN_PYTHON_VERSION) -m build;
	ls -l dist

pyreverse:
	pyreverse spectraAssureApi
	rm -f packages.dot
	pyreverse -o svg spectraAssureApi
	rm -f packages.svg
	mv *.dot *.svg doc/

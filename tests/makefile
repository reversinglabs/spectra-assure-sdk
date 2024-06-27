# makefile

MIN_PYTHON_VERSION	:= python3.10
VENV				:= ./vtmp/

ARTIFACT_OK		:= bash
ARTIFACT_ERR	:= eicarcom2.zip
ARTIFACT		:= $(ARTIFACT_ERR)
INPUT_DIR		:= ./input
INPUT_PATH		:=	$(INPUT_DIR)/$(ARTIFACT)

RLSECURE_PROXY_SERVER	:=	alt-win-proxy.rl.lan
RLSECURE_PROXY_PORT		:=	8080
RLSECURE_PROXY_USER		:=	user1
RLSECURE_PROXY_PASSWORD	:=	pero123

VERSION := $(shell awk '/VERSION/ { version=$$NF; gsub(/"/,"",version); print version; }' < ../spectra_assure_api_client/version.py )
PACKAGE_TEST_INSTALL := $(shell ls ../dist/*-$(VERSION)-py3-none-any.whl )

ENV_FILE	:=	~/.envfile_rl-scanner-cloud

export VERSION
export PACKAGE_TEST_INSTALL
export MIN_PYTHON_VERSION
export VENV
export INPUT_DIR
export INPUT_PATH
export ENV_FILE

# if we want to test proxy export the next 4 lines, else comment out
# note that this can be overwritten by ~/.envfile_rl-scanner-cloud as it comes later

ifeq ($(strip $(WITH_PROXY)),)
	# no export
else
	export RLSECURE_PROXY_SERVER
	export RLSECURE_PROXY_PORT
	export RLSECURE_PROXY_USER
	export RLSECURE_PROXY_PASSWORD
endif

TEST_EXAMPLES := t1 api_client_example
TESTS := test-list-all test-project-steps test-package-steps test-version-steps test-download $(TEST_EXAMPLES)
# TESTS := test-download $(TEST_EXAMPLES)
# TESTS := test-download


.PHONY: clean prep tests

# tests: clean prep mypy-stubs mypy $(TESTS)
tests: clean prep mypy-stubs $(TESTS)
# tests: clean prep $(TESTS)

clean:
	rm -f *.1 *.2
	rm -rf $(VENV)
	rm -rf input
	rm -f *.log
	rm -rf downloads*

prep:
	rm -rf $(VENV)
	rm -rf downloads*
	ls -l $(PACKAGE_TEST_INSTALL)
	echo $(PACKAGE_TEST_INSTALL)
	mkdir -p input
	curl -o ./input/$(ARTIFACT_ERR) -sS https://secure.eicar.org/$(ARTIFACT_ERR)

test-list-all:
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1

test-project-steps:
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1

test-package-steps:
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1

test-version-steps: prep
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1

test-download: prep
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1

t1: prep
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1

api_client_example: prep
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1

# test using the generated stubs
mypy-stubs:
	rm -rf $(VENV)
	$(MIN_PYTHON_VERSION) -m venv $(VENV); \
	source ./$(VENV)/bin/activate; \
	pip3 install --disable-pip-version-check  -q mypy; \
	pip3 install --disable-pip-version-check  -q types-requests; \
	pip3 install --disable-pip-version-check  -q $(PACKAGE_TEST_INSTALL); \
	MYPYPATH=../stubs/ mypy --strict --no-incremental *.py

# test using the type hint py.typed
mypy:
	rm -rf $(VENV)
	$(MIN_PYTHON_VERSION) -m venv $(VENV); \
	source ./$(VENV)/bin/activate; \
	pip3 install --disable-pip-version-check  -q mypy; \
	pip3 install --disable-pip-version-check  -q types-requests; \
	pip3 install --disable-pip-version-check  -q $(PACKAGE_TEST_INSTALL); \
	mypy --strict --no-incremental *.py

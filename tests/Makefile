# makefile

# ---------------------------------------
MIN_PYTHON_VERSION	:= python3.10
VENV				:= ./vtmp/
export MIN_PYTHON_VERSION
export VENV

COMMON_VENV := 	rm -rf $(VENV); \
	$(MIN_PYTHON_VERSION) -m venv $(VENV); \
	source ./$(VENV)/bin/activate;

PIP_INSTALL := pip3 -q \
	--require-virtualenv \
	--disable-pip-version-check \
	--no-color install --no-cache-dir

# ---------------------------------------
ARTIFACT_OK		:= bash
ARTIFACT_ERR	:= eicarcom2.zip
ARTIFACT		:= $(ARTIFACT_ERR)

# ---------------------------------------
INPUT_DIR		:= ./input
INPUT_PATH		:=	$(INPUT_DIR)/$(ARTIFACT)
export INPUT_DIR
export INPUT_PATH

# ---------------------------------------
VERSION := $(shell awk '/VERSION/ { version=$$NF; gsub(/"/,"",version); print version; }' < ../spectra_assure_api_client/version.py )
PACKAGE_TEST_INSTALL := $(shell ls ../dist/*-$(VERSION)-py3-none-any.whl )
export VERSION
export PACKAGE_TEST_INSTALL

# ---------------------------------------
# defaults
ENV_FILE	:=	~/.envfile_rl-scanner-cloud-my
ENV_NAME	:=	my

# variable test endpoints
ifdef TEST_PLAYGROUND1
	ENV_FILE	:=	~/.envfile_rl-scanner-cloud-playground
	ENV_NAME	:=	pg1
endif

ifdef TEST_PLAYGROUND2
	ENV_FILE	:=	~/.envfile_rl-scanner-cloud-playground2
	ENV_NAME	:=	pg2
endif

ifdef TEST_CANADA
	ENV_FILE	:=	~/.envfile_rl-scanner-cloud-canada
	ENV_NAME	:=	ca
endif

# install a config file if we have one for this environment
ZZ := myConfig.json
CONF_FILE 	:= $(shell rm -f $(ZZ) ; [ -f $(ZZ)-$(ENV_NAME) ] && cp $(ZZ)-$(ENV_NAME) $(ZZ) )

export ENV_FILE
export ENV_NAME
# export CONF_FILE

BASIC_TESTS		:= t1 t2 t3
COMMUNITY_TESTS := test-community-find-packages test-community-report-package test-community-report-version
STEPS_TESTS 	:= test-project-steps test-package-steps test-version-steps
LIST_ALL 		:= list_all # a very long test not normally needed
DOWNLOAD_TESTS 	:= test-download

TESTS 			:= $(BASIC_TESTS) \
					$(STEPS_TESTS) \
					$(TEST_DOWNLOAD) \
					$(COMMUNITY_TESTS) \
					api_client_example

TESTS 			:= api_client_example

POST_TEST := mv *.[12] $(ENV_NAME)/; ls *.log >/dev/null && mv *.log $(ENV_NAME)/

# ---------------------------------------
.PHONY: all test_clean test_prep tests mypy mypy-stubs

# ---------------------------------------
all: test_clean test_prep mypy-stubs mypy tests

test_clean:
	rm -f *.1 *.2 *.log
	rm -rf my ca pg1 pg2
	rm -rf $(VENV)
	rm -rf input test1
	rm -rf downloads*
	mkdir -p ./downloads
	mkdir -p ./input
	rm -f export_profile*.json

# this breaks under globalprotext use a local file
./input/$(ARTIFACT_ERR):
	cp ~/Downloads/eicar/$(ARTIFACT_ERR) ./input/
	# curl -o ./input/$(ARTIFACT_ERR) -sS https://secure.eicar.org/$(ARTIFACT_ERR)

# test using the generated stubs
mypy-stubs:
	$(COMMON_VENV) \
	$(PIP_INSTALL) mypy; \
	$(PIP_INSTALL) types-requests; \
	$(PIP_INSTALL) $(PACKAGE_TEST_INSTALL); \
	MYPYPATH=../stubs/ mypy --strict --no-incremental *.py

# test using the type hint py.typed
mypy:
	$(COMMON_VENV) \
	$(PIP_INSTALL) mypy; \
	$(PIP_INSTALL) types-requests; \
	$(PIP_INSTALL) $(PACKAGE_TEST_INSTALL); \
	mypy --strict --no-incremental *.py

PRE_TESTS:
	mkdir -p $(ENV_NAME)

tests: ./input/$(ARTIFACT_ERR) PRE_TESTS $(TESTS)

t1:
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1
	$(POST_TEST)

t2:
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1
	$(POST_TEST)

t3:
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1
	$(POST_TEST)

api_client_example:
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1
	$(POST_TEST)
	cp $@.py ../examples/

test-list-all:
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1
	$(POST_TEST)

test-project-steps:
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1
	$(POST_TEST)

test-package-steps:
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1
	$(POST_TEST)

test-version-steps:
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1
	$(POST_TEST)

test-download:
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1
	$(POST_TEST)

test-community-find-packages:
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1
	$(POST_TEST)

test-community-report-package:
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1
	$(POST_TEST)

test-community-report-version:
	rm -rf $(VENV)
	./test-one.sh $@.py 2>$@.2 | tee $@.1
	$(POST_TEST)

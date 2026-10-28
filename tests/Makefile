# Integration tests against a live Spectra Assure Portal. See README.md.
#
#   make ENDPOINT=<name>          clean, type-check, then run the tests
#   make tests ENDPOINT=<name>    run the tests only
#   make sweep ENDPOINT=<name>    remove what interrupted runs left on the endpoint
#
# The top-level Makefile has a target per endpoint (tests-staging, ...) and
# tests-all.

SHELL := /bin/bash
export SHELL
.SHELLFLAGS := -o pipefail -c

# The top-level Makefile hands down its minimal Python version (it exports it).
MIN_PYTHON_VERSION ?= python3.10
export MIN_PYTHON_VERSION

PIP_INSTALL := pip3 -q \
	--require-virtualenv \
	--disable-pip-version-check \
	--no-color install --no-cache-dir

# ---------------------------------------
# The endpoint table: one row per endpoint. ENDPOINT names the row to run.
#   ENV_FILE_<endpoint>       the hidden env file in the home directory (export KEY=VALUE lines)
#   NO_SSL_VERIFY_<endpoint>  1 where the endpoint has a self-signed certificate
# The TLS setting lives here, not in the env files, which other scripts share.
# tests-all (top-level Makefile) runs staging, playground1 and playground2;
# production and canada run only on demand.
ENDPOINTS := staging playground1 playground2 production canada

ENV_FILE_staging       := ~/.envfile_rl-scanner-cloud-staging
NO_SSL_VERIFY_staging  := 1
ENV_FILE_playground1   := ~/.envfile_rl-scanner-cloud-playground
ENV_FILE_playground2   := ~/.envfile_rl-scanner-cloud-playground2
ENV_FILE_production    := ~/.envfile_rl-scanner-cloud
ENV_FILE_canada        := ~/.envfile_rl-scanner-cloud-canada

ENV_FILE := $(ENV_FILE_$(ENDPOINT))
ENV_NAME := $(ENDPOINT)
# "1" turns TLS verification off for the tests and the sweep.
RLPORTAL_NO_SSL_VERIFY := $(NO_SSL_VERIFY_$(ENDPOINT))
export ENV_FILE
export ENV_NAME
export RLPORTAL_NO_SSL_VERIFY

# ---------------------------------------
# The file the scan tests upload, and the wheel under test.
ARTIFACT   := eicarcom2.zip
INPUT_PATH := ./input/$(ARTIFACT)
VERSION := $(shell awk '/VERSION/ { version=$$NF; gsub(/"/,"",version); print version; }' < ../spectra_assure_api_client/version.py )
PACKAGE_TEST_INSTALL := $(shell ls ../dist/*-$(VERSION)-py3-none-any.whl )

# ---------------------------------------
# One virtual environment per run, with the wheel and pytest, for the tests,
# the selftest and the sweep; the type checks use their own.
PYTEST_VENV := ./vpytest/
MYPY_VENV   := ./vtmp/
ACTIVATE    := source $(PYTEST_VENV)/bin/activate;

# The test modules, in the order they run. Results go to results/<endpoint>/<time>/.
RESULTS := results/$(ENDPOINT)/$(shell date +%Y%m%d-%H%M%S)
PYTEST_MODULES := integration/test_connection.py integration/test_groups.py \
	integration/test_projects.py integration/test_packages.py integration/test_versions.py \
	integration/test_community.py integration/test_audit_log.py integration/test_example.py

# ONLY_CATALOG=1: test the Catalog API and nothing else, for an endpoint where it
# is new and there is little other data to test against (staging). Only the
# example program runs, and it runs only its Catalog section.
ifneq ($(ONLY_CATALOG),)
PYTEST_MODULES := integration/test_example.py
RLPORTAL_ONLY_CATALOG := 1
export RLPORTAL_ONLY_CATALOG
endif

# --maxfail=1: the first failing test stops the run, and make fails exactly when
# pytest does. --tb=short: the long traceback prints each function's arguments,
# and with them the token (in the client's settings and in the request headers).
# The InsecureRequestWarning comes only from endpoints with TLS verification
# deliberately off (staging); it is filtered to keep the output readable.
PYTEST := python -m pytest --maxfail=1 --tb=short -p no:cacheprovider \
	-W ignore::urllib3.exceptions.InsecureRequestWarning

# ---------------------------------------
.PHONY: all tests pytests clean test_clean venv selftest selftest-run check-endpoint sweep mypy mypy-stubs

all: test_clean mypy-stubs mypy tests

# Appended to a { command group; }: its stdout is kept in $(1).1 and its stderr
# in $(1).2, and both are still shown. With pipefail the group's exit status
# survives the tee.
KEEP_OUTPUT = 2> >(tee $(1).2 >&2) | tee $(1).1

# The endpoint's env file is read with `.` and without tracing, so nothing
# secret is echoed. Everything the run produces stays in $(RESULTS) until
# `make clean`: pytest's output (pytest.1, pytest.2), its log (run.log),
# junit.xml, the downloads, and the example program's api_client_example.1,
# .2 and .log.
tests: check-endpoint venv selftest $(INPUT_PATH)
	mkdir -p $(RESULTS)
	$(ACTIVATE) { eval . $(ENV_FILE); \
	INPUT_PATH=$(abspath $(INPUT_PATH)) RLPORTAL_RESULTS=$(abspath $(RESULTS)) \
	$(PYTEST) $(PYTEST_MODULES) -o junit_family=xunit2 \
		--junitxml=$(RESULTS)/junit.xml -o log_file=$(RESULTS)/run.log -o log_file_level=INFO; \
	} $(call KEEP_OUTPUT,$(RESULTS)/pytest)
	@echo "results: $(abspath $(RESULTS))"

# The name used while the old scripts still ran beside the pytest suite.
pytests: tests

# Delete the sdktest-<endpoint>-... projects that earlier runs left on this
# endpoint, if older than SWEEP_AGE_HOURS (24); SWEEP_DRY_RUN=1 only lists them.
sweep: check-endpoint venv
	$(ACTIVATE) eval . $(ENV_FILE); python sweep.py

venv:
	rm -rf $(PYTEST_VENV); $(MIN_PYTHON_VERSION) -m venv $(PYTEST_VENV)
	$(ACTIVATE) $(PIP_INSTALL) $(PACKAGE_TEST_INSTALL) pytest

check-endpoint:
	@if [ -n "$(TEST_STAGING)$(TEST_PLAYGROUND1)$(TEST_PLAYGROUND2)$(TEST_PRODUCTION)$(TEST_CANADA)" ]; then \
		echo "FATAL: the TEST_* variables are replaced by ENDPOINT=<name>, one of: $(ENDPOINTS)" >&2; exit 2; fi
	@if [ -z "$(ENDPOINT)" ]; then \
		echo "FATAL: choose the endpoint with ENDPOINT=<name>, one of: $(ENDPOINTS)" >&2; exit 2; fi
	@if [ -z "$(filter $(ENDPOINT),$(ENDPOINTS))" ] || [ "$(words $(ENDPOINT))" != "1" ]; then \
		echo "FATAL: unknown endpoint '$(ENDPOINT)'; choose one of: $(ENDPOINTS)" >&2; exit 2; fi
	@if ! eval test -r $(ENV_FILE); then echo "FATAL: env file $(ENV_FILE) for endpoint $(ENDPOINT) is missing or unreadable" >&2; exit 2; fi
	@echo "endpoint: $(ENDPOINT) ($(ENV_FILE)), TLS verification: $(if $(RLPORTAL_NO_SSL_VERIFY),off,on)$(if $(ONLY_CATALOG), - Catalog API only)"

# Prove, before any endpoint is touched, that a failing test fails the make
# run and a passing one does not: both go through selftest-run, a recipe that
# calls pytest the way `tests` does.
selftest: venv
	@rm -rf selftest; mkdir -p selftest
	@printf 'def test_fails() -> None:\n    raise AssertionError("deliberately failing")\n' > selftest/test_fails.py
	@printf 'def test_passes() -> None:\n    pass\n' > selftest/test_passes.py
	@if $(MAKE) -s --no-print-directory selftest-run SELFTEST_MODULE=selftest/test_fails.py >/dev/null 2>&1; then \
		echo "SELFTEST FAILED: a failing test did not fail the make run" >&2; rm -rf selftest; exit 1; fi
	@if ! $(MAKE) -s --no-print-directory selftest-run SELFTEST_MODULE=selftest/test_passes.py >/dev/null 2>&1; then \
		echo "SELFTEST FAILED: a passing test failed the make run" >&2; rm -rf selftest; exit 1; fi
	@rm -rf selftest
	@echo "selftest: a failing test fails the make run, a passing one does not"

selftest-run:
	$(ACTIVATE) { $(PYTEST) $(SELFTEST_MODULE); } $(call KEEP_OUTPUT,$(basename $(SELFTEST_MODULE)))

# this breaks under globalprotect: use a local file
$(INPUT_PATH):
	mkdir -p ./input
	cp ~/Downloads/eicar/$(ARTIFACT) ./input/
	# curl -o ./input/$(ARTIFACT) -sS https://secure.eicar.org/$(ARTIFACT)

# test_clean runs before every `make ENDPOINT=<name>` and keeps results/, so the
# output of earlier runs stays available; `make clean` removes it as well.
clean: test_clean
	rm -rf results

test_clean:
	rm -rf $(PYTEST_VENV) $(MYPY_VENV) selftest input
	# what the example program writes where it runs
	rm -rf downloads* export_profile*.json *.log
	# what the old scripts left
	rm -rf $(ENDPOINTS) my ca pg1 pg2 test1 myConfig.json *.1 *.2
	rm -rf .ruff_cache */.ruff_cache __pycache__ */__pycache__

# Type-check the test code against the installed wheel: with the generated
# stubs, and with the package's own type hints (py.typed).
MYPY_SETUP := rm -rf $(MYPY_VENV); $(MIN_PYTHON_VERSION) -m venv $(MYPY_VENV); \
	source $(MYPY_VENV)/bin/activate; \
	$(PIP_INSTALL) mypy pytest types-requests $(PACKAGE_TEST_INSTALL);

mypy-stubs:
	$(MYPY_SETUP) MYPYPATH=../stubs/ mypy --strict --no-incremental *.py integration

mypy:
	$(MYPY_SETUP) mypy --strict --no-incremental *.py integration

"""Fixtures for the integration tests, which run against a live Spectra Assure Portal.

tests/Makefile chooses the endpoint: it reads the endpoint's env file from the
home directory (export KEY=VALUE lines), sets RLPORTAL_NO_SSL_VERIFY=1 for an
endpoint with a self-signed certificate, and runs pytest with --maxfail=1, so
the first failing test stops the run.

Everything a test creates on the Portal is named after the run id and deleted
when the run ends, also when a test failed.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import secrets
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
import requests

from spectra_assure_api_client import SpectraAssureApiOperations

logger = logging.getLogger(__name__)

#: How long to wait for an analysis, a report or an archive, in seconds.
WAIT_LIMIT = int(os.environ.get("RLPORTAL_WAIT_LIMIT", "1800"))
#: How long to pause between two polls, in seconds.
POLL_PAUSE = int(os.environ.get("RLPORTAL_POLL_PAUSE", "15"))

SETTINGS = {
    "host": "RLPORTAL_HOST",
    "server": "RLPORTAL_SERVER",
    "organization": "RLPORTAL_ORG",
    "group": "RLPORTAL_GROUP",
    "token": "RLPORTAL_ACCESS_TOKEN",
}
REQUIRED = ("organization", "group", "token")


# ------------------------------------------------------------------ checking responses


def expect(response: requests.Response, *codes: int) -> requests.Response:
    """Fail the test unless the response has one of these status codes (any 2xx if none are given)."""
    if (codes and response.status_code in codes) or (not codes and 200 <= response.status_code < 300):
        return response
    wanted = ", ".join(map(str, codes)) if codes else "2xx"
    request = response.request
    pytest.fail(
        f"{request.method if request else '?'} {response.url}: expected {wanted}, got {response.status_code}: "
        f"{response.text[:500]}"
    )


def until_ready(call: Callable[[], requests.Response], what: str) -> requests.Response:
    """Repeat a call while the Portal answers 202 (not ready yet), up to WAIT_LIMIT seconds."""
    deadline = time.monotonic() + WAIT_LIMIT
    while True:
        response = call()
        if response.status_code != 202:
            return response
        if time.monotonic() > deadline:
            pytest.fail(f"{what}: still 202 (not ready) after {WAIT_LIMIT} s")
        logger.info("%s: not ready yet, waiting %d s", what, POLL_PAUSE)
        time.sleep(POLL_PAUSE)


# ------------------------------------------------------------------ settings and client


class Secret(str):
    """A string that shows as '***' wherever pytest prints a value.

    A failing test's traceback includes the arguments of each function in it,
    so the token would appear in the console and in junit.xml. Formatting it
    (f"Bearer {token}") still gives the real value.
    """

    def __repr__(self) -> str:
        return "'***'"


@pytest.fixture(scope="session")
def settings() -> dict[str, Any]:
    """The endpoint's settings, from the environment the Makefile prepared."""
    found: dict[str, Any] = {
        name: os.environ[variable] for name, variable in SETTINGS.items() if os.environ.get(variable)
    }
    if "token" in found:
        found["token"] = Secret(found["token"])
    missing = [SETTINGS[name] for name in REQUIRED if name not in found]
    if "host" not in found and "server" not in found:
        missing.insert(0, "RLPORTAL_HOST or RLPORTAL_SERVER")
    if missing:
        pytest.fail(f"missing in the environment (the endpoint's env file sets them): {', '.join(missing)}")
    return found


@pytest.fixture(scope="session")
def no_ssl_verify() -> bool:
    """True only where the Makefile's endpoint table turns TLS verification off."""
    return os.environ.get("RLPORTAL_NO_SSL_VERIFY") == "1"


@pytest.fixture(scope="session")
def client(settings: dict[str, Any], no_ssl_verify: bool) -> Iterator[SpectraAssureApiOperations]:
    with SpectraAssureApiOperations(**settings, no_ssl_verify=no_ssl_verify, auto_adapt_to_throttle=True) as portal:
        yield portal


@pytest.fixture
def config_file(tmp_path: Path, settings: dict[str, Any]) -> Path:
    """A configuration file with the endpoint's settings, but not the token."""
    path = tmp_path / "myConfig.json"
    content = {name: value for name, value in settings.items() if name != "token"}
    path.write_text(json.dumps({"SpectraAssureApi": content}), encoding="utf-8")
    return path


# ------------------------------------------------------------------ run id and files


@pytest.fixture(scope="session")
def run_id() -> str:
    """sdktest-<endpoint>-<date>-<time>-<random>: every name a test creates starts with it."""
    endpoint = os.environ.get("ENV_NAME") or "local"
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"sdktest-{endpoint}-{stamp}-{secrets.token_hex(2)}"


@pytest.fixture(scope="session")
def artifact() -> Path:
    """The file the scan tests upload; the Makefile puts it in tests/input/."""
    path = Path(os.environ.get("INPUT_PATH", "input/eicarcom2.zip")).resolve()
    if not path.is_file():
        pytest.fail(f"the scan artifact {path} is missing; tests/Makefile copies it into tests/input/")
    return path


@pytest.fixture(scope="session")
def run_results_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The run's results folder when the Makefile gives one (kept until `make clean`), else a temporary folder."""
    given = os.environ.get("RLPORTAL_RESULTS")
    path = Path(given).resolve() if given else tmp_path_factory.mktemp("results")
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def results_dir(run_results_dir: Path) -> Path:
    """Where downloads go: `downloads/` in the run's results folder."""
    path = run_results_dir / "downloads"
    path.mkdir(parents=True, exist_ok=True)
    return path


# ------------------------------------------------------------------ what the run creates, and its clean-up


@dataclass
class Created:
    """Projects and packages created during the run, deleted at its end in reverse order."""

    client: SpectraAssureApiOperations
    run_id: str
    items: list[tuple[str, str | None]] = field(default_factory=list)

    def project(self, suffix: str, *, description: str | None = None) -> str:
        name = f"{self.run_id}-{suffix}"
        extra: dict[str, Any] = {"description": description} if description else {}
        expect(self.client.create(project=name, **extra), 201)
        self.items.append((name, None))
        return name

    def package(self, project: str, suffix: str, *, description: str | None = None) -> str:
        name = f"{self.run_id}-{suffix}"
        extra: dict[str, Any] = {"description": description} if description else {}
        expect(self.client.create(project=project, package=name, **extra), 201)
        self.items.append((project, name))
        return name

    def clean_up(self) -> list[str]:
        """Delete what is left; 404 means a test already deleted it. Returns what could not be deleted."""
        failed = []
        for project, package in reversed(self.items):
            response = self.client.delete(project=project, package=package)
            if response.status_code not in (204, 404):
                failed.append(f"{project}/{package or ''}: {response.status_code}")
        self.items.clear()
        return failed


@pytest.fixture(scope="session")
def created(client: SpectraAssureApiOperations, run_id: str) -> Iterator[Created]:
    registry = Created(client=client, run_id=run_id)
    yield registry
    failed = registry.clean_up()
    if failed:
        pytest.fail(f"could not delete what the run created: {'; '.join(failed)}")


# ------------------------------------------------------------------ waiting for an analysis


def wait_for_analysis(client: SpectraAssureApiOperations, *, project: str, package: str, version: str) -> None:
    """Poll the status (without asking for a download link) until the analysis is DONE.

    ERROR fails the test at once; so does running out of WAIT_LIMIT.
    """
    deadline = time.monotonic() + WAIT_LIMIT
    while True:
        response = expect(client.status(project=project, package=package, version=version), 200)
        state = str(response.json().get("analysis", {}).get("status", "")).upper()
        if state == "DONE":
            return
        if state == "ERROR":
            pytest.fail(f"the analysis of {project}/{package}@{version} ended in ERROR")
        if time.monotonic() > deadline:
            pytest.fail(
                f"the analysis of {project}/{package}@{version} is still {state or 'unknown'} after {WAIT_LIMIT} s"
            )
        logger.info("analysis of %s/%s@%s: %s, waiting %d s", project, package, version, state, POLL_PAUSE)
        time.sleep(POLL_PAUSE)

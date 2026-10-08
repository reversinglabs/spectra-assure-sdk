"""Query parameters, checked against the compiled specification for every operation that has any.

For each such operation the public call is made with every query parameter the
specification declares, plus a name it does not declare and a body field. The
query string must carry exactly the declared names: nothing dropped, nothing
invented, no body field leaking into the URL. Because the expectation comes from
the specification, a parameter added or removed there is tested without editing
this file, and a new operation with query parameters fails
`test_every_operation_with_query_parameters_is_covered` until it gets a recipe.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from spectra_assure_api_client import SpectraAssureApiOperations
from spectra_assure_api_client.spec import ROUTES, get_operation

from .support import Recorder, install, make_client

VERSION: dict[str, Any] = {"project": "pr", "package": "pk", "version": "1.0"}

Call = Callable[[SpectraAssureApiOperations, Path, dict[str, Any]], Any]


def a_file(directory: Path) -> str:
    path = directory / "artifact.bin"
    path.write_bytes(b"data")
    return str(path)


#: How to call each operation that has query parameters: (HTTP verb, call).
RECIPES: dict[str, tuple[str, Call]] = {
    "delete": ("DELETE", lambda c, d, qp: c.delete(**VERSION, **qp)),
    "report": ("GET", lambda c, d, qp: c.report(**VERSION, report_type="sarif", **qp)),
    "rl_safe": ("GET", lambda c, d, qp: c.rl_safe(**VERSION, **qp)),
    "status": ("GET", lambda c, d, qp: c.status(**VERSION, **qp)),
    "scan": ("POST", lambda c, d, qp: c.scan(**VERSION, file_path=a_file(d), **qp)),
    "url_import": ("POST", lambda c, d, qp: c.url_import(**VERSION, url="https://example.com/a.tgz", **qp)),
    "purl_import": ("POST", lambda c, d, qp: c.purl_import(**VERSION, purl="pkg:npm/a@1.0", **qp)),
    "community_find_packages": ("POST", lambda c, d, qp: c.community_find_packages(post_data=[{"a": 1}], **qp)),
    "community_report_package": (
        "GET",
        lambda c, d, qp: c.community_report_package(repository="npm", package="p", **qp),
    ),
    "community_report_version": (
        "GET",
        lambda c, d, qp: c.community_report_version(repository="npm", package="p", version="1.0", **qp),
    ),
    "filestream_list": ("GET", lambda c, d, qp: c.filestream_list(**qp)),
    "filestream_scan": ("POST", lambda c, d, qp: c.filestream_scan(file_path=a_file(d), **qp)),
    "filestream_url_import": ("POST", lambda c, d, qp: c.filestream_url_import(url="https://example.com/a.tgz", **qp)),
    "filestream_purl_import": ("POST", lambda c, d, qp: c.filestream_purl_import(purl="pkg:npm/a@1.0", **qp)),
    "filestream_status": ("GET", lambda c, d, qp: c.filestream_status(file_id="f-1", **qp)),
}


def declared_query_parameters() -> dict[str, tuple[str, ...]]:
    """action -> the query parameters the specification declares for it."""
    found: dict[str, set[str]] = {}
    for (action, _level), operation_id in ROUTES.items():
        query = get_operation(operation_id).query_params
        if query:
            found.setdefault(action, set()).update(query)
    return {action: tuple(sorted(names)) for action, names in found.items()}


def value_for(name: str) -> Any:
    """A plain value per parameter; `build` avoids `repro`, which scan combines restrictively."""
    return "v2" if name == "build" else f"value-of-{name}"


def test_every_operation_with_query_parameters_is_covered() -> None:
    assert set(RECIPES) == set(declared_query_parameters())


@pytest.mark.parametrize(("action", "declared"), sorted(declared_query_parameters().items()))
def test_exactly_the_declared_query_parameters_are_sent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, action: str, declared: tuple[str, ...]
) -> None:
    verb, call = RECIPES[action]
    recorder = install(monkeypatch, "any", Recorder())
    given = {name: value_for(name) for name in declared}

    call(make_client(), tmp_path, {**given, "not_in_the_spec": "x", "auth-pass": "secret"})

    sent = recorder.calls[-1]
    assert sent["method"] == verb
    assert sent["params"] == given  # every declared one, with its value; nothing else


@pytest.mark.parametrize(("action", "declared"), sorted(declared_query_parameters().items()))
def test_no_query_parameter_is_sent_when_none_is_given(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, action: str, declared: tuple[str, ...]
) -> None:
    _verb, call = RECIPES[action]
    recorder = install(monkeypatch, "any", Recorder())

    call(make_client(), tmp_path, {})

    assert recorder.calls[-1]["params"] == {}


def test_the_older_helpers_derive_their_parameters_from_the_specification() -> None:
    """These kept a list of their own; now they ask the specification (I-18)."""
    helpers = {
        "_qp_url_import": ("url_import", {"what": "version"}),
        "_qp_purl_import": ("purl_import", {"what": "version"}),
        "_qp_status": ("status", {"what": "version"}),
        "_qp_comm_find_packages": ("community_find_packages", {}),
        "_qp_comm_report_package": ("community_report_package", {}),
        "_qp_comm_report_version": ("community_report_version", {}),
    }
    declared = declared_query_parameters()
    for helper, (action, level) in helpers.items():
        bag = dict.fromkeys(declared[action], 1) | {"not_in_the_spec": 1}
        kept = getattr(SpectraAssureApiOperations, helper)(**level, **bag)
        assert set(kept) == set(declared[action]), helper


@pytest.mark.parametrize("helper", ["_qp_url_import", "_qp_purl_import", "_qp_status"])
def test_the_version_helpers_keep_nothing_below_version_level(helper: str) -> None:
    assert getattr(SpectraAssureApiOperations, helper)(what="package", replace=True, build="v2") == {}

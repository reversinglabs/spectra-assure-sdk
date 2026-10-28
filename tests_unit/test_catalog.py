"""Catalog operations.

The paths sit under `/catalog/...`, off the group/project/package/version
ladder; their `{project}` and `{package}` come from the SDK's `project` and
`package` arguments. The checks here are about those URLs, the
request bodies built from named arguments, and the separation from the
purl-based calls.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from spectra_assure_api_client import (
    SpectraAssureApiOperations,
    SpectraAssureInvalidAction,
)
from spectra_assure_api_client.spec import ROUTES, get_operation, operation_ids

from .support import BASE, Recorder, install, make_client

Call = Callable[[SpectraAssureApiOperations], Any]


@pytest.fixture
def client() -> SpectraAssureApiOperations:
    return make_client()


# ------------------------------------------------------------------ routing


def test_every_catalog_operation_is_compiled() -> None:
    """The seven Catalog operations of the specification."""
    catalog = {op for op in operation_ids() if get_operation(op).path.startswith("/catalog/")}
    assert catalog == {
        "getExternalCatalog",
        "listCatalogPackages",
        "importFromCatalog",
        "updateFromCatalog",
        "publishPackageToCatalog",
        "unpublishPackageFromCatalog",
        "detachFromCatalog",
    }


def test_every_catalog_method_is_named_after_its_operation() -> None:
    """The method names are the operation ids in snake case."""
    for (action, what), operation_id in ROUTES.items():
        if what != "catalog":
            continue
        snake = "".join(f"_{c.lower()}" if c.isupper() else c for c in operation_id)
        assert action == snake, operation_id
        assert callable(getattr(SpectraAssureApiOperations, action))


def test_the_catalog_routes_are_not_on_the_purl_ladder() -> None:
    """`_what` never returns "catalog", so a purl call cannot land on a catalog route."""
    levels = {
        SpectraAssureApiOperations._what(),
        SpectraAssureApiOperations._what(project="pr"),
        SpectraAssureApiOperations._what(project="pr", package="pk"),
        SpectraAssureApiOperations._what(project="pr", package="pk", version="1"),
    }
    assert "catalog" not in levels
    assert {what for (_action, what), op in ROUTES.items() if get_operation(op).path.startswith("/catalog/")} == {
        "catalog"
    }


#: method -> (call, HTTP verb, URL after BASE)
CALLS: dict[str, tuple[Call, str, str]] = {
    "get_external_catalog": (
        lambda c: c.get_external_catalog(catalog="reversinglabs"),
        "GET",
        "/catalog/list/reversinglabs",
    ),
    "list_catalog_packages": (
        lambda c: c.list_catalog_packages(),
        "GET",
        "/catalog/list/Org/Grp",
    ),
    "import_from_catalog": (
        lambda c: c.import_from_catalog(
            catalog="reversinglabs", project="pr", package="pk", software_id="RL1", stream="RL1-S"
        ),
        "POST",
        "/catalog/import/Org/Grp/reversinglabs/pkg:rl/pr/pk",
    ),
    "update_from_catalog": (
        lambda c: c.update_from_catalog(project="pr", package="pk"),
        "POST",
        "/catalog/update/Org/Grp/pkg:rl/pr/pk",
    ),
    "publish_package_to_catalog": (
        lambda c: c.publish_package_to_catalog(project="pr", package="pk"),
        "PUT",
        "/catalog/publish/Org/Grp/pkg:rl/pr/pk",
    ),
    "unpublish_package_from_catalog": (
        lambda c: c.unpublish_package_from_catalog(project="pr", package="pk"),
        "DELETE",
        "/catalog/publish/Org/Grp/pkg:rl/pr/pk",
    ),
    "detach_from_catalog": (
        lambda c: c.detach_from_catalog(project="pr", package="pk"),
        "DELETE",
        "/catalog/detach/Org/Grp/pkg:rl/pr/pk",
    ),
}


def test_every_catalog_route_has_a_call() -> None:
    assert sorted(CALLS) == sorted(action for (action, what) in ROUTES if what == "catalog")


@pytest.mark.parametrize("method", sorted(CALLS))
def test_each_call_uses_its_verb_and_url(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    method: str,
) -> None:
    call, verb, path = CALLS[method]
    recorder = install(monkeypatch, verb.lower(), Recorder())

    call(client)

    assert recorder.calls[0]["method"] == verb
    assert recorder.calls[0]["url"] == BASE + path
    assert recorder.calls[0]["params"] == {}  # no catalog operation declares query parameters


def test_path_values_are_percent_encoded(monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations) -> None:
    """A '/', '@' or space in a name cannot change the shape of the URL."""
    recorder = install(monkeypatch, "post", Recorder())

    client.import_from_catalog(catalog="a/b", project="p r", package="k@1", software_id="RL1", stream="RL1-S")

    assert recorder.calls[0]["url"] == f"{BASE}/catalog/import/Org/Grp/a%2Fb/pkg:rl/p%20r/k%401"


# ------------------------------------------------------------------ bodies


def test_import_sends_the_required_fields_only_when_nothing_else_is_given(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    recorder = install(monkeypatch, "post", Recorder())

    client.import_from_catalog(catalog="reversinglabs", project="pr", package="pk", software_id="RL1", stream="RL1-S")

    assert recorder.calls[0]["json"] == {"software_id": "RL1", "stream": "RL1-S"}


def test_import_sends_every_given_field(monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations) -> None:
    """False is a value and is sent; it is not mistaken for "not given"."""
    recorder = install(monkeypatch, "post", Recorder())

    client.import_from_catalog(
        catalog="reversinglabs",
        project="pr",
        package="pk",
        software_id="RL1",
        stream="RL1-S",
        versions=["24.07", "24.08"],
        auto_sync=False,
        project_description="pd",
        package_description="kd",
        notify_on_completion=True,
    )

    assert recorder.calls[0]["json"] == {
        "software_id": "RL1",
        "stream": "RL1-S",
        "versions": ["24.07", "24.08"],
        "auto_sync": False,
        "project_description": "pd",
        "package_description": "kd",
        "notify_on_completion": True,
    }
    assert set(recorder.calls[0]["json"]) == set(get_operation("importFromCatalog").body_properties)


def test_import_leaves_lengths_to_the_portal(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations
) -> None:
    """The specification caps descriptions at 500 characters; the SDK passes longer ones on."""
    recorder = install(monkeypatch, "post", Recorder())

    client.import_from_catalog(
        catalog="reversinglabs",
        project="pr",
        package="pk",
        software_id="RL1",
        stream="RL1-S",
        package_description="x" * 501,
    )

    assert len(recorder.calls[0]["json"]["package_description"]) == 501


@pytest.mark.parametrize("missing", ["software_id", "stream"])
def test_import_refuses_an_empty_required_field(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    missing: str,
) -> None:
    recorder = install(monkeypatch, "post", Recorder())
    software_id = "" if missing == "software_id" else "RL1"
    stream = "" if missing == "stream" else "RL1-S"

    with pytest.raises(SpectraAssureInvalidAction, match=missing):
        client.import_from_catalog(
            catalog="reversinglabs", project="pr", package="pk", software_id=software_id, stream=stream
        )

    assert recorder.calls == []


def test_update_without_arguments_sends_no_body(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    """The specification makes the body optional; nothing to say means no body."""
    recorder = install(monkeypatch, "post", Recorder())

    client.update_from_catalog(project="pr", package="pk")

    assert recorder.calls[0]["json_passed"] is False


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"versions": ["24.09"]}, {"versions": ["24.09"]}),
        ({"versions": []}, {"versions": []}),
        ({"notify_on_completion": False}, {"notify_on_completion": False}),
        ({"versions": ["1"], "notify_on_completion": True}, {"versions": ["1"], "notify_on_completion": True}),
    ],
)
def test_update_sends_what_is_given(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    kwargs: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    recorder = install(monkeypatch, "post", Recorder())

    client.update_from_catalog(project="pr", package="pk", **kwargs)

    assert recorder.calls[0]["json"] == expected


@pytest.mark.parametrize(
    "method",
    ["get_external_catalog", "list_catalog_packages", "publish_package_to_catalog", "unpublish_package_from_catalog"]
    + ["detach_from_catalog"],
)
def test_calls_without_a_body_send_none(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    method: str,
) -> None:
    call, verb, _path = CALLS[method]
    recorder = install(monkeypatch, verb.lower(), Recorder())

    call(client)

    assert recorder.calls[0]["json_passed"] is False

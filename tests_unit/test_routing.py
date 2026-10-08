"""Routing and parameter handling, driven by the compiled specification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import requests

from spectra_assure_api_client import (
    SpectraAssureApiOperations,
    SpectraAssureInvalidAction,
)
from spectra_assure_api_client.spec import (
    ROUTES,
    SpectraAssureSpecError,
    get_operation,
    operation_ids,
    resolve,
    routed_operation_ids,
)

from .support import BASE, Recorder, install, make_client, make_response


@pytest.fixture
def client() -> SpectraAssureApiOperations:
    return make_client()


# ----------------------------------------------------------- the spec table


def test_every_route_points_at_a_real_operation() -> None:
    for (action, what), operation_id in ROUTES.items():
        operation = get_operation(operation_id)
        assert operation.operation_id == operation_id, (action, what)


def test_scim_operations_are_not_reachable() -> None:
    """SCIM is deliberately out of scope and must not leak into the surface."""
    scim = [op for op in operation_ids() if op.lower().endswith("user") or "Users" in op]
    assert scim == []
    assert not any("scim" in get_operation(op).path.lower() for op in operation_ids())


def test_every_compiled_operation_is_routed() -> None:
    """No operation should sit in the table unreachable from the public API."""
    unrouted = set(operation_ids()) - routed_operation_ids()
    assert unrouted == set(), f"operations present but unreachable: {sorted(unrouted)}"


def test_unknown_action_is_reported_as_an_invalid_action(client: SpectraAssureApiOperations) -> None:
    with pytest.raises(SpectraAssureInvalidAction):
        client._make_current_url(action="teleport", project="pr")


def test_unsupported_level_names_the_levels_that_work() -> None:
    with pytest.raises(SpectraAssureSpecError) as exc:
        resolve("scan", "project")
    assert "version" in str(exc.value)


# ------------------------------------------------------------------- URLs


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({}, f"{BASE}/list/Org/Grp"),
        ({"project": "pr"}, f"{BASE}/list/Org/Grp/pkg:rl/pr"),
        ({"project": "pr", "package": "pk"}, f"{BASE}/list/Org/Grp/pkg:rl/pr/pk"),
        ({"project": "pr", "package": "pk", "version": "1.0"}, f"{BASE}/list/Org/Grp/pkg:rl/pr/pk@1.0"),
    ],
)
def test_list_walks_down_the_ladder(client: SpectraAssureApiOperations, kwargs: dict[str, Any], expected: str) -> None:
    assert client._make_current_url(action="list", **kwargs) == expected


def test_path_values_are_percent_encoded(client: SpectraAssureApiOperations) -> None:
    url = client._make_current_url(action="list", project="a b/c", package="p@k", version="1 0")
    assert url == f"{BASE}/list/Org/Grp/pkg:rl/a%20b%2Fc/p%40k@1%200"


def test_purl_separators_are_not_encoded(client: SpectraAssureApiOperations) -> None:
    """`pkg:rl/`, `/` and `@` are template syntax, not data."""
    url = client._make_current_url(action="list", project="pr", package="pk", version="1.0")
    assert "pkg:rl/" in url
    assert url.endswith("@1.0")


def test_report_type_is_a_path_segment(client: SpectraAssureApiOperations) -> None:
    url = client._make_current_url(action="report", project="pr", package="pk", version="1.0", report_type="sbom")
    assert url == f"{BASE}/report/Org/Grp/sbom/pkg:rl/pr/pk@1.0"


def test_community_paths_tolerate_an_absent_version(client: SpectraAssureApiOperations) -> None:
    with_version = client._make_current_url_community(
        action="community_report_package", repository="npm", package="ns/p", version="1.0"
    )
    without = client._make_current_url_community(action="community_report_package", repository="npm", package="ns/p")
    assert with_version == f"{BASE}/community/report/package/pkg:npm/ns/p@1.0"
    assert without == f"{BASE}/community/report/package/pkg:npm/ns/p"


# ------------------------------------------------- parameter allow-listing


def test_unknown_parameters_are_dropped_not_rejected(client: SpectraAssureApiOperations) -> None:
    """Callers share one argument bag across operations that accept different subsets."""
    accepted = client._accepted("create", "project", {"description": "d", "nonsense": "x"})
    assert accepted == {"description": "d"}


def test_parameters_are_scoped_to_the_level_they_apply_at(client: SpectraAssureApiOperations) -> None:
    assert client._qp_edit(what="project", is_released=True) == {}
    assert client._qp_edit(what="version", is_released=True) == {"is_released": True}


def test_repro_builds_reject_incompatible_parameters(client: SpectraAssureApiOperations) -> None:
    with pytest.raises(SpectraAssureInvalidAction, match="force"):
        client._qp_scan(what="version", build="repro", force=True)

    with pytest.raises(SpectraAssureInvalidAction, match="diff_with"):
        client._qp_scan(what="version", build="repro", diff_with="0.9")

    # the same parameters are fine against any other build
    assert client._qp_scan(what="version", build="version", force=True) == {
        "build": "version",
        "force": True,
    }


def test_import_operations_accept_max_size_but_not_build(client: SpectraAssureApiOperations) -> None:
    accepted = client._accepted("url_import", "version", {"max_size": 10, "build": "version"})
    assert accepted == {"max_size": 10}


# ------------------------------------------------------- where values land


def test_delete_sends_build_as_a_query_parameter(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    """Regression: this value used to be computed and then discarded."""
    recorder = install(monkeypatch, "delete", Recorder())

    client.delete(project="pr", package="pk", version="1.0", build="repro")

    assert recorder.calls[0]["params"] == {"build": "repro"}


def test_approval_reason_travels_in_the_body(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    recorder = install(monkeypatch, "put", Recorder())

    client.approve(project="pr", package="pk", version="1.0", reason="looks fine")

    assert recorder.calls[0]["json"] == {"reason": "looks fine"}


def test_scan_metadata_travels_in_the_query_string(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
) -> None:
    upload = tmp_path / "a.bin"
    upload.write_bytes(b"x")

    recorder = install(monkeypatch, "post", Recorder())

    client.scan(project="pr", package="pk", version="1.0", file_path=str(upload), publisher="RL", build="version")

    assert recorder.calls[0]["params"] == {"publisher": "RL", "build": "version"}


def test_usage_group_argument_overrides_the_session_group(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    recorder = install(monkeypatch, "get", Recorder())

    client.usage(group="Another")

    assert recorder.calls[0]["url"] == f"{BASE}/usage/Org/Another"


# ------------------------------------------------- body vs query placement


def test_create_sends_its_description(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    """Regression: body properties were once filtered out of the query string
    and never added to the body, so create() silently discarded `description`.
    """
    recorder = install(monkeypatch, "post", Recorder())

    client.create(project="pr", description="a description")

    call = recorder.calls[0]
    sent = {**(call["params"] or {}), **(call["json"] or {})}
    assert sent.get("description") == "a description"


def test_body_params_travel_in_the_body_only(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    """Body properties in the body, query parameters in the query string."""
    recorder = install(monkeypatch, "post", Recorder())

    client.create(project="pr", package="pk", description="a description")

    call = recorder.calls[0]
    assert call["json"] == {"description": "a description"}
    assert call["params"] == {}


def test_no_ssl_verify_is_unset_until_supplied() -> None:
    """The constructor must tell 'not supplied' from 'supplied as False'.

    Regression: a plain `bool = False` default made the two indistinguishable,
    so the constructor always overrode `no_ssl_verify` from a config file.
    """
    assert make_client().no_ssl_verify is None
    assert make_client(no_ssl_verify=True).no_ssl_verify is True
    assert make_client(no_ssl_verify=False).no_ssl_verify is False


# ---------------------------------------------- requests without a body


@pytest.mark.parametrize(
    ("label", "call"),
    [
        ("get", lambda c: c.list(project="pr")),
        ("delete", lambda c: c.delete(project="pr", package="pk", version="1.0")),
        ("delete with a query parameter", lambda c: c.delete(project="pr", package="pk", version="1.0", build="repro")),
        ("post without parameters", lambda c: c.sync(project="pr", package="pk", version="1.0")),
        ("filestream post", lambda c: c.filestream_sync(file_id="abc")),
    ],
)
def test_calls_with_nothing_to_say_send_no_body(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    label: str,
    call: Any,
) -> None:
    """Regression: these used to serialise an empty argument bag as `{}`.

    A two-byte body on a GET is unusual, and on a kept-alive connection anything
    that fails to drain it corrupts the next request on that socket.
    """
    recorder = Recorder()
    monkeypatch.setattr(requests.Session, "request", recorder)

    call(client)

    assert recorder.calls[0]["json_passed"] is False, label


@pytest.mark.parametrize(
    ("label", "call", "expected"),
    [
        ("create", lambda c: c.create(project="pr", description="d"), {"description": "d"}),
        ("approve", lambda c: c.approve(project="pr", package="pk", version="1.0", reason="ok"), {"reason": "ok"}),
        ("edit", lambda c: c.edit(project="pr", name="n"), {"name": "n"}),
    ],
)
def test_calls_with_a_body_still_send_it(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    label: str,
    call: Any,
    expected: dict[str, Any],
) -> None:
    recorder = Recorder()
    monkeypatch.setattr(requests.Session, "request", recorder)

    call(client)

    assert recorder.calls[0]["json"] == expected, label


def test_an_empty_list_body_is_still_a_body(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    """Only None and {} count as absent; an empty list is a real payload."""
    recorder = Recorder()
    monkeypatch.setattr(requests.Session, "request", recorder)

    client.community_find_packages(post_data=[])

    assert recorder.calls[0]["json_passed"] is True
    assert recorder.calls[0]["json"] == []


def test_a_get_goes_out_with_no_body_and_no_content_length(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    """Checked on the prepared request, which is what actually reaches the wire."""
    captured: dict[str, Any] = {}

    def prepare(self: Any, method: str, url: str, **kw: Any) -> requests.Response:
        request = requests.Request(method, url, params=kw.get("params"), headers=kw.get("headers"), json=kw.get("json"))
        prepared = requests.Session().prepare_request(request)
        captured["body"] = prepared.body
        captured["content_length"] = prepared.headers.get("Content-Length")
        return make_response()

    monkeypatch.setattr(requests.Session, "request", prepare)

    client.list(project="pr")

    assert captured["body"] is None
    assert captured["content_length"] is None


def test_a_bodyless_post_still_declares_zero_length(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    """A POST with no body must still say so: Content-Length: 0."""
    captured: dict[str, Any] = {}

    def prepare(self: Any, method: str, url: str, **kw: Any) -> requests.Response:
        prepared = requests.Session().prepare_request(
            requests.Request(method, url, params=kw.get("params"), headers=kw.get("headers"), json=kw.get("json"))
        )
        captured["body"] = prepared.body
        captured["content_length"] = prepared.headers.get("Content-Length")
        return make_response()

    monkeypatch.setattr(requests.Session, "request", prepare)

    client.sync(project="pr", package="pk", version="1.0")

    assert captured["body"] is None
    assert captured["content_length"] == "0"


def test_a_bodyless_request_declares_no_content_type(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    """Content-Type describes a body; with no body there is nothing to describe."""
    captured: dict[str, Any] = {}

    def prepare(self: Any, method: str, url: str, **kw: Any) -> requests.Response:
        prepared = requests.Session().prepare_request(
            requests.Request(method, url, params=kw.get("params"), headers=kw.get("headers"), json=kw.get("json"))
        )
        captured["content_type"] = prepared.headers.get("Content-Type")
        return make_response()

    monkeypatch.setattr(requests.Session, "request", prepare)

    client.list(project="pr")

    assert captured["content_type"] is None


def test_a_request_with_a_body_still_declares_json(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    captured: dict[str, Any] = {}

    def prepare(self: Any, method: str, url: str, **kw: Any) -> requests.Response:
        prepared = requests.Session().prepare_request(
            requests.Request(method, url, params=kw.get("params"), headers=kw.get("headers"), json=kw.get("json"))
        )
        captured["content_type"] = prepared.headers.get("Content-Type")
        return make_response()

    monkeypatch.setattr(requests.Session, "request", prepare)

    client.approve(project="pr", package="pk", version="1.0", reason="ok")

    assert captured["content_type"] == "application/json"


def test_dropping_content_type_does_not_mutate_the_executor(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    """An Executor is re-used across retries, so its headers must survive a send."""
    from spectra_assure_api_client.communication.core import Executor

    executor = Executor(
        url="https://example.invalid/x",
        proxies={},
        timeout=10,
        payload={},
        headers={"Authorization": "Bearer x", "Content-Type": "application/json"},
        url_params=None,
        method="GET",
        session=requests.Session(),
    )

    monkeypatch.setattr(requests.Session, "request", lambda *a, **kw: make_response())

    executor.execute()
    executor.execute()

    assert executor.headers["Content-Type"] == "application/json"

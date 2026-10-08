"""POST bodies: each call says what it sends, and what it sends is what the specification declares (I-23).

`_post` takes an explicit body kind instead of inferring it from the action's
name. For every POST route the public call is made, and the request must carry
the kind of body the specification's media type declares.
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from spectra_assure_api_client import SpectraAssureApiOperations, SpectraAssureInvalidAction
from spectra_assure_api_client.spec import ROUTES, get_operation

from .support import ORGANIZATION, Recorder, install, make_client

PACKAGE = Path(__file__).resolve().parents[1] / "spectra_assure_api_client"
VERSION: dict[str, Any] = {"project": "pr", "package": "pk", "version": "1.0"}

Call = Callable[[SpectraAssureApiOperations, Path], Any]


def a_file(directory: Path, name: str = "artifact.bin") -> str:
    path = directory / name
    path.write_bytes(b"data")
    return str(path)


#: (action, level) of every POST route -> how to call it.
POSTS: dict[tuple[str, str], Call] = {
    ("create", "project"): lambda c, d: c.create(project="pr", description="d"),
    ("create", "package"): lambda c, d: c.create(project="pr", package="pk", description="d"),
    ("scan", "version"): lambda c, d: c.scan(**VERSION, file_path=a_file(d)),
    ("sync", "version"): lambda c, d: c.sync(**VERSION),
    ("url_import", "version"): lambda c, d: c.url_import(**VERSION, url="https://example.com/a.tgz"),
    ("purl_import", "version"): lambda c, d: c.purl_import(**VERSION, purl="pkg:npm/a@1.0"),
    ("community_find_packages", "community"): lambda c, d: c.community_find_packages(post_data=[{"a": 1}]),
    ("audit_log_export", "organization"): lambda c, d: c.audit_log_export(
        name="n", datetime_start="a", datetime_end="b"
    ),
    ("import_profile", "organization"): lambda c, d: c.import_profile(
        organization=ORGANIZATION, file_path=a_file(d, "p.json")
    ),
    ("import_profile", "group"): lambda c, d: c.import_profile(
        organization=ORGANIZATION, group="g2", file_path=a_file(d, "p.json")
    ),
    ("filestream_scan", "filestream"): lambda c, d: c.filestream_scan(file_path=a_file(d)),
    ("filestream_url_import", "filestream"): lambda c, d: c.filestream_url_import(url="https://example.com/a.tgz"),
    ("filestream_purl_import", "filestream"): lambda c, d: c.filestream_purl_import(purl="pkg:npm/a@1.0"),
    ("filestream_sync", "filestream"): lambda c, d: c.filestream_sync(file_id="f-1"),
}


def post_routes() -> list[tuple[str, str]]:
    return sorted(key for key, operation_id in ROUTES.items() if get_operation(operation_id).method.upper() == "POST")


def body_sent(call: dict[str, Any]) -> str:
    """What kind of body a recorded request carried."""
    if call["files"]:
        return "form"
    if call["json_passed"] and call["json"] is not None:
        return "json"
    if isinstance(call["body_bytes"], bytes) and call["body_bytes"]:
        return "file"
    return "none"


def declared(operation_media: tuple[str, ...]) -> str:
    if "application/octet-stream" in operation_media:
        return "file"
    if "multipart/form-data" in operation_media:
        return "form"
    if "application/json" in operation_media:
        return "json"
    return "none"


def test_every_post_route_has_a_recipe() -> None:
    assert sorted(POSTS) == post_routes()


@pytest.mark.parametrize("route", post_routes(), ids=lambda r: f"{r[0]}@{r[1]}")
def test_each_post_sends_the_body_its_specification_declares(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, route: tuple[str, str]
) -> None:
    recorder = install(monkeypatch, "post", Recorder())

    POSTS[route](make_client(), tmp_path)

    expected = declared(get_operation(ROUTES[route]).body_media_types)
    assert body_sent(recorder.calls[-1]) == expected
    if expected == "file":
        assert recorder.calls[-1]["headers"]["Content-Type"] == "application/octet-stream"


def test_a_json_body_whose_fields_are_all_optional_is_left_out_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """create without a description sends no body, as it always did."""
    recorder = install(monkeypatch, "post", Recorder())

    make_client().create(project="pr")

    assert body_sent(recorder.calls[-1]) == "none"


# ------------------------------------------------------------------ _post itself


def test_query_parameters_never_become_the_body(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = install(monkeypatch, "post", Recorder())

    make_client()._post(action="x", url="https://example.com/x", body="none", auto_adapt_to_throttle=None, flag=1)  # noqa: SLF001

    assert recorder.calls[-1]["params"] == {"flag": 1}
    assert body_sent(recorder.calls[-1]) == "none"


def test_a_body_kind_of_none_refuses_post_data(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = install(monkeypatch, "post", Recorder())

    with pytest.raises(SpectraAssureInvalidAction, match="sends no request body, but post_data was given"):
        make_client()._post(  # noqa: SLF001
            action="x", url="https://example.com/x", body="none", auto_adapt_to_throttle=None, post_data={"a": 1}
        )

    assert recorder.calls == []


def test_an_unknown_body_kind_is_refused() -> None:
    with pytest.raises(SpectraAssureInvalidAction, match="unknown body kind 'xml'"):
        make_client()._post(action="x", url="https://example.com/x", body="xml", auto_adapt_to_throttle=None)  # type: ignore[arg-type]  # noqa: SLF001


# ------------------------------------------------------------------ the legacy entry point


@pytest.mark.parametrize(
    ("action", "post_data", "qp", "expected"),
    [
        ("scan", None, {}, "file"),
        ("url_import", {"url": "u"}, {}, "json"),
        ("import_org_profile", {"replace": True}, {}, "form"),
        ("anything", {"a": 1}, {}, "json"),
        ("anything", None, {"a": 1}, "json"),  # its old quirk: the query parameters double as the body
        ("anything", None, {}, "none"),
    ],
)
def test_the_legacy_do_it_post_still_infers_the_body_from_the_action(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, action: str, post_data: Any, qp: dict[str, Any], expected: str
) -> None:
    """Kept unchanged for the deprecated do_it_post alias; the SDK itself no longer uses it."""
    recorder = install(monkeypatch, "post", Recorder())
    file_path = a_file(tmp_path) if expected in ("file", "form") else None

    make_client()._do_it_post(  # noqa: SLF001
        action=action,
        url="https://example.com/x",
        auto_adapt_to_throttle=None,
        file_path=file_path,
        post_data=post_data,
        **qp,
    )

    assert body_sent(recorder.calls[-1]) == expected


def test_the_sdk_never_infers_a_body_from_an_action_name() -> None:
    """Outside post.py, the only reference to _do_it_post is the deprecated alias's type declaration."""
    users = sorted(
        path.name
        for path in PACKAGE.rglob("*.py")
        if path.name != "post.py"
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Attribute) and node.attr == "_do_it_post"
    )

    assert users == ["spectra_assure_api_operations.py"]

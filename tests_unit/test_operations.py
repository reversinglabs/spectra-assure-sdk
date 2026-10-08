"""The request each simple operation sends: method, URL, query string and body.

These operations had no unit test at all. Each test checks the request against
what the compiled specification declares for that operation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import requests

from spectra_assure_api_client import SpectraAssureApiOperations, SpectraAssureInvalidAction

from .support import GROUP, ORGANIZATION, Recorder, install, make_client

VERSION: dict[str, Any] = {"project": "pr", "package": "pk", "version": "1.0"}


@pytest.fixture
def client() -> SpectraAssureApiOperations:
    return make_client()


@pytest.fixture
def sent(monkeypatch: pytest.MonkeyPatch) -> Recorder:
    return install(monkeypatch, "any", Recorder())


def only(recorder: Recorder) -> dict[str, Any]:
    assert len(recorder.calls) == 1, recorder.calls
    return recorder.calls[0]


def path_of(client: SpectraAssureApiOperations, call: dict[str, Any]) -> str:
    assert call["url"].startswith(client.base_url)
    return str(call["url"][len(client.base_url) :])


# ------------------------------------------------------------------ url_import / purl_import


IMPORTS = [
    ("url_import", "url", "https://example.com/pkg.tgz", "/url-import/"),
    ("purl_import", "purl", "pkg:npm/left-pad@1.3.0", "/purl-import/"),
]


@pytest.mark.parametrize(("method", "field", "value", "prefix"), IMPORTS)
def test_an_import_posts_the_source_in_the_body_and_the_options_in_the_query(
    client: SpectraAssureApiOperations, sent: Recorder, method: str, field: str, value: str, prefix: str
) -> None:
    getattr(client, method)(**VERSION, **{field: value}, replace=True, max_size=100, not_a_parameter=1)

    call = only(sent)
    assert call["method"] == "POST"
    assert path_of(client, call) == f"{prefix}{ORGANIZATION}/{GROUP}/pkg:rl/pr/pk@1.0"
    assert call["json"] == {field: value}
    assert call["params"] == {"replace": True, "max_size": 100}  # unknown names are dropped


# ------------------------------------------------------------------ one set of import rules (I-22)

#: All four import calls, with what each needs: (call, source field, a valid value, a target).
ALL_IMPORTS: list[tuple[str, str, str, dict[str, Any]]] = [
    ("url_import", "url", "https://example.com/pkg.tgz", VERSION),
    ("purl_import", "purl", "pkg:npm/left-pad@1.3.0", VERSION),
    ("filestream_url_import", "url", "https://example.com/pkg.tgz", {}),
    ("filestream_purl_import", "purl", "pkg:npm/left-pad@1.3.0", {}),
]
IMPORT_IDS = [entry[0] for entry in ALL_IMPORTS]


@pytest.mark.parametrize(("method", "field", "value", "target"), ALL_IMPORTS, ids=IMPORT_IDS)
def test_an_import_sends_a_user_name_and_password(
    client: SpectraAssureApiOperations, sent: Recorder, method: str, field: str, value: str, target: dict[str, Any]
) -> None:
    getattr(client, method)(**target, **{field: value}, auth_user="u", auth_pass="p")  # noqa: S106

    assert only(sent)["json"] == {field: value, "auth-user": "u", "auth-pass": "p"}


@pytest.mark.parametrize(("method", "field", "value", "target"), ALL_IMPORTS, ids=IMPORT_IDS)
def test_an_import_sends_a_bearer_token_on_its_own(
    client: SpectraAssureApiOperations, sent: Recorder, method: str, field: str, value: str, target: dict[str, Any]
) -> None:
    getattr(client, method)(**target, **{field: value}, bearer_token="b")  # noqa: S106

    assert only(sent)["json"] == {field: value, "bearer-token": "b"}


@pytest.mark.parametrize(("method", "field", "value", "target"), ALL_IMPORTS, ids=IMPORT_IDS)
@pytest.mark.parametrize("other", [{"auth_user": "u"}, {"auth_pass": "p"}, {"auth_user": "u", "auth_pass": "p"}])
def test_a_bearer_token_with_a_user_name_or_password_is_refused(
    client: SpectraAssureApiOperations,
    sent: Recorder,
    method: str,
    field: str,
    value: str,
    target: dict[str, Any],
    other: dict[str, str],
) -> None:
    """The specification: a bearer token cannot be used with a user name and password."""
    with pytest.raises(SpectraAssureInvalidAction, match="bearer token cannot be combined"):
        getattr(client, method)(**target, **{field: value}, bearer_token="b", **other)  # noqa: S106

    assert sent.calls == []


@pytest.mark.parametrize(("method", "field", "value", "target"), ALL_IMPORTS, ids=IMPORT_IDS)
def test_an_empty_credential_counts_as_not_given(
    client: SpectraAssureApiOperations, sent: Recorder, method: str, field: str, value: str, target: dict[str, Any]
) -> None:
    getattr(client, method)(**target, **{field: value}, auth_user="", auth_pass="", bearer_token="")

    assert only(sent)["json"] == {field: value}


@pytest.mark.parametrize(
    ("method", "field", "bad", "target", "match"),
    [
        ("url_import", "url", "example.com/pkg.tgz", VERSION, "no '://'"),
        ("filestream_url_import", "url", "example.com/pkg.tgz", {}, "no '://'"),
        ("purl_import", "purl", "npm/left-pad@1.3.0", VERSION, "must start with 'pkg:'"),
        ("filestream_purl_import", "purl", "npm/left-pad@1.3.0", {}, "must start with 'pkg:'"),
    ],
)
def test_every_import_checks_its_source(
    client: SpectraAssureApiOperations,
    sent: Recorder,
    method: str,
    field: str,
    bad: str,
    target: dict[str, Any],
    match: str,
) -> None:
    """filestream_purl_import used to skip the 'pkg:' check that purl_import applies."""
    with pytest.raises(SpectraAssureInvalidAction, match=match):
        getattr(client, method)(**target, **{field: bad})

    assert sent.calls == []


def test_url_import_refuses_a_url_without_a_scheme(client: SpectraAssureApiOperations, sent: Recorder) -> None:
    with pytest.raises(SpectraAssureInvalidAction, match="no '://'"):
        client.url_import(**VERSION, url="example.com/pkg.tgz")

    assert sent.calls == []


@pytest.mark.parametrize("purl", ["npm/left-pad@1.3.0", "https://example.com"])
def test_purl_import_refuses_a_value_that_is_not_a_purl(
    client: SpectraAssureApiOperations, sent: Recorder, purl: str
) -> None:
    with pytest.raises(SpectraAssureInvalidAction, match="must start with 'pkg:'"):
        client.purl_import(**VERSION, purl=purl)

    assert sent.calls == []


def test_purl_import_accepts_an_upper_case_scheme(client: SpectraAssureApiOperations, sent: Recorder) -> None:
    client.purl_import(**VERSION, purl="PKG:npm/left-pad@1.3.0")

    assert only(sent)["json"] == {"purl": "PKG:npm/left-pad@1.3.0"}


@pytest.mark.parametrize(("method", "field", "value", "prefix"), IMPORTS)
def test_an_import_is_refused_below_version_level(
    client: SpectraAssureApiOperations, sent: Recorder, method: str, field: str, value: str, prefix: str
) -> None:
    with pytest.raises(SpectraAssureInvalidAction, match="only supported for version"):
        getattr(client, method)(project="pr", package="pk", version=None, **{field: value})

    assert sent.calls == []


@pytest.mark.parametrize("helper", ["_qp_url_import", "_qp_purl_import"])
def test_the_import_parameter_helpers_keep_nothing_below_version_level(helper: str) -> None:
    keep = getattr(SpectraAssureApiOperations, helper)

    assert keep(what="version", replace=True, other=1) == {"replace": True}
    assert keep(what="package", replace=True) == {}


# ------------------------------------------------------------------ report / checks


def test_report_puts_the_lower_cased_type_in_the_path(client: SpectraAssureApiOperations, sent: Recorder) -> None:
    client.report(**VERSION, report_type="CycloneDX", build="repro", ignored=1)

    call = only(sent)
    assert call["method"] == "GET"
    assert path_of(client, call) == f"/report/{ORGANIZATION}/{GROUP}/cyclonedx/pkg:rl/pr/pk@1.0"
    assert call["params"] == {"build": "repro"}


def test_report_is_refused_below_version_level(client: SpectraAssureApiOperations, sent: Recorder) -> None:
    with pytest.raises(SpectraAssureInvalidAction, match="only supported for version"):
        client.report(project="pr", package="pk", version=None, report_type="sarif")  # type: ignore[arg-type]

    assert sent.calls == []


def test_checks_gets_the_version_checks(client: SpectraAssureApiOperations, sent: Recorder) -> None:
    client.checks(**VERSION)

    call = only(sent)
    assert (call["method"], path_of(client, call), call["params"]) == (
        "GET",
        f"/checks/{ORGANIZATION}/{GROUP}/pkg:rl/pr/pk@1.0",
        {},
    )


# ------------------------------------------------------------------ audit log


def test_audit_log_export_posts_the_job_definition(client: SpectraAssureApiOperations, sent: Recorder) -> None:
    client.audit_log_export(
        name="q3",
        datetime_start="2026-07-01T00:00:00Z",
        datetime_end="2026-09-30T00:00:00Z",
        should_create_cef=True,
        filters=[{"field": "user", "value": "x"}],
        ignored=1,
    )

    call = only(sent)
    assert call["method"] == "POST"
    assert path_of(client, call) == f"/audit-log/{ORGANIZATION}/export"
    assert call["json"] == {
        "name": "q3",
        "should_create_cef": True,
        "should_create_ndjson": False,
        "datetime_start": "2026-07-01T00:00:00Z",
        "datetime_end": "2026-09-30T00:00:00Z",
        "filters": [{"field": "user", "value": "x"}],
    }
    assert call["params"] == {}


def test_audit_log_export_leaves_out_empty_filters(client: SpectraAssureApiOperations, sent: Recorder) -> None:
    client.audit_log_export(name="q3", datetime_start="a", datetime_end="b", filters=[])

    assert "filters" not in only(sent)["json"]


def test_audit_log_export_refuses_filters_that_are_not_a_list(
    client: SpectraAssureApiOperations, sent: Recorder
) -> None:
    with pytest.raises(SpectraAssureInvalidAction, match="must be a list"):
        client.audit_log_export(name="q3", datetime_start="a", datetime_end="b", filters={"a": 1})  # type: ignore[arg-type]

    assert sent.calls == []


def test_audit_log_status_puts_the_job_in_the_path(client: SpectraAssureApiOperations, sent: Recorder) -> None:
    client.audit_log_status(job_id="job-7", ignored=1)

    call = only(sent)
    assert (call["method"], path_of(client, call), call["params"]) == (
        "GET",
        f"/audit-log/{ORGANIZATION}/export/job-7/status",
        {},
    )


# ------------------------------------------------------------------ community


def test_community_report_package_sends_its_six_query_parameters(
    client: SpectraAssureApiOperations, sent: Recorder
) -> None:
    client.community_report_package(
        repository="npm",
        package="pkg",
        namespace="ns",
        version="1.0",
        artifact="a",
        artifact_tag="t",
        match_pattern="p",
        match_expression="e",
        offset=10,
        limit=5,
        ignored=1,
    )

    call = only(sent)
    assert path_of(client, call) == "/community/report/package/pkg:npm/ns/pkg@1.0"
    assert call["params"] == {
        "artifact": "a",
        "artifact_tag": "t",
        "match_pattern": "p",
        "match_expression": "e",
        "offset": 10,
        "limit": 5,
    }


def test_community_report_package_without_namespace_or_version(
    client: SpectraAssureApiOperations, sent: Recorder
) -> None:
    client.community_report_package(repository="npm", package="pkg", namespace="")

    assert path_of(client, only(sent)) == "/community/report/package/pkg:npm/pkg"


def test_community_user_account_sends_no_query_parameters(client: SpectraAssureApiOperations, sent: Recorder) -> None:
    """It accepts **qp but ignores it; the specification declares no parameters."""
    client.community_user_account(limit=5)

    call = only(sent)
    assert (call["method"], path_of(client, call), call["params"]) == ("GET", "/community/user/account", {})


# ------------------------------------------------------------------ profiles


@pytest.mark.parametrize(
    ("group", "expected"),
    [(None, f"/profile/{ORGANIZATION}/export"), ("g2", f"/profile/{ORGANIZATION}/g2/export")],
)
def test_export_profile_for_an_organization_or_a_group(
    client: SpectraAssureApiOperations, sent: Recorder, group: str | None, expected: str
) -> None:
    client.export_profile(organization=ORGANIZATION, group=group)

    call = only(sent)
    assert (call["method"], path_of(client, call)) == ("GET", expected)


def test_export_profile_uses_the_organization_it_is_given(client: SpectraAssureApiOperations, sent: Recorder) -> None:
    client.export_profile(organization="other-org")

    assert path_of(client, only(sent)) == "/profile/other-org/export"


@pytest.mark.parametrize(
    ("group", "expected"),
    [(None, f"/profile/{ORGANIZATION}/import"), ("g2", f"/profile/{ORGANIZATION}/g2/import")],
)
def test_import_profile_uploads_the_file_as_a_form(
    client: SpectraAssureApiOperations, sent: Recorder, tmp_path: Path, group: str | None, expected: str
) -> None:
    profile = tmp_path / "profile.json"
    profile.write_bytes(b'{"policy": 1}')

    client.import_profile(organization=ORGANIZATION, group=group, file_path=str(profile), replace=False)

    call = only(sent)
    assert (call["method"], path_of(client, call)) == ("POST", expected)
    assert call["files"] == {"configuration_file": b'{"policy": 1}'}
    assert "multipart" not in call["headers"].get("Content-Type", "")  # requests sets it, with the boundary


def test_import_profile_refuses_a_missing_file(
    client: SpectraAssureApiOperations, sent: Recorder, tmp_path: Path
) -> None:
    with pytest.raises(SpectraAssureInvalidAction, match="to exist and be readable"):
        client.import_profile(organization=ORGANIZATION, file_path=str(tmp_path / "missing.json"))

    assert sent.calls == []


# ------------------------------------------------------------------ organization level


def test_listing_groups_gets_the_organization(client: SpectraAssureApiOperations, sent: Recorder) -> None:
    client.list_groups()

    call = only(sent)
    assert (call["method"], path_of(client, call)) == ("GET", f"/list/{ORGANIZATION}")


@pytest.mark.parametrize(
    ("group", "expected"),
    [(None, f"/usage/{ORGANIZATION}"), ("g2", f"/usage/{ORGANIZATION}/g2")],
)
def test_usage_for_the_organization_or_a_group(
    client: SpectraAssureApiOperations, sent: Recorder, group: str | None, expected: str
) -> None:
    client.usage(group=group)

    call = only(sent)
    assert (call["method"], path_of(client, call)) == ("GET", expected)


def test_scan_refuses_a_file_that_does_not_exist(
    client: SpectraAssureApiOperations, sent: Recorder, tmp_path: Path
) -> None:
    with pytest.raises(SpectraAssureInvalidAction, match="to exist and be readable"):
        client.scan(**VERSION, file_path=str(tmp_path / "missing.bin"))

    assert sent.calls == []


# ------------------------------------------------------------------ booleans in the profile form (I-39)


@pytest.fixture
def profile(tmp_path: Path) -> str:
    path = tmp_path / "profile.json"
    path.write_bytes(b"{}")
    return str(path)


@pytest.mark.parametrize(("replace", "expected"), [(True, "true"), (False, "false")])
def test_import_profile_writes_replace_in_lowercase(
    client: SpectraAssureApiOperations, sent: Recorder, profile: str, replace: bool, expected: str
) -> None:
    """false merges the profile into the configuration, true replaces it; the specification writes them in lowercase."""
    client.import_profile(organization=ORGANIZATION, file_path=profile, replace=replace)

    assert only(sent)["body_bytes"] == {"replace": expected}


def test_import_profile_replaces_by_default(client: SpectraAssureApiOperations, sent: Recorder, profile: str) -> None:
    client.import_profile(organization=ORGANIZATION, file_path=profile)

    assert only(sent)["body_bytes"] == {"replace": "true"}


def test_the_form_field_on_the_wire_reads_false(monkeypatch: pytest.MonkeyPatch, profile: str) -> None:
    """Build the real multipart body and look at the bytes the Portal receives."""
    prepared: list[requests.PreparedRequest] = []

    def capture(_self: Any, method: str, url: str, **kw: Any) -> requests.Response:
        request = requests.Request(method, url, data=kw.get("data"), files=kw.get("files"), headers=kw.get("headers"))
        prepared.append(request.prepare())
        response = requests.Response()
        response.status_code = 200
        return response

    monkeypatch.setattr(requests.Session, "request", capture)

    make_client().import_profile(organization=ORGANIZATION, file_path=profile, replace=False)

    body = prepared[0].body
    assert isinstance(body, bytes)
    assert b'name="replace"\r\n\r\nfalse\r\n' in body
    assert b"False" not in body


def test_query_string_booleans_are_left_as_they_are(client: SpectraAssureApiOperations, sent: Recorder) -> None:
    """Only form fields change; the Portal accepts download=True in a query string."""
    client.status(**VERSION, download=True)

    assert only(sent)["params"] == {"download": True}


# ------------------------------------------------------------------ report types are the Portal's to check (I-49)


def test_report_passes_an_unknown_type_through_for_the_portal_to_check(
    client: SpectraAssureApiOperations, sent: Recorder
) -> None:
    """Deliberate: a report type the Portal adds must work without a new SDK version."""
    client.report(**VERSION, report_type="Some-Future-Type")

    assert path_of(client, only(sent)).startswith(f"/report/{ORGANIZATION}/{GROUP}/some-future-type/")


def test_the_report_page_documents_that_the_type_is_not_checked() -> None:
    page = (Path(__file__).resolve().parents[1] / "doc" / "report.md").read_text(encoding="utf-8")

    assert "will raise an exception `SpectraAssureInvalidAction`" not in page
    assert "The SDK does not check `report_type`" in page
    assert "passed to the Portal as given, in lowercase" in page

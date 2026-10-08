"""File Stream operations.

These files carry no project, package or version, so the checks here are mostly
about the handle (`file_id`), the parameters the specification declares, and the
places where File Stream deliberately differs from the purl endpoints.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import requests

from spectra_assure_api_client import (
    SpectraAssureApiOperations,
    SpectraAssureDownloadCriteria,
    SpectraAssureInvalidAction,
    SpectraAssureWaitTimeoutExceeded,
)
from spectra_assure_api_client.spec import get_operation, operation_ids

from .support import BASE, Recorder, install, make_client, make_response

FILE_ID = "1f0c9d2e-0000-4a1b-9c3d-abcdef012345"


@pytest.fixture
def client() -> SpectraAssureApiOperations:
    return make_client()


# ------------------------------------------------------------------ routing


def test_every_filestream_operation_is_compiled() -> None:
    """The thirteen File Stream operations of the specification; reports are one operation, by type in the path."""
    filestream = {op for op in operation_ids() if "/filestream" in get_operation(op).path}
    assert filestream == {
        "scanFilestreamFile",
        "importFilestreamURL",
        "importFilestreamPURL",
        "listFilestreamFiles",
        "getFilestreamFileStatus",
        "getFilestreamFileChecks",
        "getFilestreamReport",
        "syncFilestreamFile",
        "approveFilestreamFile",
        "rejectFilestreamFile",
        "revokeFilestreamFile",
        "getRlSafeFilestreamArchive",
        "deleteFilestreamFile",
    }


def test_filestream_paths_use_the_file_id_handle(client: SpectraAssureApiOperations) -> None:
    assert client._filestream_url("filestream_status", FILE_ID) == (f"{BASE}/status/Org/Grp/filestream/{FILE_ID}")


def test_creating_calls_have_no_file_id_segment(client: SpectraAssureApiOperations) -> None:
    """scan and the imports post to the collection; the id comes back in the response."""
    for action in ("filestream_scan", "filestream_url_import", "filestream_purl_import"):
        assert client._filestream_url(action).endswith("/filestream")


def test_organization_and_group_fill_either_spelling(client: SpectraAssureApiOperations) -> None:
    """The File Stream templates say organization/group now; they said organization_name/group_name.

    The URL must come out right, and both spellings stay supplied, so a template
    with either one is filled.
    """
    operation = get_operation("getFilestreamFileStatus")
    assert {"organization", "group"} <= set(operation.path_params)
    assert client._filestream_url("filestream_status", FILE_ID).startswith(f"{BASE}/status/Org/Grp/")
    values = client._context_path_values()
    assert values["organization"] == values["organization_name"] == "Org"
    assert values["group"] == values["group_name"] == "Grp"


def test_file_id_is_percent_encoded(client: SpectraAssureApiOperations) -> None:
    url = client._filestream_url("filestream_status", "a b/c")
    assert url.endswith("/filestream/a%20b%2Fc")


# ------------------------------------------------------------------ reports


def test_report_type_selects_the_matching_operation(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    recorder = install(monkeypatch, "get", Recorder())

    client.filestream_report(file_id=FILE_ID, report_type="spdx")

    assert recorder.calls[0]["url"] == f"{BASE}/report/Org/Grp/spdx/filestream/{FILE_ID}"


def test_report_type_is_case_insensitive(monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations) -> None:
    recorder = install(monkeypatch, "get", Recorder())

    client.filestream_report(file_id=FILE_ID, report_type="RL-JSON")

    assert "/rl-json/" in recorder.calls[0]["url"]


def test_every_supported_report_type_routes(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    recorder = install(monkeypatch, "get", Recorder())

    for report_type in client.filestream_report_types():
        client.filestream_report(file_id=FILE_ID, report_type=report_type)

    assert len(recorder.calls) == 8
    assert len({call["url"] for call in recorder.calls}) == 8


def test_rl_diff_is_rejected_with_the_supported_types_listed(client: SpectraAssureApiOperations) -> None:
    """File Stream holds no versions, so there is nothing to diff."""
    with pytest.raises(SpectraAssureInvalidAction) as exc:
        client.filestream_report(file_id=FILE_ID, report_type="rl-diff")

    assert "rl-diff" in str(exc.value)
    assert "spdx" in str(exc.value)


# --------------------------------------------------------------- parameters


def test_scan_metadata_travels_as_query_parameters(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
) -> None:
    upload = tmp_path / "artifact.bin"
    upload.write_bytes(b"contents")
    recorder = install(monkeypatch, "post", Recorder())

    client.filestream_scan(
        file_path=str(upload),
        publisher="RL",
        version="1.2.3",
        nonsense="dropped",
    )

    assert recorder.calls[0]["params"] == {"publisher": "RL", "version": "1.2.3"}
    assert recorder.calls[0]["body_bytes"] == b"contents"


def test_version_is_metadata_not_a_path_segment(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
) -> None:
    upload = tmp_path / "a.bin"
    upload.write_bytes(b"x")
    recorder = install(monkeypatch, "post", Recorder())

    client.filestream_scan(file_path=str(upload), version="9.9")

    assert "9.9" not in recorder.calls[0]["url"]
    assert recorder.calls[0]["params"]["version"] == "9.9"


def test_scan_requires_a_readable_file(client: SpectraAssureApiOperations) -> None:
    with pytest.raises(SpectraAssureInvalidAction, match="exist and be readable"):
        client.filestream_scan(file_path="/nonexistent/nope.bin")


def test_list_accepts_the_declared_filters(monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations) -> None:
    recorder = install(monkeypatch, "get", Recorder())

    client.filestream_list(
        approval_status="approved",
        file_name="thing.exe",
        limit=25,
        offset=50,
        sort_by="created",
        user="someone",
        deleted_in_days=7,
        build="repro",  # a purl parameter; not declared here
    )

    params = recorder.calls[0]["params"]
    assert "build" not in params
    assert params["approval_status"] == "approved"
    assert params["limit"] == 25


# ------------------------------------------------------------------ imports


def test_url_import_maps_underscored_arguments_to_hyphenated_body_keys(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    recorder = install(monkeypatch, "post", Recorder())

    client.filestream_url_import(
        url="https://host/file.exe",
        auth_user="u",
        auth_pass="p",  # noqa: S106  fake credential
        max_size=1024,
    )

    call = recorder.calls[0]
    assert call["json"] == {"url": "https://host/file.exe", "auth-user": "u", "auth-pass": "p"}
    assert call["params"] == {"max_size": 1024}


def test_purl_import_sends_the_purl_in_the_body(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    recorder = install(monkeypatch, "post", Recorder())

    client.filestream_purl_import(
        purl="pkg:npm/left-pad@1.0.0",
        bearer_token="b",  # noqa: S106  fake credential
    )

    assert recorder.calls[0]["json"] == {"purl": "pkg:npm/left-pad@1.0.0", "bearer-token": "b"}


def test_bearer_token_cannot_be_combined_with_a_password(client: SpectraAssureApiOperations) -> None:
    with pytest.raises(SpectraAssureInvalidAction, match="bearer token"):
        client.filestream_url_import(
            url="https://host/f",
            auth_user="u",
            auth_pass="p",  # noqa: S106  fake credential
            bearer_token="b",  # noqa: S106  fake credential
        )


def test_url_import_requires_a_uri(client: SpectraAssureApiOperations) -> None:
    with pytest.raises(SpectraAssureInvalidAction, match="://"):
        client.filestream_url_import(url="host/file.exe")


# ----------------------------------------------------------------- approval


@pytest.mark.parametrize("method", ["filestream_approve", "filestream_reject", "filestream_revoke"])
def test_approval_reason_travels_in_the_body(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    method: str,
) -> None:
    recorder = install(monkeypatch, "put", Recorder())

    getattr(client, method)(file_id=FILE_ID, reason="because")

    assert recorder.calls[0]["json"] == {"reason": "because"}
    assert recorder.calls[0]["url"].endswith(f"/filestream/{FILE_ID}")


@pytest.mark.parametrize("method", ["filestream_approve", "filestream_reject", "filestream_revoke"])
def test_reason_is_mandatory(client: SpectraAssureApiOperations, method: str) -> None:
    """The specification marks it required here, unlike the purl equivalents."""
    with pytest.raises(TypeError):
        getattr(client, method)(file_id=FILE_ID)

    with pytest.raises(SpectraAssureInvalidAction, match="reason"):
        getattr(client, method)(file_id=FILE_ID, reason="")


# ---------------------------------------------------------------- downloads

STATUS_DONE = {
    "analysis": {
        "status": "Done",
        "report": {
            "info": {
                "file": {"hashes": [["sha256", "abc"], ["md5", "def"]]},
                "portal": {"download": "https://dl.example.com/file?x=1"},
            }
        },
    }
}


def test_download_skips_a_file_that_is_not_approved(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
) -> None:
    listing = {"files": [{"id": FILE_ID, "approval_status": "pending"}]}
    install(monkeypatch, "get", Recorder([STATUS_DONE, listing]))

    result = client.filestream_download(target_dir=str(tmp_path), file_id=FILE_ID)

    assert result is None


def test_download_requests_the_link_only_after_the_checks_pass(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
) -> None:
    """Each download link drawn costs group capacity, so it is requested last."""
    listing = {"files": [{"id": FILE_ID, "approval_status": "approved"}]}
    recorder = install(monkeypatch, "get", Recorder([STATUS_DONE, listing, STATUS_DONE]))

    downloaded: dict[str, Any] = {}

    def fake_download(self: Any, *, download_url: str, hashes: dict[str, str]) -> tuple[bool, str]:
        downloaded["url"] = download_url
        downloaded["hashes"] = hashes
        target = tmp_path / "artifact.bin"
        target.write_bytes(b"data")
        return True, str(target)

    monkeypatch.setattr(
        "spectra_assure_api_client.operations.filestream.UrlDownloader.download_file_from_url",
        fake_download,
    )

    result = client.filestream_download(target_dir=str(tmp_path), file_id=FILE_ID)

    # status, list, then status again with download=True
    assert [call["params"].get("download") for call in recorder.calls] == [None, None, True]
    assert downloaded["hashes"] == {"sha256": "abc", "md5": "def"}
    assert result is not None
    assert result[FILE_ID]["downloaded"] is True


@pytest.mark.parametrize(
    ("approval_status", "expect_download"),
    [
        ("Approved", True),
        # An automatic policy approval still counts as approved.
        ("ApprovedAutomatically", True),
        ("Undetermined", False),
        ("ApprovalRejected", False),
        ("ApprovalRevoked", False),
    ],
)
def test_download_honours_every_approval_state(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    approval_status: str,
    expect_download: bool,
) -> None:
    """The specification declares five approval states, two of which are approved."""
    listing = {"files": [{"id": FILE_ID, "approval_status": approval_status}]}
    install(monkeypatch, "get", Recorder([STATUS_DONE, listing, STATUS_DONE]))
    monkeypatch.setattr(
        "spectra_assure_api_client.operations.filestream.UrlDownloader.download_file_from_url",
        lambda self, *, download_url, hashes: (True, str(tmp_path / "f.bin")),
    )

    result = client.filestream_download(target_dir=str(tmp_path), file_id=FILE_ID)

    assert (result is not None) is expect_download


def test_download_rejects_a_missing_target_directory(client: SpectraAssureApiOperations) -> None:
    from spectra_assure_api_client import SpectraAssureInvalidPath

    with pytest.raises(SpectraAssureInvalidPath):
        client.filestream_download(target_dir="/no/such/place", file_id=FILE_ID)


def test_download_criteria_can_waive_the_approval_check(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
) -> None:
    recorder = install(monkeypatch, "get", Recorder([STATUS_DONE, STATUS_DONE]))
    monkeypatch.setattr(
        "spectra_assure_api_client.operations.filestream.UrlDownloader.download_file_from_url",
        lambda self, *, download_url, hashes: (True, str(tmp_path / "f.bin")),
    )

    criteria = SpectraAssureDownloadCriteria(must_be_approved=False)
    result = client.filestream_download(target_dir=str(tmp_path), file_id=FILE_ID, download_criteria=criteria)

    # no list call: approval was not consulted
    assert len(recorder.calls) == 2
    assert result is not None


def test_rl_safe_download_names_the_archive_after_the_file_id(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
) -> None:
    install(monkeypatch, "get", Recorder([{"download_link": "https://dl.example.com/a"}]))

    source = tmp_path / "downloaded.tmp"

    def fake_download(self: Any, *, download_url: str, hashes: dict[str, str]) -> tuple[bool, str]:
        source.write_bytes(b"archive")
        return True, str(source)

    monkeypatch.setattr(
        "spectra_assure_api_client.operations.filestream.UrlDownloader.download_file_from_url",
        fake_download,
    )

    ok, path = client.filestream_rl_safe_download(target_dir=str(tmp_path), file_id=FILE_ID)

    assert ok is True
    assert path.endswith(f"{FILE_ID}.rl-safe")


def test_rl_safe_download_can_keep_the_original_name(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
) -> None:
    install(monkeypatch, "get", Recorder([{"download_link": "https://dl.example.com/a"}]))
    source = tmp_path / "downloaded.tmp"
    monkeypatch.setattr(
        "spectra_assure_api_client.operations.filestream.UrlDownloader.download_file_from_url",
        lambda self, *, download_url, hashes: (source.write_bytes(b"a"), (True, str(source)))[1],
    )

    ok, path = client.filestream_rl_safe_download(target_dir=str(tmp_path), file_id=FILE_ID, rename_archive=False)

    assert ok is True
    assert path.endswith("downloaded.tmp")


# ---------------------------------------------------------- staying apart


def test_a_file_id_passed_to_a_purl_call_is_not_sent(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    """Both families take **qp, so crossing them must drop, not smuggle."""
    recorder = install(monkeypatch, "get", Recorder())

    client.status(project="pr", package="pk", version="1.0", file_id=FILE_ID)

    assert "file_id" not in recorder.calls[0]["params"]
    assert FILE_ID not in recorder.calls[0]["url"]


def test_purl_ladder_arguments_passed_to_a_filestream_call_are_not_sent(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    recorder = install(monkeypatch, "get", Recorder())

    client.filestream_status(file_id=FILE_ID, project="pr", package="pk", version="1.0")

    assert recorder.calls[0]["params"] == {}
    assert recorder.calls[0]["url"] == f"{BASE}/status/Org/Grp/filestream/{FILE_ID}"


def test_filestream_status_requires_a_file_id(client: SpectraAssureApiOperations) -> None:
    # file_id is deliberately omitted: the point is that it is mandatory
    with pytest.raises(TypeError):
        client.filestream_status()  # type: ignore[call-arg]


def test_scan_sends_the_headers_the_upload_requires(
    client: SpectraAssureApiOperations,
    tmp_path: Path,
) -> None:
    """Content-Disposition and Content-Length are both required by the specification.

    The first is set explicitly; the second is left to requests, which derives it
    from the file handle. If that ever regressed the body would go out chunked
    and the Portal would reject the upload, so it is pinned here.
    """
    payload = b"X" * 4096
    upload = tmp_path / "upload.exe"
    upload.write_bytes(payload)

    captured: dict[str, Any] = {}

    def prepare(self: Any, method: str, url: str, **kw: Any) -> requests.Response:
        # Prepare the request the way requests would, then read the headers that
        # would actually go on the wire.
        request = requests.Request(method, url, params=kw.get("params"), headers=kw.get("headers"), data=kw.get("data"))
        captured.update(requests.Session().prepare_request(request).headers)
        captured["__method__"] = method
        return make_response(201, payload={"id": FILE_ID})

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(requests.Session, "request", prepare)
        client.filestream_scan(file_path=str(upload))

    assert captured["__method__"] == "POST"

    assert captured["Content-Disposition"] == "attachment; filename=upload.exe"
    assert captured["Content-Length"] == str(len(payload))
    assert captured["Content-Type"] == "application/octet-stream"
    assert "Transfer-Encoding" not in captured


def test_rl_safe_download_waits_out_a_202(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
) -> None:
    """202 means the archive is still being prepared, not that the call failed."""
    recorder = Recorder(
        responses=[
            make_response(202),
            make_response(202),
            make_response(200, payload={"download_link": "https://dl.example.com/a"}),
        ]
    )
    install(monkeypatch, "get", recorder)

    slept: list[float] = []
    monkeypatch.setattr("spectra_assure_api_client.operations.filestream.time.sleep", slept.append)

    source = tmp_path / "downloaded.tmp"
    monkeypatch.setattr(
        "spectra_assure_api_client.operations.filestream.UrlDownloader.download_file_from_url",
        lambda self, *, download_url, hashes: (source.write_bytes(b"a"), (True, str(source)))[1],
    )

    ok, path = client.filestream_rl_safe_download(target_dir=str(tmp_path), file_id=FILE_ID)

    assert ok is True
    assert len(recorder.calls) == 3
    assert len(slept) == 2


def test_rl_safe_download_gives_up_after_the_budget(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
) -> None:
    install(monkeypatch, "get", Recorder(responses=[make_response(202) for _ in range(50)]))
    monkeypatch.setattr("spectra_assure_api_client.operations.filestream.time.sleep", lambda _: None)

    with pytest.raises(SpectraAssureWaitTimeoutExceeded, match="202"):
        client.filestream_rl_safe_download(target_dir=str(tmp_path), file_id=FILE_ID, max_wait_time_for_archive=10)


def test_rl_safe_download_can_fail_immediately_on_202(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
) -> None:
    """A zero budget restores the old fail-fast behaviour."""
    recorder = install(monkeypatch, "get", Recorder(responses=[make_response(202)]))

    with pytest.raises(SpectraAssureWaitTimeoutExceeded):
        client.filestream_rl_safe_download(target_dir=str(tmp_path), file_id=FILE_ID, max_wait_time_for_archive=0)

    assert len(recorder.calls) == 1


def test_rl_safe_download_raises_at_once_on_a_real_error(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
) -> None:
    """404 is not a 'not ready yet', so it must not be waited out."""
    recorder = install(monkeypatch, "get", Recorder(responses=[make_response(404)]))

    with pytest.raises(SpectraAssureInvalidAction, match="404"):
        client.filestream_rl_safe_download(target_dir=str(tmp_path), file_id=FILE_ID)

    assert len(recorder.calls) == 1

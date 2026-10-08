"""File Stream: waiting for an analysis, finding a file's approval, and the download's error paths (I-32).

The requests are answered in order by a Recorder; `time.sleep` is recorded
instead of served, so the waits cost nothing.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from spectra_assure_api_client import (
    SpectraAssureApiOperations,
    SpectraAssureDownloadCriteria,
    SpectraAssureInvalidAction,
    SpectraAssureInvalidPath,
    SpectraAssureNoDownloadUrlInResult,
    SpectraAssureUnexpectedNoDataFound,
)

from .support import ORGANIZATION, Recorder, install, make_client, make_response
from .test_filestream import FILE_ID, STATUS_DONE

GROUP_PATH = f"{ORGANIZATION}/Grp"


def status(analysis: str, *, link: bool = False) -> dict[str, Any]:
    info: dict[str, Any] = {"file": {"hashes": [["sha256", "abc"]]}}
    if link:
        info["portal"] = {"download": "https://dl.example.com/file?x=1"}
    return {"analysis": {"status": analysis, "report": {"info": info}}}


def listing(*ids: str, approval: str = "approved") -> dict[str, Any]:
    return {"files": [{"id": i, "approval_status": approval} for i in ids]}


@pytest.fixture
def client() -> SpectraAssureApiOperations:
    return make_client()


@pytest.fixture
def slept(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    waits: list[float] = []
    monkeypatch.setattr("time.sleep", waits.append)
    return waits


@pytest.fixture
def fetched(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> list[str]:
    urls: list[str] = []

    def fake_download(_self: Any, *, download_url: str, hashes: dict[str, str]) -> tuple[bool, str]:
        urls.append(download_url)
        target = tmp_path / "file.bin"
        target.write_bytes(b"data")
        return True, str(target)

    monkeypatch.setattr(
        "spectra_assure_api_client.operations.filestream.UrlDownloader.download_file_from_url", fake_download
    )
    return urls


def no_approval_check(**criteria: Any) -> SpectraAssureDownloadCriteria:
    return SpectraAssureDownloadCriteria(must_be_approved=False, **criteria)


# ------------------------------------------------------------------ waiting for the analysis


def test_waiting_polls_until_the_analysis_is_done(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    slept: list[float],
    fetched: list[str],
) -> None:
    recorder = install(
        monkeypatch, "get", Recorder([status("running"), status("running"), status("done"), status("done", link=True)])
    )
    criteria = no_approval_check(wait_for_scan_done=True, max_wait_time_for_scan_done=300)

    result = client.filestream_download(target_dir=str(tmp_path), file_id=FILE_ID, download_criteria=criteria)

    assert result is not None
    assert slept == [30, 30]  # a fifth of the maximum wait, kept within 10..30 s
    assert [c["params"].get("download") for c in recorder.calls] == [None, None, None, True]
    assert len(fetched) == 1


def test_waiting_gives_up_after_the_maximum_and_skips_the_file(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    slept: list[float],
    fetched: list[str],
) -> None:
    install(monkeypatch, "get", Recorder([status("running") for _ in range(20)]))
    criteria = no_approval_check(wait_for_scan_done=True, max_wait_time_for_scan_done=50)

    assert client.filestream_download(target_dir=str(tmp_path), file_id=FILE_ID, download_criteria=criteria) is None
    assert sum(slept) > 50
    assert fetched == []


def test_without_waiting_a_running_analysis_is_skipped_at_once(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    slept: list[float],
    fetched: list[str],
) -> None:
    recorder = install(monkeypatch, "get", Recorder([status("running")]))

    assert (
        client.filestream_download(target_dir=str(tmp_path), file_id=FILE_ID, download_criteria=no_approval_check())
        is None
    )
    assert slept == []
    assert len(recorder.calls) == 1  # no link requested


def test_a_status_error_while_waiting_is_raised(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, slept: list[float]
) -> None:
    install(monkeypatch, "get", Recorder(responses=[make_response(500, text="broken")]))

    with pytest.raises(SpectraAssureUnexpectedNoDataFound, match=rf"filestream_status\({FILE_ID}\) :: 500"):
        client.filestream_download(target_dir=str(tmp_path), file_id=FILE_ID)


# ------------------------------------------------------------------ finding the file's approval


def test_the_file_is_found_on_a_later_page_of_the_list(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, fetched: list[str]
) -> None:
    monkeypatch.setattr("spectra_assure_api_client.operations.filestream._LOOKUP_PAGE_SIZE", 2)
    recorder = install(
        monkeypatch, "get", Recorder([STATUS_DONE, listing("a", "b"), listing("c", FILE_ID), status("done", link=True)])
    )

    result = client.filestream_download(target_dir=str(tmp_path), file_id=FILE_ID)

    assert result is not None
    pages = [c["params"] for c in recorder.calls if c["url"].endswith("/filestream")]
    assert pages == [{"limit": 2, "offset": 0}, {"limit": 2, "offset": 2}]


def test_a_file_missing_from_a_short_last_page_is_skipped(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, fetched: list[str]
) -> None:
    monkeypatch.setattr("spectra_assure_api_client.operations.filestream._LOOKUP_PAGE_SIZE", 2)
    recorder = install(monkeypatch, "get", Recorder([STATUS_DONE, listing("a")]))

    assert client.filestream_download(target_dir=str(tmp_path), file_id=FILE_ID) is None
    assert len(recorder.calls) == 2  # a short page ends the search; no link requested
    assert fetched == []


def test_the_search_gives_up_after_the_page_limit(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr("spectra_assure_api_client.operations.filestream._LOOKUP_PAGE_SIZE", 1)
    monkeypatch.setattr("spectra_assure_api_client.operations.filestream._LOOKUP_MAX_PAGES", 3)
    install(monkeypatch, "get", Recorder([STATUS_DONE, listing("a"), listing("b"), listing("c")]))

    with caplog.at_level(logging.WARNING, logger="spectra_assure_api_client"):
        assert client.filestream_download(target_dir=str(tmp_path), file_id=FILE_ID) is None

    assert f"gave up looking for {FILE_ID} after 3 pages" in caplog.text
    assert fetched == []


def test_a_list_error_is_raised(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, fetched: list[str]
) -> None:
    install(
        monkeypatch, "get", Recorder(responses=[make_response(payload=STATUS_DONE), make_response(503, text="busy")])
    )

    with pytest.raises(SpectraAssureUnexpectedNoDataFound, match="filestream_list :: 503"):
        client.filestream_download(target_dir=str(tmp_path), file_id=FILE_ID)

    assert fetched == []


# ------------------------------------------------------------------ the download's error paths


def test_a_target_that_is_a_file_is_refused(client: SpectraAssureApiOperations, tmp_path: Path) -> None:
    a_file = tmp_path / "file.txt"
    a_file.write_text("x")

    with pytest.raises(SpectraAssureInvalidPath, match="not directory"):
        client.filestream_download(target_dir=str(a_file), file_id=FILE_ID)


def test_a_link_request_error_is_raised(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, fetched: list[str]
) -> None:
    install(
        monkeypatch, "get", Recorder(responses=[make_response(payload=status("done")), make_response(403, text="no")])
    )

    with pytest.raises(SpectraAssureUnexpectedNoDataFound, match=f"we get 403 from status lookup for {FILE_ID}"):
        client.filestream_download(target_dir=str(tmp_path), file_id=FILE_ID, download_criteria=no_approval_check())

    assert fetched == []


def test_a_link_answer_without_a_link_is_raised(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, fetched: list[str]
) -> None:
    install(monkeypatch, "get", Recorder([status("done"), status("done")]))

    with pytest.raises(SpectraAssureNoDownloadUrlInResult, match=f"no download URL from status for {FILE_ID}"):
        client.filestream_download(target_dir=str(tmp_path), file_id=FILE_ID, download_criteria=no_approval_check())

    assert fetched == []


def test_rl_safe_download_without_a_link_is_refused(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path
) -> None:
    install(monkeypatch, "get", Recorder([{"something_else": 1}]))

    with pytest.raises(SpectraAssureInvalidAction, match="missing download url in rl-safe download request"):
        client.filestream_rl_safe_download(target_dir=str(tmp_path), file_id=FILE_ID)


# ------------------------------------------------------------------ single calls


def test_checks_gets_the_file_checks(monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations) -> None:
    recorder = install(monkeypatch, "get", Recorder())

    client.filestream_checks(file_id=FILE_ID)

    assert recorder.calls[0]["url"].endswith(f"/checks/{GROUP_PATH}/filestream/{FILE_ID}")


def test_delete_deletes_the_file(monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations) -> None:
    recorder = install(monkeypatch, "delete", Recorder())

    client.filestream_delete(file_id=FILE_ID)

    assert (recorder.calls[0]["method"], recorder.calls[0]["url"].split("/api/public/v1")[1]) == (
        "DELETE",
        f"/delete/{GROUP_PATH}/filestream/{FILE_ID}",
    )


# ------------------------------------------------------------------ the version rl-safe calls (rl_safe.py)


def test_rl_safe_is_refused_below_version_level(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations
) -> None:
    recorder = install(monkeypatch, "get", Recorder())

    with pytest.raises(SpectraAssureInvalidAction, match="only supported for version"):
        client.rl_safe(project="pr", package="pk", version=None)  # type: ignore[arg-type]

    assert recorder.calls == []


def test_rl_safe_download_without_a_link_in_the_answer_is_refused(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path
) -> None:
    install(monkeypatch, "get", Recorder([{"no_link": True}]))

    with pytest.raises(SpectraAssureInvalidAction, match="missing download url"):
        client.rl_safe_download(target_dir=str(tmp_path), project="pr", package="pk", version="1.0")


@pytest.mark.parametrize("downloaded", [True, False])
def test_rl_safe_download_can_keep_the_downloaded_name(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, downloaded: bool
) -> None:
    """rename_archive=False, or a download that did not happen, leaves the file as the downloader returned it."""
    source = tmp_path / "as-downloaded.zip"
    source.write_bytes(b"archive")
    monkeypatch.setattr(
        "spectra_assure_api_client.operations.rl_safe.UrlDownloader.download_file_from_url",
        lambda *_a, **_k: (downloaded, str(source)),
    )
    install(monkeypatch, "get", Recorder([{"download_link": "https://dl.example.com/a"}]))

    ok, path = client.rl_safe_download(
        target_dir=str(tmp_path), project="pr", package="pk", version="1.0", rename_archive=not downloaded
    )

    assert (ok, Path(path)) == (downloaded, source)
    assert source.exists()


def test_rl_safe_download_will_not_put_the_archive_where_a_file_blocks_the_folder(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path
) -> None:
    """The archive goes to <target>/<project>/; if <project> is a file, it is reported, not overwritten."""
    blocker = tmp_path / "pr"
    blocker.write_text("not a folder")
    source = tmp_path / "as-downloaded.zip"
    source.write_bytes(b"archive")
    monkeypatch.setattr(
        "spectra_assure_api_client.operations.rl_safe.UrlDownloader.download_file_from_url",
        lambda *_a, **_k: (True, str(source)),
    )
    install(monkeypatch, "get", Recorder([{"download_link": "https://dl.example.com/a"}]))

    ok, message = client.rl_safe_download(target_dir=str(tmp_path), project="pr", package="pk", version="1.0")

    assert ok is False
    assert "exists but is not a directory" in message
    assert blocker.read_text() == "not a folder"


# ------------------------------------------------------------------ a failed analysis (I-44)


def test_a_failed_file_analysis_stops_the_wait_at_once(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    slept: list[float],
    fetched: list[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """ERROR is final; it used to be polled for the whole wait budget."""
    recorder = install(monkeypatch, "get", Recorder([status("ERROR") for _ in range(10)]))
    criteria = no_approval_check(wait_for_scan_done=True, max_wait_time_for_scan_done=3600)

    with caplog.at_level(logging.WARNING, logger="spectra_assure_api_client"):
        result = client.filestream_download(target_dir=str(tmp_path), file_id=FILE_ID, download_criteria=criteria)

    assert result is None
    assert slept == []
    assert len(recorder.calls) == 1  # one status call, no link requested
    assert f"the analysis of {FILE_ID} ended in an error; it will be skipped" in caplog.text
    assert fetched == []


def test_the_file_stream_in_progress_states_are_waited_on(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    slept: list[float],
    fetched: list[str],
) -> None:
    """SECURING and IMPORTING come before PROCESSING for File Stream files; none of them is final."""
    install(
        monkeypatch,
        "get",
        Recorder(
            [status("SECURING"), status("IMPORTING"), status("PROCESSING"), status("DONE"), status("DONE", link=True)]
        ),
    )
    criteria = no_approval_check(wait_for_scan_done=True, max_wait_time_for_scan_done=300)

    result = client.filestream_download(target_dir=str(tmp_path), file_id=FILE_ID, download_criteria=criteria)

    assert result is not None
    assert slept == [30, 30, 30]
    assert len(fetched) == 1


# ------------------------------------------------------------------ the download-link rate limit (I-46)


def test_a_rate_limited_file_link_request_waits_and_the_download_completes(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    slept: list[float],
    fetched: list[str],
) -> None:
    recorder = install(
        monkeypatch,
        "get",
        Recorder(
            responses=[
                make_response(payload=status("DONE")),
                make_response(429, headers={"Retry-After": "5"}, text="Too many requests"),
                make_response(payload=status("DONE", link=True)),
            ]
        ),
    )

    result = client.filestream_download(
        target_dir=str(tmp_path), file_id=FILE_ID, download_criteria=no_approval_check()
    )

    assert result is not None
    assert slept == [5]
    assert [c["params"].get("download") for c in recorder.calls] == [None, True, True]
    assert len(fetched) == 1


# ------------------------------------------------------------------ insufficient capacity (I-48)


def test_a_402_on_a_file_link_request_names_the_cause(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, fetched: list[str]
) -> None:
    install(
        monkeypatch, "get", Recorder(responses=[make_response(payload=status("done")), make_response(402, text="no")])
    )

    with pytest.raises(
        SpectraAssureUnexpectedNoDataFound,
        match=f"we get 402 from status lookup for {FILE_ID}: insufficient remaining capacity",
    ):
        client.filestream_download(target_dir=str(tmp_path), file_id=FILE_ID, download_criteria=no_approval_check())

    assert fetched == []

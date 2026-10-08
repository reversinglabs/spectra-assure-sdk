"""`download`: the error paths, waiting for an analysis, and the edges of version selection.

Builds on the fake Portal of `test_download.py`. Each variant below changes one
answer the Portal gives, so each test shows how `download` reacts to it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import requests

from spectra_assure_api_client import (
    SpectraAssureApiOperations,
    SpectraAssureDownloadCriteria,
    SpectraAssureInvalidPath,
    SpectraAssureNoDownloadUrlInResult,
    SpectraAssureUnexpectedNoDataFound,
    UrlDownloader,
)

from .support import make_client, make_response
from .test_download import INFO_PATH, STATUS_PATH, VERSIONS_PATH, FakePortal, Release

COORDINATES: dict[str, Any] = {"project": "pr", "package": "pk"}


@pytest.fixture
def client() -> SpectraAssureApiOperations:
    return make_client()


@pytest.fixture
def fetched(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> list[str]:
    """Stub the transfer and record which links were downloaded."""
    urls: list[str] = []

    def fake_download(_self: UrlDownloader, *, download_url: str, hashes: dict[str, str]) -> tuple[bool, str]:
        urls.append(download_url)
        return True, str(tmp_path / "pk.bin")

    monkeypatch.setattr(UrlDownloader, "download_file_from_url", fake_download)
    return urls


@pytest.fixture
def slept(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    waits: list[float] = []
    monkeypatch.setattr("time.sleep", waits.append)
    return waits


def serve(monkeypatch: pytest.MonkeyPatch, portal: FakePortal) -> FakePortal:
    monkeypatch.setattr(requests.Session, "request", portal.request)
    return portal


@dataclass
class FailingPortal(FakePortal):
    """A Portal that answers one kind of request with an error status."""

    fail: str = ""
    status: int = 500

    def request(self, method: str, url: str, **kw: Any) -> requests.Response:
        params = dict(kw.get("params") or {})
        kinds = {
            "link": bool(STATUS_PATH.search(url)) and bool(params.get("download")),
            "status": bool(STATUS_PATH.search(url)) and not params.get("download"),
            "info": bool(INFO_PATH.search(url)),
            "versions": bool(VERSIONS_PATH.search(url)) and not INFO_PATH.search(url),
        }
        if kinds.get(self.fail):
            return make_response(self.status, text="broken")
        return super().request(method, url, **kw)


@dataclass
class LinklessPortal(FakePortal):
    """Answers the link request with 200 but without a download link."""

    def request(self, method: str, url: str, **kw: Any) -> requests.Response:
        params = dict(kw.get("params") or {})
        if STATUS_PATH.search(url) and params.get("download"):
            return make_response(payload={"analysis": {"status": "done", "report": {"info": {}}}})
        return super().request(method, url, **kw)


@dataclass
class SlowPortal(FakePortal):
    """Reports the analysis as running for the first `running_for` status calls."""

    running_for: int = 0

    def request(self, method: str, url: str, **kw: Any) -> requests.Response:
        if STATUS_PATH.search(url) and not (kw.get("params") or {}).get("download"):
            done = len(self.discovery_calls()) >= self.running_for
            for release in self.releases.values():
                release.analysis = "done" if done else "running"
        return super().request(method, url, **kw)


# ------------------------------------------------------------------ target directory


def test_a_missing_target_directory_is_refused(client: SpectraAssureApiOperations, tmp_path: Path) -> None:
    with pytest.raises(SpectraAssureInvalidPath, match="does not exist"):
        client.download(target_dir=str(tmp_path / "absent"), **COORDINATES, version="1.0")


def test_a_target_that_is_a_file_is_refused(client: SpectraAssureApiOperations, tmp_path: Path) -> None:
    a_file = tmp_path / "file.txt"
    a_file.write_text("x")

    with pytest.raises(SpectraAssureInvalidPath, match="not directory"):
        client.download(target_dir=str(a_file), **COORDINATES, version="1.0")


# ------------------------------------------------------------------ the Portal answers badly


@pytest.mark.parametrize(
    ("fail", "version", "match"),
    [
        ("versions", None, r"list\(pr,pk,None\)"),
        ("info", "1.0", r"list\(pr,pk,1\.0\)"),
        ("status", "1.0", r"status\(pr,pk,1\.0\)"),
        ("link", "1.0", "from status lookup"),
    ],
)
def test_an_error_from_the_portal_is_raised_not_ignored(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[str],
    fail: str,
    version: str | None,
    match: str,
) -> None:
    serve(monkeypatch, FailingPortal(releases={"1.0": Release()}, fail=fail))

    with pytest.raises(SpectraAssureUnexpectedNoDataFound, match=match):
        client.download(target_dir=str(tmp_path), **COORDINATES, version=version)

    assert fetched == []


def test_a_link_answer_without_a_link_is_raised(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, fetched: list[str]
) -> None:
    serve(monkeypatch, LinklessPortal(releases={"1.0": Release()}))

    with pytest.raises(SpectraAssureNoDownloadUrlInResult, match="no download URL"):
        client.download(target_dir=str(tmp_path), **COORDINATES, version="1.0")

    assert fetched == []


# ------------------------------------------------------------------ analysis not finished


def test_a_version_still_being_analysed_is_skipped_when_not_waiting(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[str],
    slept: list[float],
) -> None:
    portal = serve(monkeypatch, FakePortal(releases={"1.0": Release(analysis="running")}))

    assert client.download(target_dir=str(tmp_path), **COORDINATES, version="1.0") is None
    assert fetched == []
    assert slept == []
    assert portal.link_calls() == []


def test_waiting_for_the_analysis_polls_until_it_is_done(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[str],
    slept: list[float],
) -> None:
    portal = serve(monkeypatch, SlowPortal(releases={"1.0": Release()}, running_for=2))
    criteria = SpectraAssureDownloadCriteria(wait_for_scan_done=True, max_wait_time_for_scan_done=300)

    result = client.download(target_dir=str(tmp_path), **COORDINATES, version="1.0", download_criteria=criteria)

    assert result is not None
    assert len(portal.discovery_calls()) == 3
    assert slept == [30, 30]  # a fifth of the maximum wait, kept within 10..30 s
    assert len(fetched) == 1


def test_waiting_gives_up_after_the_maximum_and_skips_the_version(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[str],
    slept: list[float],
) -> None:
    serve(monkeypatch, SlowPortal(releases={"1.0": Release()}, running_for=1_000))
    criteria = SpectraAssureDownloadCriteria(wait_for_scan_done=True, max_wait_time_for_scan_done=50)

    assert client.download(target_dir=str(tmp_path), **COORDINATES, version="1.0", download_criteria=criteria) is None
    assert sum(slept) > 50
    assert fetched == []


# ------------------------------------------------------------------ approval and selection


def test_without_the_approval_requirement_an_unapproved_version_is_downloaded(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, fetched: list[str]
) -> None:
    serve(monkeypatch, FakePortal(releases={"1.0": Release(approval="Undetermined")}))
    criteria = SpectraAssureDownloadCriteria(must_be_approved=False)

    result = client.download(target_dir=str(tmp_path), **COORDINATES, version="1.0", download_criteria=criteria)

    assert result is not None
    assert list(result) == ["1.0"]


def test_latest_approved_selects_nothing_when_no_candidate_is_approved(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """With the approval requirement off, unapproved versions are candidates, but the
    default strategy picks the latest *approved* one. With none approved it selects
    nothing, as when no version qualifies at all; it used to raise (I-38)."""
    portal = serve(
        monkeypatch,
        FakePortal(
            releases={
                "1.0": Release(approval="Undetermined", stamp=None),  # type: ignore[arg-type]
                "2.0": Release(approval="Undetermined", stamp=None),  # type: ignore[arg-type]
            }
        ),
    )
    criteria = SpectraAssureDownloadCriteria(must_be_approved=False)

    with caplog.at_level(logging.INFO, logger="spectra_assure_api_client"):
        result = client.download(target_dir=str(tmp_path), **COORDINATES, download_criteria=criteria)

    assert result is None
    assert fetched == []
    assert portal.link_calls() == []  # no download capacity spent
    assert "selects nothing: none of the candidates ['1.0', '2.0'] has been approved" in caplog.text


def test_latest_approved_still_ignores_unapproved_candidates_among_approved_ones(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, fetched: list[str]
) -> None:
    serve(
        monkeypatch,
        FakePortal(
            releases={
                "1.0": Release(approval="Approved", stamp="2026-01-01T00:00:00Z"),
                "2.0": Release(approval="Approved", stamp="2026-03-01T00:00:00Z"),
                "3.0": Release(approval="Undetermined", stamp=None),  # type: ignore[arg-type]
            }
        ),
    )
    criteria = SpectraAssureDownloadCriteria(must_be_approved=False)

    result = client.download(target_dir=str(tmp_path), **COORDINATES, download_criteria=criteria)

    assert result is not None
    assert list(result) == ["2.0"]


def test_a_single_unapproved_candidate_is_still_downloaded_without_the_approval_requirement(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, fetched: list[str]
) -> None:
    serve(monkeypatch, FakePortal(releases={"1.0": Release(approval="Undetermined", stamp=None)}))  # type: ignore[arg-type]
    criteria = SpectraAssureDownloadCriteria(must_be_approved=False)

    result = client.download(target_dir=str(tmp_path), **COORDINATES, download_criteria=criteria)

    assert result is not None
    assert list(result) == ["1.0"]


def test_qp_download_keeps_build_only_for_a_version() -> None:
    keep = SpectraAssureApiOperations._qp_download

    assert keep(what="version", build="repro", download=True, other=1) == {"build": "repro"}
    assert keep(what="package", build="repro") == {}


def test_all_approved_downloads_every_approved_version(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, fetched: list[str]
) -> None:
    serve(
        monkeypatch,
        FakePortal(
            releases={
                "1.0": Release(stamp="2026-01-01T00:00:00Z"),
                "2.0": Release(stamp="2026-02-01T00:00:00Z"),
                "3.0": Release(approval="ApprovalRejected"),
            }
        ),
    )
    criteria = SpectraAssureDownloadCriteria(current_strategy="AllApproved")

    result = client.download(target_dir=str(tmp_path), **COORDINATES, download_criteria=criteria)

    assert result is not None
    assert sorted(result) == ["1.0", "2.0"]  # the rejected one is skipped
    assert len(fetched) == 2


# ------------------------------------------------------------------ approval timestamps and criteria (I-27)


def approved(stamp: str) -> Release:
    return Release(approval="Approved", stamp=stamp)


@pytest.mark.parametrize(
    ("earlier", "later"),
    [
        ("2026-01-01T10:00:00Z", "2026-01-01T10:00:00.500Z"),  # as text, the first sorts after the second
        ("2026-01-01T10:00:00+01:00", "2026-01-01T09:30:00Z"),  # 09:00 UTC versus 09:30 UTC
        ("2026-01-01T09:00:00+0000", "2026-01-01T09:00:01+00:00"),  # two offset spellings from the spec
    ],
)
def test_latest_approved_compares_points_in_time_not_text(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[str],
    earlier: str,
    later: str,
) -> None:
    serve(monkeypatch, FakePortal(releases={"1.0": approved(later), "2.0": approved(earlier)}))

    result = client.download(target_dir=str(tmp_path), **COORDINATES)

    assert result is not None
    assert list(result) == ["1.0"]  # approved later, whatever the text says


def test_equal_timestamps_choose_the_version_listed_last(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, fetched: list[str]
) -> None:
    """The order the Portal lists versions in decides; written in two forms, it is still the same moment."""
    serve(
        monkeypatch,
        FakePortal(releases={"1.0": approved("2026-01-01T10:00:00Z"), "2.0": approved("2026-01-01T10:00:00+00:00")}),
    )

    result = client.download(target_dir=str(tmp_path), **COORDINATES)

    assert result is not None
    assert list(result) == ["2.0"]


def test_an_unreadable_timestamp_is_not_considered(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    serve(monkeypatch, FakePortal(releases={"1.0": approved("2026-01-01T10:00:00Z"), "2.0": approved("yesterday")}))

    with caplog.at_level(logging.WARNING, logger="spectra_assure_api_client"):
        result = client.download(target_dir=str(tmp_path), **COORDINATES)

    assert result is not None
    assert list(result) == ["1.0"]
    assert "approval timestamp 'yesterday' of version 2.0 cannot be read" in caplog.text


def test_download_keeps_no_criteria_on_the_client(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, fetched: list[str]
) -> None:
    """The criteria are passed down, so one call cannot change what another is using."""
    serve(monkeypatch, FakePortal(releases={"1.0": Release()}))

    client.download(
        target_dir=str(tmp_path), **COORDINATES, version="1.0", download_criteria=SpectraAssureDownloadCriteria()
    )

    assert not hasattr(client, "download_criteria")


def test_each_call_uses_its_own_criteria(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, fetched: list[str]
) -> None:
    """A second call with other criteria, made while the first is running, does not leak into the first."""
    serve(
        monkeypatch,
        FakePortal(
            releases={"1.0": Release(stamp="2026-01-01T00:00:00Z"), "2.0": Release(stamp="2026-02-01T00:00:00Z")}
        ),
    )
    seen: list[bool] = []
    real_init = UrlDownloader.__init__

    def spy(self: UrlDownloader, **kwargs: Any) -> None:
        seen.append(kwargs["with_overwrite_existing_files"])
        if len(seen) == 1:  # inside the first call, start a second one with other criteria
            client.download(
                target_dir=str(tmp_path),
                **COORDINATES,
                version="1.0",
                download_criteria=SpectraAssureDownloadCriteria(with_overwrite_existing_files=True),
            )
        real_init(self, **kwargs)

    monkeypatch.setattr(UrlDownloader, "__init__", spy)
    outer = SpectraAssureDownloadCriteria(current_strategy="AllApproved", with_overwrite_existing_files=False)

    result = client.download(target_dir=str(tmp_path), **COORDINATES, download_criteria=outer)

    assert result is not None
    assert sorted(result) == ["1.0", "2.0"]
    assert seen == [False, True]  # the first call's downloader kept the first call's setting


# ------------------------------------------------------------------ a failed analysis (I-44)


@dataclass
class SequencePortal(FakePortal):
    """Reports the analysis states in `states`, one per status call while choosing, then the last one."""

    states: tuple[str, ...] = ("DONE",)

    def request(self, method: str, url: str, **kw: Any) -> requests.Response:
        if STATUS_PATH.search(url) and not (kw.get("params") or {}).get("download"):
            state = self.states[min(len(self.discovery_calls()), len(self.states) - 1)]
            for release in self.releases.values():
                release.analysis = state
        return super().request(method, url, **kw)


def test_a_failed_analysis_stops_the_wait_at_once(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[str],
    slept: list[float],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """ERROR is final; it used to be polled for the whole wait budget."""
    portal = serve(monkeypatch, SequencePortal(releases={"1.0": Release()}, states=("ERROR",)))
    criteria = SpectraAssureDownloadCriteria(wait_for_scan_done=True, max_wait_time_for_scan_done=3600)

    with caplog.at_level(logging.WARNING, logger="spectra_assure_api_client"):
        result = client.download(target_dir=str(tmp_path), **COORDINATES, version="1.0", download_criteria=criteria)

    assert result is None
    assert slept == []
    assert len(portal.discovery_calls()) == 1
    assert portal.link_calls() == []
    assert "pr/pk@1.0: the analysis ended in an error; it will be skipped" in caplog.text


def test_an_analysis_that_fails_while_waited_on_stops_the_wait_then(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[str],
    slept: list[float],
) -> None:
    portal = serve(
        monkeypatch, SequencePortal(releases={"1.0": Release()}, states=("PROCESSING", "PROCESSING", "ERROR"))
    )
    criteria = SpectraAssureDownloadCriteria(wait_for_scan_done=True, max_wait_time_for_scan_done=3600)

    assert client.download(target_dir=str(tmp_path), **COORDINATES, version="1.0", download_criteria=criteria) is None
    assert len(slept) == 2
    assert len(portal.discovery_calls()) == 3
    assert fetched == []


def test_without_waiting_a_failed_analysis_is_reported_as_failed(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    serve(monkeypatch, FakePortal(releases={"1.0": Release(analysis="ERROR")}))

    with caplog.at_level(logging.INFO, logger="spectra_assure_api_client"):
        assert client.download(target_dir=str(tmp_path), **COORDINATES, version="1.0") is None

    assert "the analysis ended in an error" in caplog.text
    assert "has not yet finished processing" not in caplog.text


def test_an_analysis_still_processing_is_still_waited_on(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[str],
    slept: list[float],
) -> None:
    serve(monkeypatch, SequencePortal(releases={"1.0": Release()}, states=("PROCESSING", "PROCESSING", "DONE")))
    criteria = SpectraAssureDownloadCriteria(wait_for_scan_done=True, max_wait_time_for_scan_done=300)

    result = client.download(target_dir=str(tmp_path), **COORDINATES, version="1.0", download_criteria=criteria)

    assert result is not None
    assert slept == [30, 30]
    assert len(fetched) == 1


# ------------------------------------------------------------------ the download-link rate limit (I-46)


@dataclass
class RateLimitedPortal(FakePortal):
    """Answers the n-th download-link request once with 429 and a Retry-After, as the Portal does past 10 a minute."""

    limit_at: int = 2
    retry_after: str = "7"
    refused: int = 0

    def request(self, method: str, url: str, **kw: Any) -> requests.Response:
        params = dict(kw.get("params") or {})
        if STATUS_PATH.search(url) and params.get("download") and not self.refused:
            if len(self.link_calls()) + 1 == self.limit_at:
                self.refused += 1
                return make_response(429, headers={"Retry-After": self.retry_after}, text="Too many requests")
        return super().request(method, url, **kw)


def three_approved() -> dict[str, Release]:
    return {v: Release(stamp=f"2026-0{i}-01T00:00:00Z") for i, v in enumerate(("1.0", "2.0", "3.0"), start=1)}


def test_a_rate_limited_link_request_waits_and_the_download_completes(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[str],
    slept: list[float],
) -> None:
    """With the client's throttle handling off (the default), a 429 on a link request is still waited out."""
    portal = RateLimitedPortal(releases=three_approved())
    serve(monkeypatch, portal)
    criteria = SpectraAssureDownloadCriteria(current_strategy="AllApproved")

    result = client.download(target_dir=str(tmp_path), **COORDINATES, download_criteria=criteria)

    assert result is not None
    assert sorted(result) == ["1.0", "2.0", "3.0"]
    assert portal.refused == 1
    assert slept == [7]  # as long as Retry-After said
    assert len(fetched) == 3


def test_an_explicit_no_to_throttling_still_fails_fast_on_a_link_request(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[str],
    slept: list[float],
) -> None:
    serve(monkeypatch, RateLimitedPortal(releases=three_approved()))
    criteria = SpectraAssureDownloadCriteria(current_strategy="AllApproved")

    with pytest.raises(SpectraAssureUnexpectedNoDataFound, match="we get 429 from status lookup"):
        client.download(
            target_dir=str(tmp_path), **COORDINATES, download_criteria=criteria, auto_adapt_to_throttle=False
        )

    assert slept == []


def test_other_requests_still_follow_the_client_setting(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, slept: list[float]
) -> None:
    """Only link requests changed: a 429 while choosing versions is not retried when throttling is off."""
    serve(monkeypatch, FailingPortal(releases={"1.0": Release()}, fail="status", status=429))

    with pytest.raises(SpectraAssureUnexpectedNoDataFound, match="429"):
        client.download(target_dir=str(tmp_path), **COORDINATES, version="1.0")

    assert slept == []


@pytest.mark.parametrize(("per_call", "retries"), [(None, True), (True, True), (False, False)])
def test_the_link_request_rule(per_call: bool | None, retries: bool) -> None:
    assert SpectraAssureApiOperations._link_request_throttle(per_call) is retries  # noqa: SLF001


# ------------------------------------------------------------------ insufficient capacity (I-48)


def test_a_402_on_a_link_request_names_the_cause(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, fetched: list[str]
) -> None:
    """402 is "Insufficient remaining capacity" in the specification; it used to be reported by its number only."""
    serve(monkeypatch, FailingPortal(releases={"1.0": Release()}, fail="link", status=402))

    with pytest.raises(SpectraAssureUnexpectedNoDataFound) as caught:
        client.download(target_dir=str(tmp_path), **COORDINATES, version="1.0")

    message = str(caught.value)
    assert message.startswith("we get 402 from status lookup for pr/pk@1.0")  # unchanged start
    assert "insufficient remaining capacity" in message
    assert fetched == []


def test_other_link_request_failures_keep_their_message(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, tmp_path: Path, fetched: list[str]
) -> None:
    serve(monkeypatch, FailingPortal(releases={"1.0": Release()}, fail="link", status=403))

    with pytest.raises(SpectraAssureUnexpectedNoDataFound, match=r"^we get 403 from status lookup for pr/pk@1\.0$"):
        client.download(target_dir=str(tmp_path), **COORDINATES, version="1.0")

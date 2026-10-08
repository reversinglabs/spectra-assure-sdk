"""`download`: which versions qualify, and what the discovery requests carry.

A small fake Portal answers the `list` and `status` calls that `download` makes
while it decides what to fetch, and the file transfer itself is stubbed out, so
these tests exercise the selection logic without a network.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
import requests

from spectra_assure_api_client import SpectraAssureApiOperations, UrlDownloader

from .support import make_client, make_response

LINK = "https://files.example.com/pkg?response-content-disposition=attachment%3B%20filename%3D%22pk.bin%22"

STATUS_PATH = re.compile(r"/status/[^/]+/[^/]+/pkg:rl/(?P<project>[^/]+)/(?P<package>[^/@]+)@(?P<version>[^/]+)$")
INFO_PATH = re.compile(r"/list/[^/]+/[^/]+/pkg:rl/(?P<project>[^/]+)/(?P<package>[^/@]+)@(?P<version>[^/]+)$")
VERSIONS_PATH = re.compile(r"/list/[^/]+/[^/]+/pkg:rl/(?P<project>[^/]+)/(?P<package>[^/@]+)$")


@dataclass
class Release:
    """What the fake Portal knows about one version."""

    approval: str = "Approved"
    stamp: str = "2026-01-01T00:00:00Z"
    analysis: str = "done"
    # The main artifact and the reproducible build are different files, so they
    # have different hashes. Which one a status answer carries depends on `build`.
    main_hash: str = "main-hash"
    repro_hash: str = "repro-hash"


@dataclass
class FakePortal:
    releases: dict[str, Release]
    status_calls: list[dict[str, Any]] = field(default_factory=list)

    def request(self, method: str, url: str, **kw: Any) -> requests.Response:
        """Stand in for `Session.request`; installed as a bound method, so no session argument arrives."""
        assert method == "GET", f"download only reads: {method} {url}"
        params = dict(kw.get("params") or {})

        if match := STATUS_PATH.search(url):
            version = match["version"]
            self.status_calls.append({"version": version, "params": params})
            return make_response(payload=self._status(self.releases[version], params))

        if match := INFO_PATH.search(url):
            release = self.releases[match["version"]]
            return make_response(
                payload={
                    "approval_status": release.approval,
                    "approval_information": {"timestamp": release.stamp},
                    "is_released": True,
                }
            )

        if VERSIONS_PATH.search(url):
            return make_response(payload={"versions": [{"version": v} for v in self.releases]})

        raise AssertionError(f"unexpected request: {url}")

    @staticmethod
    def _status(release: Release, params: dict[str, Any]) -> dict[str, Any]:
        digest = release.repro_hash if params.get("build") == "repro" else release.main_hash
        info: dict[str, Any] = {"file": {"hashes": [["sha256", digest]]}}
        if params.get("download"):
            info["portal"] = {"download": LINK}
        return {
            "analysis": {
                "status": release.analysis,
                "report": {"info": {**info, "statistics": {"quality": {"status": "pass"}}}},
            }
        }

    def discovery_calls(self) -> list[dict[str, Any]]:
        """Status calls made while choosing what to download (no link requested)."""
        return [c for c in self.status_calls if not c["params"].get("download")]

    def link_calls(self) -> list[dict[str, Any]]:
        return [c for c in self.status_calls if c["params"].get("download")]


@pytest.fixture
def fetched(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> list[dict[str, Any]]:
    """Stub the transfer, recording the link and the hashes each file is verified against."""
    calls: list[dict[str, Any]] = []

    def fake_download(_self: UrlDownloader, *, download_url: str, hashes: dict[str, str]) -> tuple[bool, str]:
        calls.append({"url": download_url, "hashes": dict(hashes)})
        return True, str(tmp_path / "pk.bin")

    monkeypatch.setattr(UrlDownloader, "download_file_from_url", fake_download)
    return calls


def portal_with(monkeypatch: pytest.MonkeyPatch, releases: dict[str, Release]) -> FakePortal:
    portal = FakePortal(releases)
    monkeypatch.setattr(requests.Session, "request", portal.request)
    return portal


@pytest.fixture
def client() -> SpectraAssureApiOperations:
    return make_client()


# ------------------------------------------------------------------ I-10


def test_build_reaches_the_discovery_requests(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[dict[str, Any]],
) -> None:
    """`build=repro` names a different artifact, so the status checked must be that one's."""
    portal = portal_with(monkeypatch, {"1.0": Release()})

    client.download(target_dir=str(tmp_path), project="pr", package="pk", version="1.0", build="repro")

    assert [c["params"] for c in portal.discovery_calls()] == [{"build": "repro"}]
    assert [c["params"] for c in portal.link_calls()] == [{"build": "repro", "download": True}]


def test_the_downloaded_build_is_verified_against_its_own_hashes(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[dict[str, Any]],
) -> None:
    """Verifying the reproducible build against the main artifact's hash can never pass."""
    portal_with(monkeypatch, {"1.0": Release(main_hash="main-hash", repro_hash="repro-hash")})

    client.download(target_dir=str(tmp_path), project="pr", package="pk", version="1.0", build="repro")

    assert fetched[0]["hashes"] == {"sha256": "repro-hash"}


def test_build_reaches_discovery_when_downloading_a_whole_package(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[dict[str, Any]],
) -> None:
    portal = portal_with(monkeypatch, {"1.0": Release(), "2.0": Release(stamp="2026-02-01T00:00:00Z")})

    client.download(target_dir=str(tmp_path), project="pr", package="pk", build="repro")

    assert {c["version"] for c in portal.discovery_calls()} == {"1.0", "2.0"}
    assert all(c["params"] == {"build": "repro"} for c in portal.discovery_calls())


def test_without_build_the_main_artifact_is_used_throughout(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[dict[str, Any]],
) -> None:
    portal = portal_with(monkeypatch, {"1.0": Release()})

    client.download(target_dir=str(tmp_path), project="pr", package="pk", version="1.0")

    assert [c["params"] for c in portal.discovery_calls()] == [{}]
    assert fetched[0]["hashes"] == {"sha256": "main-hash"}


def test_a_download_flag_from_the_caller_never_reaches_discovery(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    fetched: list[dict[str, Any]],
) -> None:
    """`download=True` asks for a link, which costs download capacity; only the chosen version may."""
    portal = portal_with(monkeypatch, {"1.0": Release(), "2.0": Release(approval="ApprovalRejected")})

    client.download(target_dir=str(tmp_path), project="pr", package="pk", download=True)

    assert all("download" not in c["params"] for c in portal.discovery_calls())
    assert [c["version"] for c in portal.link_calls()] == ["1.0"]

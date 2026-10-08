"""`UrlDownloader`: timeouts, and what a failed download reports."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
import requests

from spectra_assure_api_client import SpectraAssureApiOperations, UrlDownloader

from .support import Recorder, install, make_client

URL = "https://files.example.com/a?response-content-disposition=attachment%3B%20filename%3D%22a.bin%22"


def test_read_timeout_is_honoured(tmp_path: Path) -> None:
    """The client passes `read_timeout`; only `timeout` used to be read."""
    downloader = UrlDownloader(target_dir=str(tmp_path), read_timeout=30)

    assert downloader.read_timeout == 30
    assert downloader.timeout == 30


def test_timeout_still_works_as_an_alias(tmp_path: Path) -> None:
    downloader = UrlDownloader(target_dir=str(tmp_path), timeout=45)

    assert downloader.read_timeout == 45


def test_read_timeout_wins_over_its_alias(tmp_path: Path) -> None:
    downloader = UrlDownloader(target_dir=str(tmp_path), timeout=45, read_timeout=30)

    assert downloader.read_timeout == 30


def test_defaults_are_unchanged(tmp_path: Path) -> None:
    downloader = UrlDownloader(target_dir=str(tmp_path))

    assert downloader.read_timeout == 3600
    assert downloader.connect_timeout == 10


def test_connect_timeout_is_honoured(tmp_path: Path) -> None:
    assert UrlDownloader(target_dir=str(tmp_path), connect_timeout=5).connect_timeout == 5


@pytest.mark.parametrize(
    ("read_timeout", "connect_timeout", "attribute", "expected"),
    [
        (5, None, "read_timeout", 10),
        (7200, None, "read_timeout", 3600),
        (None, 60, "connect_timeout", 10),
    ],
)
def test_out_of_range_timeouts_are_clamped_and_reported(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    read_timeout: int | None,
    connect_timeout: int | None,
    attribute: str,
    expected: int,
) -> None:
    with caplog.at_level(logging.WARNING):
        downloader = UrlDownloader(
            target_dir=str(tmp_path),
            read_timeout=read_timeout,
            connect_timeout=connect_timeout,
        )

    assert getattr(downloader, attribute) == expected
    assert any("outside" in record.getMessage() for record in caplog.records)


def test_in_range_timeouts_are_not_reported(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        UrlDownloader(target_dir=str(tmp_path), read_timeout=30, connect_timeout=5)

    assert not caplog.records


def test_client_timeouts_reach_its_downloads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The client's `read_timeout` must be what a download actually uses."""
    captured: dict[str, Any] = {}
    real_init = UrlDownloader.__init__

    def spy(self: UrlDownloader, **kwargs: Any) -> None:
        captured.update(kwargs)
        real_init(self, **kwargs)

    monkeypatch.setattr(UrlDownloader, "__init__", spy)
    # Stop before any network traffic: "not downloaded" is a normal return.
    monkeypatch.setattr(UrlDownloader, "download_file_from_url", lambda *_a, **_k: (False, "skipped"))
    install(monkeypatch, "get", Recorder(payloads=[{"download_link": URL}]))
    client: SpectraAssureApiOperations = make_client(read_timeout=90, connect_timeout=4)

    client.rl_safe_download(target_dir=str(tmp_path), project="pr", package="pk", version="1.0")

    assert captured["read_timeout"] == 90
    assert captured["connect_timeout"] == 4


def downloader_with(session: Any, target: Path) -> UrlDownloader:
    return UrlDownloader(target_dir=str(target), session=session, with_verify_after_download=False)


def leftovers(directory: Path) -> list[str]:
    """Anything left in the download directory, temporary files included."""
    return sorted(entry.name for entry in directory.iterdir())


@pytest.mark.parametrize(
    "error",
    [
        requests.ConnectionError("no route to host"),
        requests.exceptions.SSLError("certificate verify failed"),
        requests.Timeout("timed out"),
    ],
)
def test_a_failed_request_surfaces_the_real_error(tmp_path: Path, error: Exception) -> None:
    """There is no response when the request itself fails; that must not mask the error."""
    session = Mock()
    session.get.side_effect = error

    with pytest.raises(type(error)) as caught:
        downloader_with(session, tmp_path).download_file_from_url(download_url=URL, hashes={})

    assert caught.value is error
    assert leftovers(tmp_path) == []


def test_an_http_error_status_closes_the_response(tmp_path: Path) -> None:
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
    session = Mock()
    session.get.return_value = response

    with pytest.raises(requests.HTTPError):
        downloader_with(session, tmp_path).download_file_from_url(download_url=URL, hashes={})

    response.close.assert_called_once()
    assert leftovers(tmp_path) == []


def test_a_broken_stream_removes_the_partial_file_and_closes_the_response(tmp_path: Path) -> None:
    def broken_stream(*_args: Any, **_kwargs: Any) -> Any:
        yield b"partial"
        raise requests.ConnectionError("connection reset")

    response = Mock()
    response.headers = {}
    response.iter_content.side_effect = broken_stream
    session = Mock()
    session.get.return_value = response

    with pytest.raises(requests.ConnectionError, match="connection reset"):
        downloader_with(session, tmp_path).download_file_from_url(download_url=URL, hashes={})

    response.close.assert_called_once()
    assert leftovers(tmp_path) == []


def test_a_successful_download_is_unchanged(tmp_path: Path) -> None:
    response = Mock()
    response.headers = {"Content-Length": "5"}
    response.iter_content.return_value = [b"hello"]
    session = Mock()
    session.get.return_value = response

    downloaded, path = downloader_with(session, tmp_path).download_file_from_url(download_url=URL, hashes={})

    assert downloaded is True
    assert Path(path).read_bytes() == b"hello"
    assert leftovers(tmp_path) == ["a.bin"]

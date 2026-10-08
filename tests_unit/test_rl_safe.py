"""`rl_safe_download` for project/package/version archives.

The API answers 202 while the archive is still being prepared. This has to be
waited out here just as it is for File Stream files, and the finished archive
has to be moved into place in a way that also works where `Path.rename` will
not overwrite.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from spectra_assure_api_client import (
    SpectraAssureApiOperations,
    SpectraAssureInvalidAction,
    SpectraAssureWaitTimeoutExceeded,
)

from .support import Recorder, install, make_client, make_response

LINK = {"download_link": "https://dl.example.com/a"}


@pytest.fixture
def client() -> SpectraAssureApiOperations:
    return make_client()


@pytest.fixture
def slept(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Record the waits between polls instead of serving them."""
    recorded: list[float] = []
    monkeypatch.setattr("time.sleep", recorded.append)
    return recorded


@pytest.fixture
def transfer(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Stub the file transfer; it 'downloads' into a temporary file and returns its path."""
    source = tmp_path / "downloaded.tmp"

    def fake_download(_self: Any, *, download_url: str, hashes: dict[str, str]) -> tuple[bool, str]:
        source.write_bytes(b"archive")
        return True, str(source)

    monkeypatch.setattr(
        "spectra_assure_api_client.operations.rl_safe.UrlDownloader.download_file_from_url",
        fake_download,
    )
    return source


def test_a_202_is_waited_out(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    slept: list[float],
    transfer: Path,
) -> None:
    """202 means the archive is still being prepared, not that the call failed."""
    recorder = install(
        monkeypatch,
        "get",
        Recorder(responses=[make_response(202), make_response(202), make_response(200, payload=LINK)]),
    )

    ok, path = client.rl_safe_download(target_dir=str(tmp_path), project="pr", package="pk", version="1.0")

    assert ok is True
    assert len(recorder.calls) == 3
    assert slept == [5, 5]
    assert Path(path) == tmp_path / "pr" / "pk@1.0.rl-safe"
    assert Path(path).read_bytes() == b"archive"


def test_the_wait_gives_up_after_the_budget(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    slept: list[float],
) -> None:
    recorder = install(monkeypatch, "get", Recorder(responses=[make_response(202) for _ in range(50)]))

    with pytest.raises(SpectraAssureWaitTimeoutExceeded, match=r"pr/pk@1\.0.*202"):
        client.rl_safe_download(
            target_dir=str(tmp_path), max_wait_time_for_archive=10, project="pr", package="pk", version="1.0"
        )

    assert len(recorder.calls) == 3  # at 0 s, 5 s and 10 s
    assert slept == [5, 5]


def test_a_zero_budget_fails_on_the_first_202(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    slept: list[float],
) -> None:
    """Callers that relied on the old fail-fast behaviour can ask for it."""
    recorder = install(monkeypatch, "get", Recorder(responses=[make_response(202)]))

    with pytest.raises(SpectraAssureWaitTimeoutExceeded):
        client.rl_safe_download(
            target_dir=str(tmp_path), max_wait_time_for_archive=0, project="pr", package="pk", version="1.0"
        )

    assert len(recorder.calls) == 1
    assert slept == []


def test_a_real_error_is_raised_at_once(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    slept: list[float],
) -> None:
    """404 is not 'not ready yet', so it must not be waited out."""
    recorder = install(monkeypatch, "get", Recorder(responses=[make_response(404)]))

    with pytest.raises(SpectraAssureInvalidAction, match="404"):
        client.rl_safe_download(target_dir=str(tmp_path), project="pr", package="pk", version="1.0")

    assert len(recorder.calls) == 1
    assert slept == []


def test_query_parameters_are_sent_on_every_poll(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    slept: list[float],
    transfer: Path,
) -> None:
    recorder = install(
        monkeypatch,
        "get",
        Recorder(responses=[make_response(202), make_response(200, payload=LINK)]),
    )

    client.rl_safe_download(target_dir=str(tmp_path), build="repro", project="pr", package="pk", version="1.0")

    assert [call["params"] for call in recorder.calls] == [{"build": "repro"}, {"build": "repro"}]


def test_rl_safe_itself_still_returns_a_202_as_it_is(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    slept: list[float],
) -> None:
    """Only the download waits; callers of `rl_safe` decide for themselves."""
    recorder = install(monkeypatch, "get", Recorder(responses=[make_response(202)]))

    response = client.rl_safe(project="pr", package="pk", version="1.0")

    assert response.status_code == 202
    assert len(recorder.calls) == 1
    assert slept == []


def test_the_archive_replaces_an_existing_one_even_where_rename_would_refuse(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    transfer: Path,
) -> None:
    """`Path.rename` raises FileExistsError on Windows; a re-download must still work there."""

    def refuse(_self: Path, _target: object) -> Path:
        raise FileExistsError("target exists")

    monkeypatch.setattr(Path, "rename", refuse)
    install(monkeypatch, "get", Recorder([LINK]))
    existing = tmp_path / "pr" / "pk@1.0.rl-safe"
    existing.parent.mkdir()
    existing.write_bytes(b"stale")

    ok, path = client.rl_safe_download(target_dir=str(tmp_path), project="pr", package="pk", version="1.0")

    assert ok is True
    assert Path(path) == existing
    assert existing.read_bytes() == b"archive"


def test_the_timeout_carries_the_message_the_api_sent(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    tmp_path: Path,
    slept: list[float],
) -> None:
    """A 202 can mean 'not done yet' or 'no complete analysis'; the caller should be able to tell which."""
    message = "Cannot get report for version that does not have complete analysis"
    install(
        monkeypatch,
        "get",
        Recorder(responses=[make_response(202, payload={"message": message}) for _ in range(5)]),
    )

    with pytest.raises(SpectraAssureWaitTimeoutExceeded, match=message):
        client.rl_safe_download(
            target_dir=str(tmp_path), max_wait_time_for_archive=5, project="pr", package="pk", version="1.0"
        )

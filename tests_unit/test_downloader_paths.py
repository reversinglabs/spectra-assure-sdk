"""`UrlDownloader`: what happens to existing files, temporary files and bad downloads.

The session is a Mock, so no request leaves the process; files are real, in a
temporary directory.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from spectra_assure_api_client import (
    UrlDownloader,
    UrlDownloaderFileVerifyIssue,
    UrlDownloaderTargetDirectoryIssue,
    UrlDownloaderTargetFileIssue,
    UrlDownloaderTempFileIssue,
    UrlDownloaderUnknownHashKey,
)

URL = "https://files.example.com/a?response-content-disposition=attachment%3B%20filename%3D%22a.bin%22"
CONTENT = b"hello"
GOOD = {"sha256": hashlib.sha256(CONTENT).hexdigest()}
BAD = {"sha256": "0" * 64}


def session_serving(content: bytes = CONTENT, *, length: int | None = None) -> Mock:
    response = Mock()
    response.headers = {"Content-Length": str(len(content) if length is None else length)}
    response.iter_content.return_value = [content]
    session = Mock()
    session.get.return_value = response
    return session


def downloader(target: Path, session: Mock | None = None, **options: Any) -> UrlDownloader:
    return UrlDownloader(target_dir=str(target), session=session or session_serving(), **options)


def entries(directory: Path) -> list[str]:
    return sorted(p.name for p in directory.iterdir())


# ------------------------------------------------------------------ construction


def test_an_unsupported_hash_key_is_refused(tmp_path: Path) -> None:
    with pytest.raises(UrlDownloaderUnknownHashKey, match="must be one of"):
        UrlDownloader(target_dir=str(tmp_path), hash_key="md5")


def test_a_missing_target_directory_is_refused(tmp_path: Path) -> None:
    with pytest.raises(UrlDownloaderTargetDirectoryIssue, match="does not exist"):
        UrlDownloader(target_dir=str(tmp_path / "absent"))


def test_a_target_that_is_a_file_is_refused(tmp_path: Path) -> None:
    a_file = tmp_path / "f"
    a_file.write_text("x")

    with pytest.raises(UrlDownloaderTargetDirectoryIssue, match="not a directory"):
        UrlDownloader(target_dir=str(a_file))


@pytest.mark.parametrize(("given", "used"), [(1024, 65536), (10**6, 65536), (8192, 8192)])
def test_a_block_size_outside_4_to_64_kib_becomes_64_kib(tmp_path: Path, given: int, used: int) -> None:
    """Pins current behaviour: a too-small value is not raised to the minimum but set to the maximum."""
    assert UrlDownloader(target_dir=str(tmp_path), block_size=given).block_size == used


# ------------------------------------------------------------------ what the link and hashes must provide


def test_hashes_without_the_configured_key_are_refused(tmp_path: Path) -> None:
    with pytest.raises(UrlDownloaderUnknownHashKey, match="sha256 is not present"):
        downloader(tmp_path).download_file_from_url(download_url=URL, hashes={"sha1": "x"})


def test_a_link_without_a_file_name_is_refused(tmp_path: Path) -> None:
    with pytest.raises(UrlDownloaderTargetFileIssue, match="cannot be extracted"):
        downloader(tmp_path).download_file_from_url(download_url="https://files.example.com/a", hashes={})


def test_a_file_name_with_a_path_is_reduced_to_its_last_part(tmp_path: Path) -> None:
    """A name such as ../../x must not place the file outside the target directory."""
    url = "https://f.example.com/a?response-content-disposition=attachment%3B%20filename%3D%22..%2F..%2Fx.bin%22"

    _, path = downloader(tmp_path, with_verify_after_download=False).download_file_from_url(download_url=url, hashes={})

    assert Path(path) == tmp_path / "x.bin"
    assert entries(tmp_path) == ["x.bin"]


# ------------------------------------------------------------------ verification


def test_a_download_matching_its_hash_is_kept(tmp_path: Path) -> None:
    downloaded, path = downloader(tmp_path).download_file_from_url(download_url=URL, hashes=GOOD)

    assert downloaded is True
    assert Path(path).read_bytes() == CONTENT


def test_a_download_with_the_wrong_hash_is_refused_and_removed(tmp_path: Path) -> None:
    with pytest.raises(UrlDownloaderFileVerifyIssue, match="verify of"):
        downloader(tmp_path).download_file_from_url(download_url=URL, hashes=BAD)

    assert entries(tmp_path) == []


def test_sha1_is_supported(tmp_path: Path) -> None:
    hashes = {"sha1": hashlib.sha1(CONTENT).hexdigest()}  # noqa: S324  the Portal publishes sha1 too

    downloaded, _ = downloader(tmp_path, hash_key="sha1").download_file_from_url(download_url=URL, hashes=hashes)

    assert downloaded is True


def test_a_size_that_differs_from_content_length_is_refused_and_removed(tmp_path: Path) -> None:
    session = session_serving(CONTENT, length=len(CONTENT) + 1)

    with pytest.raises(UrlDownloaderFileVerifyIssue, match="does not match Content-Length"):
        downloader(tmp_path, session).download_file_from_url(download_url=URL, hashes=GOOD)

    assert entries(tmp_path) == []


# ------------------------------------------------------------------ an existing target file


@pytest.fixture
def existing(tmp_path: Path) -> Path:
    target = tmp_path / "a.bin"
    target.write_bytes(CONTENT)
    return target


def test_an_existing_file_that_verifies_is_not_downloaded_again(tmp_path: Path, existing: Path) -> None:
    session = session_serving()

    downloaded, path = downloader(tmp_path, session).download_file_from_url(download_url=URL, hashes=GOOD)

    assert (downloaded, Path(path)) == (False, existing)
    session.get.assert_not_called()


def test_an_existing_file_that_does_not_verify_is_reported(tmp_path: Path, existing: Path) -> None:
    with pytest.raises(UrlDownloaderFileVerifyIssue):
        downloader(tmp_path).download_file_from_url(download_url=URL, hashes=BAD)

    assert existing.read_bytes() == CONTENT  # left as it was


def test_an_existing_file_is_kept_unchecked_when_verification_is_off(tmp_path: Path, existing: Path) -> None:
    session = session_serving()

    downloaded, _ = downloader(tmp_path, session, with_verify_existing_files=False).download_file_from_url(
        download_url=URL, hashes=BAD
    )

    assert downloaded is False
    session.get.assert_not_called()


def test_an_existing_file_is_replaced_when_overwriting(tmp_path: Path, existing: Path) -> None:
    existing.write_bytes(b"stale")
    session = session_serving()

    downloaded, _ = downloader(tmp_path, session, with_overwrite_existing_files=True).download_file_from_url(
        download_url=URL, hashes=GOOD
    )

    assert downloaded is True
    assert existing.read_bytes() == CONTENT


def test_overwriting_works_where_rename_will_not_replace_a_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, existing: Path
) -> None:
    """Simulates Windows, where rename onto an existing file raises FileExistsError.

    Replacing an existing file must not depend on rename overwriting it.
    """
    real_rename = Path.rename

    def windows_rename(self: Path, target: Any) -> Path:
        if Path(target).exists():
            raise FileExistsError(target)
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", windows_rename)
    existing.write_bytes(b"stale")

    downloaded, _ = downloader(tmp_path, with_overwrite_existing_files=True).download_file_from_url(
        download_url=URL, hashes=GOOD
    )

    assert downloaded is True
    assert existing.read_bytes() == CONTENT
    assert entries(tmp_path) == ["a.bin"]  # no temporary file left behind


def test_replacing_the_file_uses_os_replace(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """os.replace is the portable call; the finished file must be moved with it."""
    moves: list[tuple[str, str]] = []
    real_replace = os.replace

    def recording_replace(source: Any, target: Any) -> None:
        moves.append((os.path.basename(source), os.path.basename(target)))
        real_replace(source, target)

    monkeypatch.setattr(os, "replace", recording_replace)

    downloader(tmp_path).download_file_from_url(download_url=URL, hashes=GOOD)

    assert len(moves) == 1
    assert moves[0][0].endswith(".tmp")
    assert moves[0][1] == "a.bin"


def test_a_failed_move_removes_the_temporary_file_and_is_reported(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def refuse(_source: Any, _target: Any) -> None:
        raise PermissionError("target is locked")

    monkeypatch.setattr(os, "replace", refuse)

    with pytest.raises(PermissionError, match="target is locked"):
        downloader(tmp_path).download_file_from_url(download_url=URL, hashes=GOOD)

    assert entries(tmp_path) == []


# ------------------------------------------------------------------ the temporary file


def leftover_from_an_interrupted_run(directory: Path) -> Path:
    """The temporary name the downloader used before: derived from the URL only."""
    stale = directory / f".{uuid.uuid5(uuid.NAMESPACE_URL, URL)}.tmp"
    stale.write_bytes(b"partial")
    return stale


def test_a_leftover_temporary_file_does_not_block_the_download(tmp_path: Path) -> None:
    """An interrupted run used to leave a file with the one name the next attempt wanted."""
    stale = leftover_from_an_interrupted_run(tmp_path)

    downloaded, path = downloader(tmp_path).download_file_from_url(download_url=URL, hashes=GOOD)

    assert downloaded is True
    assert Path(path).read_bytes() == CONTENT
    assert stale.read_bytes() == b"partial"  # not ours to delete: another process may own it
    assert entries(tmp_path) == sorted(["a.bin", stale.name])


def test_each_attempt_writes_its_own_temporary_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    used: list[str] = []
    real_replace = os.replace

    def recording_replace(source: Any, target: Any) -> None:
        used.append(os.path.basename(source))
        real_replace(source, target)

    monkeypatch.setattr(os, "replace", recording_replace)
    subject = downloader(tmp_path, with_overwrite_existing_files=True)

    subject.download_file_from_url(download_url=URL, hashes=GOOD)
    subject.download_file_from_url(download_url=URL, hashes=GOOD)

    assert len(used) == 2
    assert used[0] != used[1]
    prefix = f".{uuid.uuid5(uuid.NAMESPACE_URL, URL)}."
    assert all(name.startswith(prefix) and name.endswith(".tmp") for name in used)
    assert entries(tmp_path) == ["a.bin"]  # nothing left behind


def test_no_temporary_file_is_left_after_a_failed_download(tmp_path: Path) -> None:
    with pytest.raises(UrlDownloaderFileVerifyIssue):
        downloader(tmp_path).download_file_from_url(download_url=URL, hashes=BAD)

    assert entries(tmp_path) == []


def test_a_directory_where_no_temporary_file_can_be_created_is_reported(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def refuse(*_args: Any, **_kwargs: Any) -> tuple[int, str]:
        raise PermissionError("read-only directory")

    monkeypatch.setattr(tempfile, "mkstemp", refuse)

    with pytest.raises(UrlDownloaderTempFileIssue, match="cannot create a temporary file.*read-only directory"):
        downloader(tmp_path).download_file_from_url(download_url=URL, hashes=GOOD)

    assert entries(tmp_path) == []

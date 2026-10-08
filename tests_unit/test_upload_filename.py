"""The Content-Disposition header of an upload, per RFC 6266 (I-47).

The name used to go out as `attachment; filename=<name>` whatever it held: a
space or `;` cut it short for a parser, a `"` broke the syntax, and a name with
characters outside Latin-1 made the upload fail with UnicodeEncodeError.
"""

from __future__ import annotations

import email
import email.policy
import urllib.parse
from pathlib import Path

import pytest

from spectra_assure_api_client.communication.post import _content_disposition

from .support import Recorder, install, make_client

TOKEN_NAMES = ["7z1514-x64.msi", "upload.exe", "a_b-c.d~e+f.tar.gz"]
QUOTED_NAMES = ["my file (1).zip", 'say "hi";x.zip', "back\\slash.zip", "a,b;c=d.zip"]
NON_ASCII_NAMES = ["résumé.zip", "файл.zip", "数据.bin", "naïve 名前.zip"]


def parsed_filename(header: str) -> str:
    """The plain `filename` parameter, as a standard parser reads it."""
    message = email.message_from_string(f"Content-Disposition: {header}\n\n", policy=email.policy.default)
    return str(dict(message["Content-Disposition"].params)["filename"])


def extended_filename(header: str) -> str:
    """The `filename*` parameter decoded per RFC 8187 (UTF-8, percent-encoded)."""
    marker = "filename*=UTF-8''"
    assert marker in header
    return urllib.parse.unquote(header.split(marker, 1)[1].split(";", 1)[0], encoding="utf-8")


@pytest.mark.parametrize("name", TOKEN_NAMES)
def test_a_simple_name_is_sent_as_before(name: str) -> None:
    """The specification's own example form: attachment; filename=upload.exe."""
    assert _content_disposition(name) == f"attachment; filename={name}"


@pytest.mark.parametrize("name", QUOTED_NAMES)
def test_a_name_with_spaces_or_separators_is_quoted_and_read_back_whole(name: str) -> None:
    header = _content_disposition(name)

    assert 'filename="' in header
    assert "filename*" not in header
    assert parsed_filename(header) == name


@pytest.mark.parametrize("name", NON_ASCII_NAMES)
def test_a_non_ascii_name_carries_the_real_name_in_filename_star(name: str) -> None:
    header = _content_disposition(name)

    assert header.isascii()  # http.client can always send it
    assert extended_filename(header) == name
    fallback = parsed_filename(header)
    assert fallback.isascii()
    assert len(fallback) == len(name)  # one stand-in per character


@pytest.mark.parametrize("name", ["line\nbreak.zip", "carriage\rreturn.zip", "tab\there.zip", "nul\x00.zip"])
def test_control_characters_never_reach_the_header(name: str) -> None:
    header = _content_disposition(name)

    assert header.isascii()
    assert not any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in header)
    assert extended_filename(header) == name


@pytest.mark.parametrize("method", ["scan", "filestream_scan"])
@pytest.mark.parametrize("name", ["файл.zip", "my file (1).zip"])
def test_uploading_such_a_file_works(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, method: str, name: str) -> None:
    """A Cyrillic name used to fail with UnicodeEncodeError before anything was sent."""
    path = tmp_path / name
    path.write_bytes(b"data")
    recorder = install(monkeypatch, "post", Recorder())
    target = {"project": "pr", "package": "pk", "version": "1.0"} if method == "scan" else {}

    getattr(make_client(), method)(**target, file_path=str(path))

    header = recorder.calls[0]["headers"]["Content-Disposition"]
    assert header == _content_disposition(name)
    assert header.encode("latin-1")  # sendable

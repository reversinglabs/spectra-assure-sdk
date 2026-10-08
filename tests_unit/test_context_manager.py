"""`with SpectraAssureApiOperations(...) as client`: the runtime behaviour and the type it promises."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from spectra_assure_api_client import SpectraAssureApiOperations

from .support import GROUP, HOST, ORGANIZATION, TOKEN, Recorder, install

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def new_client() -> SpectraAssureApiOperations:
    return SpectraAssureApiOperations(host=HOST, organization=ORGANIZATION, group=GROUP, token=TOKEN)


def test_with_gives_back_the_same_client() -> None:
    client = new_client()

    with client as entered:
        assert entered is client


def test_operations_are_available_on_the_entered_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """This is also checked by mypy, which reads this file: `list` must be known on `entered`."""
    install(monkeypatch, "get", Recorder())

    with new_client() as entered:
        response = entered.list(project="pr")

    assert response.status_code == 200


def test_leaving_the_block_closes_the_session(monkeypatch: pytest.MonkeyPatch) -> None:
    client = new_client()
    closed: list[bool] = []
    monkeypatch.setattr(client.session, "close", lambda: closed.append(True))

    with client:
        assert closed == []

    assert closed == [True]


def test_an_error_inside_the_block_still_closes_the_session_and_is_not_swallowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = new_client()
    closed: list[bool] = []
    monkeypatch.setattr(client.session, "close", lambda: closed.append(True))

    with pytest.raises(RuntimeError, match="boom"), client:
        raise RuntimeError("boom")

    assert closed == [True]


SNIPPET = """\
from spectra_assure_api_client import SpectraAssureApiOperations

with SpectraAssureApiOperations(host="h", organization="o", group="g", token="t") as client:
    client.list(project="p")  # a real operation: the type checker must know it
    client.no_such_operation()  # type: ignore[attr-defined]  # and must still reject a made-up one
"""


def test_a_type_checker_knows_the_operations_on_the_entered_client(tmp_path: Path) -> None:
    """The entered client is typed as the client, not as the transport layer beneath it.

    The unused-ignore check of --strict is the control: were `client` typed as
    Any, the `type: ignore` would be reported as unused and this would fail.
    """
    pytest.importorskip("mypy")
    snippet = tmp_path / "entered_client.py"
    snippet.write_text(SNIPPET, encoding="utf-8")

    env: dict[str, Any] = {"MYPYPATH": str(REPOSITORY_ROOT), "PATH": "", "HOME": str(tmp_path)}
    result = subprocess.run(  # noqa: S603  fixed arguments, no shell
        [
            sys.executable,
            "-m",
            "mypy",
            "--strict",
            "--no-incremental",
            "--cache-dir",
            str(tmp_path / "cache"),
            str(snippet),
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Success" in result.stdout

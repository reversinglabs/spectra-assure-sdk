"""Runtime validation is done with explicit checks, never with `assert`.

`python -O` removes every `assert`, and a failed one raises AssertionError, which
is not an SDK exception. Each check below used to be an assert; each now raises an
SDK exception with a message that names the requirement that failed.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from spectra_assure_api_client import (
    SpectraAssureApiOperations,
    SpectraAssureInvalidAction,
    UrlDownloader,
    UrlDownloaderUnknownHashKey,
)

from .support import GROUP, HOST, ORGANIZATION, TOKEN, Recorder, install, make_client

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = REPOSITORY_ROOT / "spectra_assure_api_client"


# ------------------------------------------------------------ the guards themselves


def test_the_package_contains_no_assert_statements() -> None:
    found = [
        f"{path.relative_to(REPOSITORY_ROOT)}:{node.lineno}"
        for path in sorted(PACKAGE.rglob("*.py"))
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Assert)
    ]

    assert found == [], f"use an explicit `raise` instead of `assert` in: {found}"


def test_the_checks_still_fire_under_python_dash_o() -> None:
    """Under -O an assert is gone; an explicit check must still refuse the call."""
    snippet = (
        "import sys\n"
        "from spectra_assure_api_client import SpectraAssureApiOperations, SpectraAssureInvalidAction\n"
        "print('debug' if __debug__ else 'optimized')\n"
        "try:\n"
        "    SpectraAssureApiOperations(host='h', organization='o', group='g', token='t', api_version='')\n"
        "except SpectraAssureInvalidAction as error:\n"
        "    print('refused:', error)\n"
        "else:\n"
        "    print('accepted')\n"
    )

    result = subprocess.run(  # noqa: S603  fixed arguments, no shell
        [sys.executable, "-O", "-c", snippet],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(REPOSITORY_ROOT)},
        check=False,
    )

    assert result.stdout.splitlines() == ["optimized", "refused: Fatal: the api_version is not set"], result.stderr


# ------------------------------------------------------------ the checks, one by one


def build(*, api_version: str = "v1", api_domain: str = "secure.software", api_proto: str = "https") -> object:
    return SpectraAssureApiOperations(
        host=HOST,
        organization=ORGANIZATION,
        group=GROUP,
        token=TOKEN,
        api_version=api_version,
        api_domain=api_domain,
        api_proto=api_proto,
    )


def test_an_empty_api_version_is_refused() -> None:
    with pytest.raises(SpectraAssureInvalidAction, match="the api_version is not set"):
        build(api_version="")


def test_an_empty_api_domain_is_refused() -> None:
    with pytest.raises(SpectraAssureInvalidAction, match="the api_domain is not set"):
        build(api_domain="")


def test_an_empty_api_proto_is_refused() -> None:
    with pytest.raises(SpectraAssureInvalidAction, match="the api_proto is not set"):
        build(api_proto="")


@pytest.mark.parametrize(
    ("token", "message"),
    [(None, "token must not be None"), ("", "token must not be empty")],
)
def test_a_token_that_is_lost_after_construction_is_refused_before_sending(
    monkeypatch: pytest.MonkeyPatch, token: str | None, message: str
) -> None:
    recorder = install(monkeypatch, "get", Recorder())
    client = make_client()
    setattr(client, "token", token)  # noqa: B010  the attribute is typed str

    with pytest.raises(SpectraAssureInvalidAction, match=message):
        client.list(project="pr")

    assert recorder.calls == []


def test_make_logger_refuses_no_logger() -> None:
    with pytest.raises(SpectraAssureInvalidAction, match="my_logger must not be None"):
        SpectraAssureApiOperations.make_logger(my_logger=None)  # type: ignore[arg-type]


def test_a_community_report_without_a_package_is_refused_before_sending(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = install(monkeypatch, "get", Recorder())

    with pytest.raises(SpectraAssureInvalidAction, match=r"package must not be None.*community_report_version"):
        make_client().community_report_version(repository="npm", package=None)  # type: ignore[arg-type]

    assert recorder.calls == []


@pytest.mark.parametrize("action", ["url_import", "purl_import", "community_find_packages", "audit_log_export"])
def test_a_json_post_without_post_data_is_refused_before_sending(monkeypatch: pytest.MonkeyPatch, action: str) -> None:
    recorder = install(monkeypatch, "post", Recorder())

    with pytest.raises(SpectraAssureInvalidAction, match=f"post_data must not be None for '{action}'"):
        make_client()._do_it_post(
            action=action, url="https://example.com/x", auto_adapt_to_throttle=None, post_data=None
        )

    assert recorder.calls == []


@pytest.mark.parametrize("action", ["import_org_profile", "import_group_profile"])
def test_a_profile_import_without_post_data_is_refused_before_sending(
    monkeypatch: pytest.MonkeyPatch, action: str
) -> None:
    recorder = install(monkeypatch, "post", Recorder())

    with pytest.raises(SpectraAssureInvalidAction, match=rf"post_data must not be None for '{action}'.*replace"):
        make_client()._do_it_post(
            action=action,
            url="https://example.com/x",
            auto_adapt_to_throttle=None,
            file_path="profile.json",
            post_data=None,
        )

    assert recorder.calls == []


# ------------------------------------------------------------ download criteria
#
# The guard that insisted the criteria had been prepared is gone with I-27: the
# criteria are now a required argument of every helper that reads them, so a
# missing one is a TypeError and a type-checker error, not a runtime state.


# ------------------------------------------------------------ hash key


def test_an_unsupported_hash_key_is_refused_when_a_digest_is_needed(tmp_path: Path) -> None:
    downloader = UrlDownloader(target_dir=str(tmp_path))
    setattr(downloader, "hash_key", "md5")  # noqa: B010  bypasses the constructor's own check
    target = tmp_path / "file.bin"
    target.write_bytes(b"data")

    with pytest.raises(UrlDownloaderUnknownHashKey, match="it is 'md5'"):
        downloader._get_hex_digest(file_path=str(target))  # noqa: SLF001

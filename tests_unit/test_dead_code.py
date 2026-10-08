"""No dead code or dead data in the shipped package, and the fixes that removed some."""

from __future__ import annotations

import ast
import dataclasses
import re
import tempfile
from pathlib import Path
from typing import Any

import pytest

from spectra_assure_api_client import SpectraAssureApiOperations, SpectraAssureInvalidAction
from spectra_assure_api_client.spec.index import Operation

from .support import GROUP, HOST, ORGANIZATION, TOKEN, make_client

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "spectra_assure_api_client"


def test_every_field_of_an_operation_is_read_somewhere() -> None:
    """tags, statuses and _query_meta were loaded from the compiled spec and read by nothing."""
    read = {
        node.attr
        for path in PACKAGE.rglob("*.py")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Attribute)
    }

    assert [f.name for f in dataclasses.fields(Operation) if f.name not in read] == []


@pytest.mark.parametrize("token", ["missing", None])
def test_a_client_without_a_token_is_refused(token: Any) -> None:
    """The minimal-settings check refuses it; the separate None check after it could never fire and is gone."""
    settings: dict[str, Any] = {"host": HOST, "organization": ORGANIZATION, "group": GROUP}
    if token is None:
        settings["token"] = None  # given, but None; "missing" leaves it out altogether

    with pytest.raises(SpectraAssureInvalidAction, match="missing or empty: token;"):
        SpectraAssureApiOperations(**settings)


def test_the_supported_levels_are_joined_with_spaces() -> None:
    """The message read "only supported for packageand version"."""
    with pytest.raises(SpectraAssureInvalidAction, match=r"only supported for package and version$"):
        make_client().download(target_dir=tempfile.gettempdir(), project="p", package=None)  # type: ignore[arg-type]

    joins = [
        f"{path.relative_to(ROOT)}:{number}"
        for path in PACKAGE.rglob("*.py")
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if "'and '.join(" in line
    ]
    assert joins == []


# ------------------------------------------------------------------ the README's host table against the code


def readme_host_rows() -> dict[str, str]:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    # The table is found by its "Requests go to" column; the first header cell may be renamed.
    start = readme.index("| Requests go to |")
    table = readme[readme.rindex("\n", 0, start) + 1 :].split("\n\n", 1)[0]
    return dict(re.findall(r"^\| (.+?) \| `(https://[^`]+)` \|$", table, re.M))


#: README row -> (settings to build a client with, the values to put into the row's URL)
CASES: dict[str, tuple[dict[str, Any], dict[str, str]]] = {
    "`server` only": ({"server": "demo"}, {"server": "demo"}),
    "`host` only": ({"host": "portal.example.com"}, {"host": "portal.example.com"}),
    "`host` and `server`": (
        {"host": "portal.example.com", "server": "develop"},
        {"host": "portal.example.com", "server": "develop"},
    ),
    "`server` is `trial` or `playground`, with or without `host`": ({"server": "trial"}, {"server": "trial"}),
}


def test_the_readme_host_table_has_a_row_for_every_case() -> None:
    assert set(readme_host_rows()) == set(CASES)


@pytest.mark.parametrize("row", sorted(CASES))
def test_each_row_of_the_readme_host_table_is_what_the_client_builds(row: str) -> None:
    settings, values = CASES[row]
    expected = readme_host_rows()[row]
    for name, value in values.items():
        expected = expected.replace(f"<{name}>", value)

    client = SpectraAssureApiOperations(organization=ORGANIZATION, group=GROUP, token=TOKEN, **settings)

    assert client.base_url == expected


def test_trial_and_playground_win_over_a_host() -> None:
    client = SpectraAssureApiOperations(
        host="portal.example.com", server="playground", organization=ORGANIZATION, group=GROUP, token=TOKEN
    )

    assert client.base_url == "https://playground.secure.software/api/public/v1"

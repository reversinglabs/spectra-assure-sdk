"""The customer contract must not drift.

`contract_snapshot.json` was extracted from the released SDK. This test asserts
that the current package still presents the same public surface: the same
exported names, the same public members, the same parameters in the same order.

Changes that were made on purpose are listed in `ALLOWED_*` below. Anything
else failing here is a break for someone's existing code, so the fix is to
restore the surface rather than to re-record the snapshot.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest

from tools.extract_contract import extract

SNAPSHOT_PATH = Path(__file__).with_name("contract_snapshot.json")


# --------------------------------------------------------------- allowlist

# Retry on 429 became the default, so the per-call override had to grow a third
# state: None (inherit the client setting), True (force on), False (force off).
# Previously it was `bool = False`, and an explicit False could not switch off
# an instance-level True because the two were combined with `or`.
THROTTLE_PARAM = "auto_adapt_to_throttle"
ALLOWED_DEFAULT_CHANGES: dict[str, tuple[str, str]] = {
    THROTTLE_PARAM: ("False", "None"),
    # The timeouts default to None so that a value in the config file is not
    # overridden by a default. The effective defaults are unchanged (3600 s
    # read, 10 s connect) and are applied after the file and the arguments have
    # been merged.
    "timeout": ("3600", "None"),
    "read_timeout": ("3600", "None"),
    "connect_timeout": ("10", "None"),
}

# Parameters added since the snapshot. Each must have a default, so that code
# written against the old signature still calls successfully.
ALLOWED_ADDED_PARAMETERS: set[tuple[str, str]] = {
    # `delete` accepts a `build` query parameter per the specification, but
    # do_it_delete had nowhere to put it and silently dropped it.
    ("do_it_delete", "url_params"),
    # A connect timeout, separate from the read timeout. `timeout` covered both,
    # so an unroutable host took the full read timeout -- an hour -- to fail.
    ("__init__", "connect_timeout"),
    # `rl_safe_download` treated the API's 202 ("archive still being prepared")
    # as an error, unlike its File Stream counterpart. It now waits for the
    # archive, and the wait can be bounded or switched off with this argument.
    ("rl_safe_download", "max_wait_time_for_archive"),
}

# Config-file keys added since the release. `keywords` is checked for removals
# rather than exact equality: a new key cannot break an existing config file,
# but a missing one silently stops honouring a setting somebody relies on.
ALLOWED_ADDED_KEYWORDS: set[str] = {
    "connect_timeout",
}


@pytest.fixture(scope="module")
def snapshot() -> dict[str, Any]:
    with SNAPSHOT_PATH.open(encoding="utf-8") as fh:
        loaded: dict[str, Any] = json.load(fh)
    return loaded


@pytest.fixture(scope="module")
def current() -> dict[str, Any]:
    extracted: dict[str, Any] = extract()
    return extracted


def test_no_exported_name_removed(snapshot: dict[str, Any], current: dict[str, Any]) -> None:
    """A removed export breaks `from spectra_assure_api_client import X`; an added one breaks nothing."""
    missing = set(snapshot["__all__"]) - set(current["__all__"])
    assert not missing, f"exports removed: {sorted(missing)}"


def test_no_export_changed_kind(snapshot: dict[str, Any], current: dict[str, Any]) -> None:
    for name, expected in snapshot["exports"].items():
        assert current["exports"][name]["kind"] == expected["kind"], name


def _keeps_order(old: list[str], new: list[str]) -> bool:
    """Whether every entry of `old` is still in `new`, in the same order."""
    remaining = iter(new)
    return all(entry in remaining for entry in old)


def test_exception_ancestry_kept(snapshot: dict[str, Any], current: dict[str, Any]) -> None:
    """Customers catch these by base class, so no ancestor may be lost or reordered.

    An added ancestor is compatible: every `except` that caught the exception
    before still catches it. UrlDownloaderExceptions gaining
    SpectraAssureExceptions (I-20) is such an addition.
    """
    for name, expected in snapshot["exports"].items():
        if "exception_mro" not in expected:
            continue
        actual = current["exports"][name]["exception_mro"]
        assert _keeps_order(expected["exception_mro"], actual), f"{name}: {expected['exception_mro']} -> {actual}"


def _classes(snapshot: dict[str, Any]) -> list[str]:
    return [n for n, e in snapshot["exports"].items() if e["kind"] == "class"]


def test_no_public_member_removed(snapshot: dict[str, Any], current: dict[str, Any]) -> None:
    for class_name in _classes(snapshot):
        expected = set(snapshot["exports"][class_name]["members"])
        actual = set(current["exports"][class_name]["members"])
        missing = expected - actual
        assert not missing, f"{class_name} lost public members: {sorted(missing)}"


def test_public_attributes_unchanged(snapshot: dict[str, Any], current: dict[str, Any]) -> None:
    for class_name in _classes(snapshot):
        for member, expected in snapshot["exports"][class_name]["members"].items():
            if expected["kind"] != "attribute":
                continue

            actual = current["exports"][class_name]["members"][member]

            if member == "keywords":
                # Config-file keys: additions are allowed and declared above,
                # removals are not.
                before = set(ast.literal_eval(expected["value"]))
                after = set(ast.literal_eval(actual["value"]))

                missing = before - after
                assert not missing, f"{class_name}.keywords lost: {sorted(missing)}"

                undeclared = after - before - ALLOWED_ADDED_KEYWORDS
                assert not undeclared, f"{class_name}.keywords gained undeclared keys: {sorted(undeclared)}"
                continue

            assert actual["value"] == expected["value"], f"{class_name}.{member}"


def _by_name(parameters: list[dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    return {p["name"]: p for p in (parameters or [])}


@pytest.mark.parametrize("class_name", ["SpectraAssureApiOperations"])
def test_method_parameters_unchanged(snapshot: dict[str, Any], current: dict[str, Any], class_name: str) -> None:
    expected_members = snapshot["exports"][class_name]["members"]
    actual_members = current["exports"][class_name]["members"]

    for member, expected in expected_members.items():
        if expected["kind"] != "method":
            continue

        actual = actual_members[member]
        expected_params = _by_name(expected["parameters"])
        actual_params = _by_name(actual["parameters"])

        missing = set(expected_params) - set(actual_params)
        assert not missing, f"{class_name}.{member} lost parameters: {sorted(missing)}"

        for added in set(actual_params) - set(expected_params):
            assert (member, added) in ALLOWED_ADDED_PARAMETERS, (
                f"{class_name}.{member} grew an undeclared parameter: {added}"
            )
            assert "default" in actual_params[added], (
                f"{class_name}.{member}.{added} was added without a default, which breaks existing callers"
            )

        for name, want in expected_params.items():
            got = actual_params[name]

            assert got["kind"] == want["kind"], f"{class_name}.{member}.{name} changed kind"

            if "default" in want:
                assert "default" in got, f"{class_name}.{member}.{name} lost its default and is now mandatory"

            if want.get("default") == got.get("default"):
                continue

            allowed = ALLOWED_DEFAULT_CHANGES.get(name)
            assert allowed == (want.get("default"), got.get("default")), (
                f"{class_name}.{member}.{name} default changed {want.get('default')} -> {got.get('default')}"
            )


def test_positional_order_unchanged(snapshot: dict[str, Any], current: dict[str, Any]) -> None:
    """Keyword-only parameters are order-insensitive, positional ones are not."""
    for class_name in _classes(snapshot):
        expected_members = snapshot["exports"][class_name]["members"]
        actual_members = current["exports"][class_name]["members"]

        for member, expected in expected_members.items():
            if expected["kind"] != "method":
                continue

            def positional(params: list[dict[str, Any]] | None) -> list[str]:
                return [p["name"] for p in (params or []) if p["kind"] in ("POSITIONAL_ONLY", "POSITIONAL_OR_KEYWORD")]

            assert positional(actual_members[member]["parameters"]) == positional(expected["parameters"]), (
                f"{class_name}.{member} positional order changed"
            )


# ------------------------------------------------------------------ the same contract on every Python


def test_the_snapshot_records_no_member_that_python_defines(snapshot: dict[str, Any]) -> None:
    """Members inherited from Python's own classes differ between Python versions.

    BaseException.add_note does not exist on 3.10, has no readable signature on
    3.11 and 3.12, and reads (self, object, /) on 3.13 and (self, note, /) on
    3.14; recorded in the snapshot, it made this test pass only on the Python
    that made it. The SDK's surface is what the SDK defines.
    """
    python_defined = {name for name in dir(BaseException) if not name.startswith("_")}
    recorded = {
        (cls, member)
        for cls, entry in snapshot["exports"].items()
        for member in entry.get("members", {})
        if member in python_defined
    }

    assert recorded == set()


def test_inherited_python_members_are_skipped_and_the_sdks_own_kept() -> None:
    from spectra_assure_api_client import SpectraAssureInvalidAction, UrlDownloader
    from tools.extract_contract import _defined_by_python

    # args and with_traceback exist on every supported Python; add_note only from 3.11
    assert _defined_by_python(SpectraAssureInvalidAction, "args")
    assert _defined_by_python(SpectraAssureInvalidAction, "with_traceback")
    assert not _defined_by_python(SpectraAssureInvalidAction, "__init__")  # the SDK's own
    assert not _defined_by_python(UrlDownloader, "download_file_from_url")

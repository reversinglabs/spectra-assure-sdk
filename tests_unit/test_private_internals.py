"""SDK internals carry a leading underscore; their old public names are deprecated aliases (I-19).

The old names stay callable so that nobody breaks in a minor release, but each
one warns, forwards to the private method, and is used nowhere in the SDK.
"""

from __future__ import annotations

import ast
import inspect
import re
import warnings
from pathlib import Path
from typing import Any

import pytest
import requests

from spectra_assure_api_client import SpectraAssureApiOperations
from spectra_assure_api_client.spectra_assure_api_operations import DEPRECATED_INTERNAL_NAMES, DEPRECATED_RENAMED

from .support import GROUP, HOST, ORGANIZATION, TOKEN, Recorder, install, make_client

PACKAGE = Path(__file__).resolve().parents[1] / "spectra_assure_api_client"
CLIENT_MODULE = PACKAGE / "spectra_assure_api_operations.py"

#: Helpers that look internal but are used by callers, so they stay public.
KEPT_PUBLIC = {"make_logger", "get_additional_args"}


@pytest.mark.parametrize("old", DEPRECATED_INTERNAL_NAMES)
def test_each_internal_exists_under_its_private_name(old: str) -> None:
    assert hasattr(SpectraAssureApiOperations, f"_{old}")


@pytest.mark.parametrize("old", DEPRECATED_INTERNAL_NAMES)
def test_the_old_name_keeps_the_private_signature_and_kind(old: str) -> None:
    alias = inspect.getattr_static(SpectraAssureApiOperations, old)
    private = inspect.getattr_static(SpectraAssureApiOperations, f"_{old}")

    assert isinstance(alias, staticmethod) == isinstance(private, staticmethod)
    assert inspect.signature(getattr(SpectraAssureApiOperations, old)) == inspect.signature(
        getattr(SpectraAssureApiOperations, f"_{old}")
    )


def test_a_deprecated_method_warns_and_forwards(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = install(monkeypatch, "get", Recorder())
    client = make_client()

    with pytest.warns(DeprecationWarning, match=r"SpectraAssureApiOperations\.do_it_get is internal") as caught:
        response = client.do_it_get(url="https://example.com/x", auto_adapt_to_throttle=None)

    assert response.status_code == 200
    assert len(recorder.calls) == 1
    assert caught[0].filename == __file__  # points at the caller


@pytest.mark.parametrize("on", ["class", "instance"])
def test_a_deprecated_static_method_works_on_the_class_and_on_an_instance(on: str) -> None:
    owner: Any = SpectraAssureApiOperations if on == "class" else make_client()

    with pytest.warns(DeprecationWarning, match=r"\.get_path is internal") as caught:
        value = owner.get_path(path="a/b", data={"a": {"b": 1}})

    assert value == 1
    assert caught[0].filename == __file__


def test_the_private_names_do_not_warn(monkeypatch: pytest.MonkeyPatch) -> None:
    install(monkeypatch, "get", Recorder())
    client = make_client()

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        client._do_it_get(url="https://example.com/x", auto_adapt_to_throttle=None)  # noqa: SLF001
        assert SpectraAssureApiOperations._get_path(path="a", data={"a": 2}) == 2  # noqa: SLF001


def test_the_sdk_itself_never_uses_a_deprecated_name() -> None:
    """Every call inside the package goes to the private name; only the alias table names the old ones."""
    used = [
        f"{path.relative_to(PACKAGE.parent)}:{node.lineno} .{node.attr}"
        for path in sorted(PACKAGE.rglob("*.py"))
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Attribute)
        and (node.attr in DEPRECATED_INTERNAL_NAMES or node.attr in DEPRECATED_RENAMED)
    ]

    assert used == []


def test_the_typed_declarations_match_the_runtime_aliases() -> None:
    """The TYPE_CHECKING block must declare exactly the names the runtime aliases create."""
    tree = ast.parse(CLIENT_MODULE.read_text(encoding="utf-8"))
    client = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "SpectraAssureApiOperations")
    declared = {
        target.id
        for block in client.body
        if isinstance(block, ast.If) and ast.unparse(block.test) == "TYPE_CHECKING"
        for statement in block.body
        if isinstance(statement, ast.Assign)
        for target in statement.targets
        if isinstance(target, ast.Name)
    }

    assert declared == set(DEPRECATED_INTERNAL_NAMES) | set(DEPRECATED_RENAMED)


def test_the_helpers_callers_use_stay_public_and_do_not_warn() -> None:
    client = SpectraAssureApiOperations(
        host=HOST, organization=ORGANIZATION, group=GROUP, token=TOKEN, additional_args={"x": 1}
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert client.get_additional_args() == {"x": 1}

    assert not KEPT_PUBLIC & set(DEPRECATED_INTERNAL_NAMES)
    assert all(not name.startswith("_") for name in KEPT_PUBLIC)


# ------------------------------------------------------------------ renamed public methods (I-25)


@pytest.mark.parametrize(("old", "new"), list(DEPRECATED_RENAMED.items()))
def test_a_renamed_method_keeps_the_new_signature(old: str, new: str) -> None:
    assert inspect.signature(getattr(SpectraAssureApiOperations, old)) == inspect.signature(
        getattr(SpectraAssureApiOperations, new)
    )


def test_list_groups_under_its_old_name_warns_and_forwards(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = install(monkeypatch, "get", Recorder())
    client = make_client()

    with pytest.warns(DeprecationWarning, match=r"listGroups is deprecated.*use list_groups instead") as caught:
        response = client.listGroups()

    assert response.status_code == 200
    assert caught[0].filename == __file__
    assert recorder.calls[0]["url"] == f"{client.base_url}/list/{client.organization}"


def test_list_groups_under_its_new_name_does_not_warn(monkeypatch: pytest.MonkeyPatch) -> None:
    install(monkeypatch, "get", Recorder())

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        make_client().list_groups()


def test_there_is_one_implementation_of_list_groups() -> None:
    """listGroups is an alias, not a second copy of the body."""
    source = (PACKAGE / "operations" / "list_groups.py").read_text(encoding="utf-8")

    assert "def listGroups" not in source


# ------------------------------------------------------------------ return annotations (I-25)

#: Operations that deliberately do not return the HTTP response.
NOT_A_RESPONSE = {"download", "filestream_download", "rl_safe_download", "filestream_rl_safe_download"}
NOT_OPERATIONS = {"close", "make_logger", "get_additional_args", "filestream_report_types"}


def test_every_operation_is_annotated_with_what_it_returns() -> None:
    """Calls that return the HTTP response say so; `Any` hid that for six of them."""
    hidden = set(DEPRECATED_INTERNAL_NAMES) | set(DEPRECATED_RENAMED) | NOT_OPERATIONS
    wrong = {}
    for name, member in inspect.getmembers(SpectraAssureApiOperations, inspect.isroutine):
        if name.startswith("_") or name in hidden:
            continue
        annotation = inspect.signature(member, eval_str=True).return_annotation  # resolves postponed annotations
        if name in NOT_A_RESPONSE:
            if annotation in (Any, requests.Response, inspect.Signature.empty):
                wrong[name] = annotation
        elif annotation is not requests.Response:
            wrong[name] = annotation

    assert wrong == {}


# ------------------------------------------------------------------ no dead private code (I-40)


def test_every_private_function_is_used_somewhere_in_the_package() -> None:
    """A private function nothing refers to is dead code; it should be deleted, not kept.

    References through the deprecated aliases count: the aliases forward to the
    private names, so those functions are in use until the aliases go.
    """
    sources = {path: path.read_text(encoding="utf-8") for path in sorted(PACKAGE.rglob("*.py"))}
    everything = "\n".join(sources.values())
    unused = [
        f"{path.relative_to(PACKAGE.parent)}:{node.lineno} {node.name}"
        for path, source in sources.items()
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef)
        and node.name.startswith("_")
        and not node.name.startswith("__")
        and len(re.findall(rf"\b{re.escape(node.name)}\b", everything)) == 1  # only its own definition
    ]

    assert unused == []

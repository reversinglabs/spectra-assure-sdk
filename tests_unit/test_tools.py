"""The tools/ scripts: what they produce matches what is committed, and they refuse what they cannot read."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


def load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"tools_{name}", TOOLS / f"{name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------------------------ compile_spec.py


def a_spec(body_schema: dict[str, Any], *, tags: list[str] | None = None) -> dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "paths": {
            "/thing": {
                "post": {
                    "operationId": "postThing",
                    "tags": tags or ["Things"],
                    "requestBody": {"content": {"application/json": {"schema": body_schema}}},
                    "responses": {"201": {"description": "created"}},
                }
            }
        },
    }


@pytest.mark.parametrize("keyword", ["allOf", "oneOf", "anyOf", "not"])
def test_a_composed_body_schema_is_refused_instead_of_compiling_to_nothing(keyword: str) -> None:
    """It used to compile with no body properties, so every field would have been filtered away."""
    collect = load("compile_spec").collect
    schema = {keyword: [{"type": "object", "properties": {"name": {"type": "string"}}}]}

    with pytest.raises(ValueError, match=rf"test\.yaml postThing \(application/json\): .*uses {keyword}"):
        collect(a_spec(schema), "test.yaml")


def test_an_inline_body_schema_still_compiles() -> None:
    operations, _ = load("compile_spec").collect(
        a_spec({"type": "object", "required": ["name"], "properties": {"name": {}, "size": {}}}), "test.yaml"
    )

    assert operations["postThing"]["body_properties"] == ["name", "size"]
    assert operations["postThing"]["body_required_properties"] == ["name"]


def test_an_excluded_operation_may_use_a_composed_schema() -> None:
    """The SCIM operations use allOf; they are excluded before their bodies are read."""
    module = load("compile_spec")
    tag = sorted(module.EXCLUDED_TAGS)[0]

    operations, skipped = module.collect(a_spec({"allOf": [{}]}, tags=[tag]), "test.yaml")

    assert operations == {}
    assert skipped == ["postThing"]


def test_the_shipped_compiled_spec_is_what_the_yaml_compiles_to() -> None:
    yaml = pytest.importorskip("yaml")
    module = load("compile_spec")
    sources = [
        (path.name, yaml.safe_load(path.read_text(encoding="utf-8")))
        for path in sorted((ROOT / "etc").glob("spectra-assure-*.yaml"))
    ]

    compiled = module.compile_specs(sources)
    shipped = json.loads(
        (ROOT / "spectra_assure_api_client" / "spec" / "compiled_spec.json").read_text(encoding="utf-8")
    )

    assert json.loads(json.dumps(compiled, sort_keys=True)) == shipped


def test_the_file_stream_report_types_are_the_ones_the_specification_lists() -> None:
    """filestream_report checks the type against FILESTREAM_REPORT_OPERATIONS; it must match the API."""
    yaml = pytest.importorskip("yaml")
    from spectra_assure_api_client.spec.routes import FILESTREAM_REPORT_OPERATIONS

    spec = yaml.safe_load((ROOT / "etc" / "spectra-assure-portal-public-api.yaml").read_text(encoding="utf-8"))
    # Parameters may sit on the path item as well as on the operation.
    parameters = next(
        item.get("parameters", []) + op.get("parameters", [])
        for item in spec["paths"].values()
        for op in item.values()
        if isinstance(op, dict) and op.get("operationId") == "getFilestreamReport"
    )
    listed = next(p["schema"]["enum"] for p in parameters if p.get("in") == "path" and p.get("name") == "report_type")

    assert sorted(FILESTREAM_REPORT_OPERATIONS) == sorted(listed)
    assert set(FILESTREAM_REPORT_OPERATIONS.values()) == {"getFilestreamReport"}

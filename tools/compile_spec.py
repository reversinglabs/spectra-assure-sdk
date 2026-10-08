"""Build step: distil the OpenAPI YAML into a small JSON operation table.

The full spec is ~290 KB of YAML and costs ~240 ms to parse with PyYAML on
every process start. Almost all of that is prose: descriptions, examples and
response schemas the client never consults at runtime. This script keeps only
what routing and parameter validation need, and emits JSON so the shipped
package needs no YAML parser at all -- `requests` stays the single runtime
dependency.

The Portal API is published as more than one document -- the purl-based
endpoints and the File Stream endpoints are separate YAML files that share a
server, an auth scheme and an operation-id namespace. They are compiled into one
table; operation ids are asserted unique across the inputs.

Usage:  python tools/compile_spec.py <out.json> <spec.yaml> [<spec.yaml> ...]
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

import yaml  # build-time only; never imported by the shipped package

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")

# Operations the SDK does not expose. Kept out of the compiled table so the
# runtime surface cannot drift into exposing them by accident.
# The SCIM user-management operations are not part of the SDK. The specification
# tags some of them "SCIM" and others "SCIM (System for Cross-domain Identity
# Management)", so both spellings are excluded.
EXCLUDED_TAGS = ("SCIM", "SCIM (System for Cross-domain Identity Management)")


def _resolve(node: Any, root: dict[str, Any], seen: frozenset[str] = frozenset()) -> Any:
    """Resolve $ref pointers into plain data. Local refs only, cycle-safe."""
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str):
            if not ref.startswith("#/"):
                raise ValueError(f"non-local $ref not supported: {ref}")
            if ref in seen:
                return {}
            target: Any = root
            for part in ref[2:].split("/"):
                target = target[part]
            return _resolve(target, root, seen | {ref})
        return {k: _resolve(v, root, seen) for k, v in node.items() if k != "$ref"}
    if isinstance(node, list):
        return [_resolve(item, root, seen) for item in node]
    return node


def _param(raw: dict[str, Any]) -> dict[str, Any]:
    schema = raw.get("schema") or {}
    out: dict[str, Any] = {
        "name": raw["name"],
        "in": raw["in"],
        "required": bool(raw.get("required", raw["in"] == "path")),
    }
    if schema.get("type"):
        out["type"] = schema["type"]
    if schema.get("enum"):
        out["enum"] = list(schema["enum"])
    if schema.get("default") is not None:
        out["default"] = schema["default"]
    return out


_COMPOSITION_KEYWORDS = ("allOf", "oneOf", "anyOf", "not")


def _properties(schema: Any, where: str) -> dict[str, Any] | None:
    """The `properties` of a request-body schema, refusing schemas it cannot read.

    Only an inline `properties` block is read. A schema composed with allOf,
    oneOf, anyOf or not used to compile with no body properties at all, without
    a word, and every field the SDK filters against them would then have been
    dropped (I-33). Such a schema is now an error naming the operation.
    """
    if not isinstance(schema, dict):
        return None
    composed = [key for key in _COMPOSITION_KEYWORDS if key in schema]
    if composed:
        raise ValueError(
            f"{where}: the request body schema uses {', '.join(composed)}, which this compiler does not read; "
            "its fields would be lost. Flatten the schema or extend compile_spec.py."
        )
    props = schema.get("properties")
    return props if isinstance(props, dict) else None


def collect(spec: dict[str, Any], source: str) -> tuple[dict[str, Any], list[str]]:
    operations: dict[str, Any] = {}
    skipped: list[str] = []

    for path, path_item in spec.get("paths", {}).items():
        shared = [_param(_resolve(p, spec)) for p in path_item.get("parameters", [])]

        for method, raw_op in path_item.items():
            if method not in HTTP_METHODS:
                continue

            op = _resolve(raw_op, spec)
            op_id = op.get("operationId")
            if not op_id:
                raise ValueError(f"{method.upper()} {path} has no operationId")

            if any(tag in EXCLUDED_TAGS for tag in op.get("tags", [])):
                skipped.append(op_id)
                continue

            params = list(shared)
            seen = {(p["name"], p["in"]) for p in params}
            for raw_param in op.get("parameters", []):
                p = _param(raw_param)
                if (p["name"], p["in"]) not in seen:
                    params.append(p)

            entry: dict[str, Any] = {
                "method": method.upper(),
                "path": path,
                "tags": op.get("tags", []),
                "path_params": [p["name"] for p in params if p["in"] == "path"],
                "query_params": [p for p in params if p["in"] == "query"],
            }

            body = op.get("requestBody")
            if body:
                content = body.get("content", {})
                entry["body_media_types"] = sorted(content)
                entry["body_required"] = bool(body.get("required", False))
                json_schema = content.get("application/json", {}).get("schema", {})
                props = _properties(json_schema, f"{source} {op_id} (application/json)")
                if props is not None:
                    entry["body_properties"] = sorted(props)
                    entry["body_required_properties"] = sorted(json_schema.get("required", []))
                form = content.get("multipart/form-data", {}).get("schema", {})
                form_props = _properties(form, f"{source} {op_id} (multipart/form-data)")
                if form_props is not None:
                    entry["form_properties"] = sorted(form_props)

            entry["statuses"] = sorted(str(s) for s in op.get("responses", {}))
            entry["source"] = source
            operations[op_id] = entry

    return operations, skipped


def compile_specs(sources: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    operations: dict[str, Any] = {}
    skipped: list[str] = []
    servers: list[str] = []

    for source, spec in sources:
        found, excluded = collect(spec, source)

        clashes = sorted(set(found) & set(operations))
        if clashes:
            raise ValueError(f"{source}: operationId(s) already defined by another document: {clashes}")

        operations.update(found)
        skipped.extend(excluded)

        spec_servers = spec.get("servers", [])
        if spec_servers:
            servers.append(spec_servers[0]["url"])

    # Every document must describe the same server, or the base URL the client
    # builds would be right for some operations and wrong for others.
    distinct = sorted(set(servers))
    if len(distinct) > 1:
        raise ValueError(f"documents disagree on the server template: {distinct}")

    return {
        "server_template": distinct[0] if distinct else None,
        "sources": sorted({source for source, _ in sources}),
        "excluded_operations": sorted(skipped),
        "operations": dict(sorted(operations.items())),
    }


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__.strip().splitlines()[-1])
        return 2

    dst = sys.argv[1]
    sources = []
    for src in sys.argv[2:]:
        with open(src, encoding="utf-8") as fh:
            sources.append((os.path.basename(src), yaml.safe_load(fh)))

    compiled = compile_specs(sources)

    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(compiled, fh, indent=1, sort_keys=True)
        fh.write("\n")

    print(
        f"compiled {len(compiled['operations'])} operations from "
        f"{len(sources)} document(s), {len(compiled['excluded_operations'])} excluded -> {dst}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

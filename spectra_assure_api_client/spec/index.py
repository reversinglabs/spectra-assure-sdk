"""The operation table, derived from the Portal OpenAPI specification.

`compiled_spec.json` is generated at build time by `tools/compile_spec.py` from `./etc/*.yaml`.
Shipping the distilled JSON rather than the YAML keeps `requests` as the only runtime dependency
and cuts the load cost from roughly 240 ms to under a millisecond.

The table is the single source of truth: which URL an operation lives at,
and which query or body parameters it accepts.
Anything the specification does not declare is dropped before the request is built.
"""

from __future__ import annotations

import json
import logging
import urllib.parse
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

# From where it is defined, not from the package root: the root is still being
# initialised when this module is imported, so a root import worked only while
# __init__ happened to import the exceptions before the client (I-24).
from spectra_assure_api_client.communication.exceptions import SpectraAssureExceptions

logger = logging.getLogger(__name__)

SPEC_FILE = Path(__file__).with_name("compiled_spec.json")


class SpectraAssureSpecError(SpectraAssureExceptions):  # was RuntimeError
    """The compiled specification is missing, malformed, or lacks an operation.

    This is a packaging fault rather than a user error: it means the build step
    did not run or the installed package is incomplete.
    """


@dataclass(frozen=True)
class Operation:
    """One operation from the specification."""

    operation_id: str
    method: str
    path: str
    path_params: tuple[str, ...] = ()
    query_params: tuple[str, ...] = ()
    body_properties: tuple[str, ...] = ()
    form_properties: tuple[str, ...] = ()
    body_media_types: tuple[str, ...] = ()
    body_required: bool = False

    @property
    def accepted_parameters(self) -> tuple[str, ...]:
        """Every parameter name the operation accepts, wherever it is carried.

        The SDK's public methods take one flat `**qp` bag and do not ask the
        caller to know whether a value travels as a query string or a JSON body,
        so membership is tested against the union.
        """
        return tuple(sorted({*self.query_params, *self.body_properties, *self.form_properties}))

    def render_path(self, **values: str) -> str:
        """Substitute path parameters into the template.

        Values are percent-encoded with no safe characters, matching the
        previous behaviour. Note that the specification writes purl segments as
        `pkg:rl/{project}/{package}@{version}`, so the `pkg:rl/`, `/` and `@`
        separators are part of the template and are never encoded -- only the
        caller-supplied values are.
        """
        missing = [p for p in self.path_params if p not in values]
        if missing:
            raise SpectraAssureSpecError(f"{self.operation_id}: missing path parameter(s): {', '.join(missing)}")

        rendered = self.path
        for name in self.path_params:
            quoted = urllib.parse.quote(str(values[name]), safe="")
            rendered = rendered.replace("{" + name + "}", quoted)
        return rendered

    def split_parameters(self, values: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        """Split a flat argument bag into (query, body), dropping unknown keys.

        Dropping rather than raising is deliberate: it is what the previous
        `qp_*` allow-lists did, and callers pass shared `**qp` dictionaries
        across several operations that accept different subsets of them.
        """
        query: dict[str, Any] = {}
        body: dict[str, Any] = {}

        for key, value in values.items():
            if key in self.query_params:
                query[key] = value
            elif key in self.body_properties or key in self.form_properties:
                body[key] = value
            else:
                logger.debug(
                    "%s does not accept parameter %r; it will not be sent",
                    self.operation_id,
                    key,
                )

        return query, body


def _build(raw: dict[str, Any]) -> dict[str, Operation]:
    operations: dict[str, Operation] = {}

    for op_id, entry in raw.get("operations", {}).items():
        operations[op_id] = Operation(
            operation_id=op_id,
            method=entry["method"],
            path=entry["path"],
            path_params=tuple(entry.get("path_params", ())),
            query_params=tuple(sorted(p["name"] for p in entry.get("query_params", []))),
            body_properties=tuple(entry.get("body_properties", ())),
            form_properties=tuple(entry.get("form_properties", ())),
            body_media_types=tuple(entry.get("body_media_types", ())),
            body_required=bool(entry.get("body_required", False)),
        )

    return operations


@lru_cache(maxsize=1)
def _table() -> dict[str, Operation]:
    """Load and cache the operation table.

    Cached for the life of the process: the table is immutable and constructing
    many clients must not re-read the file.
    """
    try:
        with SPEC_FILE.open(encoding="utf-8") as fh:
            raw = json.load(fh)
    except FileNotFoundError as exc:
        raise SpectraAssureSpecError(
            f"the compiled API specification is missing from the installed package: {SPEC_FILE}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise SpectraAssureSpecError(f"the compiled API specification is not valid JSON: {SPEC_FILE}: {exc}") from exc

    table = _build(raw)
    if not table:
        raise SpectraAssureSpecError(f"the compiled API specification declares no operations: {SPEC_FILE}")

    logger.debug("loaded %d operations from %s", len(table), SPEC_FILE)
    return table


def get_operation(operation_id: str) -> Operation:
    """Return one operation, or raise if the specification does not declare it."""
    try:
        return _table()[operation_id]
    except KeyError as exc:
        raise SpectraAssureSpecError(f"the API specification declares no operation {operation_id!r}") from exc


def operation_ids() -> tuple[str, ...]:
    """Every operation id in the table, sorted."""
    return tuple(sorted(_table()))

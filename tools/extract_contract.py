"""Extract the public API surface of the SDK into a JSON snapshot.

The snapshot is the customer contract in machine-readable form: every public
name reachable from the package root, and the shape of every public method.

Parameters are recorded structurally rather than as a formatted signature
string, so a comparison can tell an accidental change (a parameter renamed,
dropped, or made mandatory) apart from a deliberate one (a default changed on
purpose and recorded in the test's allowlist).

Usage:  python tools/extract_contract.py <path-to-package-parent> > snapshot.json
"""

from __future__ import annotations

import importlib
import inspect
import json
import sys
from typing import Any

PACKAGE = "spectra_assure_api_client"

_EMPTY = inspect.Parameter.empty


def _describe_parameters(func: Any) -> list[dict[str, Any]] | None:
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError):
        return None

    described: list[dict[str, Any]] = []
    for name, param in signature.parameters.items():
        if name == "self":
            continue
        entry: dict[str, Any] = {"name": name, "kind": param.kind.name}
        if param.default is not _EMPTY:
            # repr keeps None, False and 0 distinguishable from one another
            entry["default"] = repr(param.default)
        if param.annotation is not _EMPTY:
            entry["annotation"] = param.annotation if isinstance(param.annotation, str) else str(param.annotation)
        described.append(entry)

    return described


def _defined_by_python(cls: type, name: str) -> bool:
    """Whether `name` reaches `cls` from a class built into Python, such as BaseException.

    Those members are Python's, not the SDK's, and Python changes them between
    versions: BaseException.add_note does not exist on 3.10, has no readable
    signature on 3.11 and 3.12, and reads (self, object, /) on 3.13 and
    (self, note, /) on 3.14. Recording them tied the contract test to the Python
    that made the snapshot, so it failed on every other one.
    """
    owner = next((klass for klass in cls.__mro__ if name in vars(klass)), None)
    return owner is not None and owner.__module__ == "builtins"


def _public_members(cls: type) -> dict[str, Any]:
    out: dict[str, Any] = {}

    for name in dir(cls):
        if name.startswith("_") and name != "__init__":
            continue
        if _defined_by_python(cls, name):
            continue
        try:
            member = getattr(cls, name)
        except AttributeError:
            continue

        if inspect.isroutine(member):
            out[name] = {"kind": "method", "parameters": _describe_parameters(member)}
        elif not inspect.isclass(member):
            out[name] = {"kind": "attribute", "value": repr(member)}

    return out


def extract() -> dict[str, Any]:
    pkg = importlib.import_module(PACKAGE)
    exported = sorted(getattr(pkg, "__all__", []))

    snapshot: dict[str, Any] = {"package": PACKAGE, "__all__": exported, "exports": {}}

    for name in exported:
        obj = getattr(pkg, name)

        if not inspect.isclass(obj):
            snapshot["exports"][name] = {"kind": "value", "type": type(obj).__name__}
            continue

        entry: dict[str, Any] = {"kind": "class", "members": _public_members(obj)}

        # The mixin tree behind the client is an implementation detail and is
        # deliberately not recorded. The exception hierarchy is not: customers
        # catch these by base class, so the ancestry is part of the contract.
        if issubclass(obj, BaseException):
            entry["exception_mro"] = [c.__name__ for c in obj.__mro__ if c is not object]

        snapshot["exports"][name] = entry

    return snapshot


if __name__ == "__main__":
    sys.path.insert(0, sys.argv[1])
    json.dump(extract(), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")

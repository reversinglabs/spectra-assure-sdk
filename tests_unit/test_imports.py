"""The package imports cleanly whatever order its __init__ lists its imports in (I-24).

spec/index.py imported SpectraAssureExceptions from the package root. The root
is still being initialised at that point, so it worked only because
__init__.py imported the exceptions before the client; with the client first,
`import spectra_assure_api_client` failed with "cannot import name
'SpectraAssureExceptions' from partially initialized module".
"""

from __future__ import annotations

import ast
import shutil
import subprocess
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "spectra_assure_api_client"
ROOT = PACKAGE.name


def test_no_module_imports_from_the_package_root() -> None:
    """Modules import from where a name is defined; only __init__.py may use the root."""
    offenders = sorted(
        f"{path.relative_to(PACKAGE.parent)}:{node.lineno}"
        for path in PACKAGE.rglob("*.py")
        if path.name != "__init__.py" or path.parent != PACKAGE
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.ImportFrom) and node.module == ROOT and node.level == 0
    )

    assert offenders == []


def test_the_package_imports_with_the_client_listed_first(tmp_path: Path) -> None:
    """Reorder __init__.py the way an import sorter might, and import the copy in a fresh interpreter."""
    copy = tmp_path / ROOT
    shutil.copytree(PACKAGE, copy, ignore=shutil.ignore_patterns("__pycache__"))
    init = copy / "__init__.py"
    client = "from .spectra_assure_api_operations import SpectraAssureApiOperations\n"
    source = init.read_text(encoding="utf-8")
    assert source.count(client) == 1
    init.write_text(client + source.replace(client, ""), encoding="utf-8")

    result = subprocess.run(  # noqa: S603  fixed arguments, no shell
        [sys.executable, "-c", f"import {ROOT}; print({ROOT}.SpectraAssureApiOperations.__name__)"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "SpectraAssureApiOperations"


# ------------------------------------------------------------------ the communication package's exports (I-26)


def test_the_communication_exports_are_listed_once_and_all_exist() -> None:
    """__all__ repeated two names and left out two of the three timeouts."""
    import spectra_assure_api_client.communication as communication

    names = communication.__all__

    assert len(names) == len(set(names))
    assert all(hasattr(communication, name) for name in names)
    assert {"DEFAULT_TIMEOUT", "DEFAULT_READ_TIMEOUT", "DEFAULT_CONNECT_TIMEOUT"} <= set(names)


def test_the_communication_exports_are_exactly_what_its_init_imports() -> None:
    source = (PACKAGE / "communication" / "__init__.py").read_text(encoding="utf-8")
    imported = {
        alias.asname or alias.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }

    import spectra_assure_api_client.communication as communication

    assert set(communication.__all__) == imported

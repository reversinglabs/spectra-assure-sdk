"""The example program that is copied to examples/ must run without errors against the endpoint."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[1] / "api_client_example.py"


def test_the_example_program_runs_without_errors(run_id: str) -> None:
    """It runs with this environment (the endpoint's settings and TLS choice) and the run id.

    The run id names the example's project, so runs never collide and `make
    sweep` recognises what an interrupted run left.
    """
    result = subprocess.run(  # noqa: S603  a fixed script, no shell
        [sys.executable, str(EXAMPLE)],
        cwd=EXAMPLE.parent,
        env={**os.environ, "RLPORTAL_RUN_ID": run_id},
        capture_output=True,
        text=True,
        timeout=3600,
        check=False,
    )

    if result.returncode != 0 or "Traceback" in result.stderr:
        pytest.fail(f"{EXAMPLE.name} exited with {result.returncode}\n--- end of stderr ---\n{result.stderr[-3000:]}")

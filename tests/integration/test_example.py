"""The example program that is copied to examples/ must run without errors against the endpoint."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[1] / "api_client_example.py"
# make_logger() in the example writes <program>.log in its working directory.
EXAMPLE_LOG = EXAMPLE.with_suffix(".log")


def test_the_example_program_runs_without_errors(run_id: str, run_results_dir: Path) -> None:
    """It runs with this environment (the endpoint's settings and TLS choice) and the run id.

    The run id names the example's project, so runs never collide and `make
    sweep` recognises what an interrupted run left.

    Its stdout, stderr and log are kept in the run's results folder as
    api_client_example.1, .2 and .log, whether it passes or fails.
    """
    stdout = run_results_dir / f"{EXAMPLE.stem}.1"
    stderr = run_results_dir / f"{EXAMPLE.stem}.2"
    # the log handler appends: start from an empty log, so it holds this run only
    EXAMPLE_LOG.unlink(missing_ok=True)

    try:
        # written to the files as the program runs, so a timeout keeps what it printed
        with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
            result = subprocess.run(  # noqa: S603  a fixed script, no shell
                [sys.executable, str(EXAMPLE)],
                cwd=EXAMPLE.parent,
                env={**os.environ, "RLPORTAL_RUN_ID": run_id},
                stdout=out,
                stderr=err,
                text=True,
                timeout=3600,
                check=False,
            )
    finally:
        if EXAMPLE_LOG.exists():
            shutil.move(EXAMPLE_LOG, run_results_dir / EXAMPLE_LOG.name)

    errors = stderr.read_text(encoding="utf-8", errors="replace")
    if result.returncode != 0 or "Traceback" in errors:
        pytest.fail(
            f"{EXAMPLE.name} exited with {result.returncode} (output in {run_results_dir})\n"
            f"--- end of stderr ---\n{errors[-3000:]}"
        )

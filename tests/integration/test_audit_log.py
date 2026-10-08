"""Exporting the audit log and following the export job (was t4_audit)."""

from __future__ import annotations

import datetime

from conftest import expect

from spectra_assure_api_client import SpectraAssureApiOperations


def test_an_audit_log_export_can_be_started_and_followed(client: SpectraAssureApiOperations, run_id: str) -> None:
    """The last 30 days; t4_audit used fixed dates, which drift out of the retention period."""
    end = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    start = end - datetime.timedelta(days=30)

    response = expect(
        client.audit_log_export(
            name=run_id,
            should_create_cef=True,
            should_create_ndjson=True,
            datetime_start=start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            datetime_end=end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        201,
    )
    job = response.json()["id"]

    expect(client.audit_log_status(job_id=job), 200)

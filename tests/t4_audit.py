import logging
import os
import traceback
import uuid

from spectra_assure_api_client import SpectraAssureApiOperations

logger = logging.getLogger()


SpectraAssureApiOperations.make_logger(my_logger=logger)

prefix = "RLPORTAL_"
host = os.getenv(f"{prefix}HOST")  # may be None
server = os.getenv(f"{prefix}SERVER")  # may be None
organization = os.getenv(f"{prefix}ORG", "")
group = os.getenv(f"{prefix}GROUP", "")
token = os.getenv(f"{prefix}ACCESS_TOKEN", "")

msg = f"host: {host}, server: {server}"
logger.info(msg)

try:
    # use only args
    ah = SpectraAssureApiOperations(
        host=host,
        server=server,
        organization=organization,
        group=group,
        token=token,
        no_ssl_verify=True,
    )

    print("==================== EXPORT =========================")
    name = str(uuid.uuid1())
    should_create_cef = True
    should_create_ndjson = True
    datetime_start = "2026-01-01T00:00:00Z"
    datetime_end = "2026-06-01T00:00:00Z"

    r1 = ah.audit_log_export(
        name=name,
        should_create_cef=should_create_cef,
        should_create_ndjson=should_create_ndjson,
        datetime_end=datetime_end,
        datetime_start=datetime_start,
    )
    print(r1.json())
    print("==================== STATUS =========================")

    my_id = r1.json().get("id")
    r2 = ah.audit_log_status(
        job_id=my_id,
    )
    print("response_status:", r2, "resonse_data:", r2.json())
    print("==================== END =========================")

except Exception as e:
    print(f"exception: {e}")
    traceback.print_exc()

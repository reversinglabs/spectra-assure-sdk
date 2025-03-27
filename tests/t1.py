import logging
import traceback
import os
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
    aHandle = SpectraAssureApiOperations(
        host=host,
        server=server,
        organization=organization,
        group=group,
        token=token,
        no_ssl_verify=True,
    )
    print(f"SpectraAssureApiOperations: {aHandle}")
    if 1:  # 2025-03-14 not yet in the api
        r = aHandle.usage()
        print("ORG", r.status_code, r.text)

        r = aHandle.usage(group=group)
        print("GROUP", r.status_code, r.text)

except Exception as e:
    print(f"exception: {e}")
    traceback.print_exc()

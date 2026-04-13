import logging
import os
import traceback

from spectra_assure_api_client import SpectraAssureApiOperations

logger = logging.getLogger()


SpectraAssureApiOperations.make_logger(my_logger=logger)

prefix = "RLPORTAL_"

host = os.getenv(f"{prefix}HOST")  # may be None
server = os.getenv(f"{prefix}SERVER")  # may be None

organization = os.getenv(f"{prefix}ORG", "")
group = os.getenv(f"{prefix}GROUP", "")

token = os.getenv(f"{prefix}ACCESS_TOKEN", "")

configfile = "./myConfig.json"

msg = f"host: {host}, server: {server}"
logger.info(msg)

try:
    # combine a config file with arguments
    ah = SpectraAssureApiOperations(
        host=host,
        server=server,
        organization=organization,
        group=group,
        token=token,
        no_ssl_verify=True,
        config_file=configfile,
    )
    print(f"SpectraAssureApiOperations: {ah}")

except Exception as e:
    print(f"exception: {e}")
    traceback.print_exc()

import logging
import os
import traceback

from spectra_assure_api_client import SpectraAssureApiOperations

logger = logging.getLogger()


SpectraAssureApiOperations.make_logger(my_logger=logger)

prefix = "RLPORTAL_"
token = os.getenv(f"{prefix}ACCESS_TOKEN", "")
configfile = "./myConfig.json"

try:
    # use only a config file
    ah = SpectraAssureApiOperations(
        config_file=configfile,
        token=token,
        no_ssl_verify=True,
    )
    print(f"SpectraAssureApiOperations: {ah}")
except Exception as e:
    print(f"exception: {e}")
    traceback.print_exc()

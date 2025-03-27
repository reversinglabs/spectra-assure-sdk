import os
import logging
import traceback

from spectra_assure_api_client import SpectraAssureApiOperations

logger = logging.getLogger()


SpectraAssureApiOperations.make_logger(my_logger=logger)

prefix = "RLPORTAL_"
token = os.getenv(f"{prefix}ACCESS_TOKEN", "")
configFile = "./myConfig.json"

try:
    # use only a config file
    aHandle = SpectraAssureApiOperations(
        config_file=configFile,
        token=token,
        no_ssl_verify=True,
    )
    print(f"SpectraAssureApiOperations: {aHandle}")
except Exception as e:
    print(f"exception: {e}")
    traceback.print_exc()

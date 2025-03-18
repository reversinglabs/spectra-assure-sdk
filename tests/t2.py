import logging
import traceback

from spectra_assure_api_client import SpectraAssureApiOperations

logger = logging.getLogger()


SpectraAssureApiOperations.make_logger(my_logger=logger)

configFile = "./myConfig.json"

try:
    # use only a config file
    aHandle = SpectraAssureApiOperations(
        config_file=configFile,
    )
    print(f"SpectraAssureApiOperations: {aHandle}")
except Exception as e:
    print(f"exception: {e}")
    traceback.print_exc()

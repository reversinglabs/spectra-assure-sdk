import os
import logging

from spectra_assure_api_client import SpectraAssureApiOperations

logger = logging.getLogger()


if __name__ == "__main__":
    SpectraAssureApiOperations.make_logger(my_logger=logger)
    prefix = "RLPORTAL_"

    server = str(os.getenv(f"{prefix}SERVER"))
    organization = str(os.getenv(f"{prefix}ORG"))
    group = str(os.getenv(f"{prefix}GROUP"))
    token = str(os.getenv(f"{prefix}ACCESS_TOKEN"))
    configFile = "./myConfig.json"

    for what in [1, 2, 3]:
        try:
            if what == 1:
                # use only args
                aHandle = SpectraAssureApiOperations(
                    server=server,
                    organization=organization,
                    group=group,
                    token=token,
                )
            elif what == 2:
                # use only a config file
                aHandle = SpectraAssureApiOperations(
                    config_file=configFile,
                )
            elif what == 3:
                # combine a config file with arguments
                aHandle = SpectraAssureApiOperations(
                    config_file=configFile,
                    token=token,
                )
            print(what, aHandle)
        except Exception as e:
            print(what, e)

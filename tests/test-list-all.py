#! /usr/bin/env python3

import sys
import logging

import testGroup
import startProg

from spectra_assure_api_client import SpectraAssureApiOperations


logger = logging.getLogger()


def main() -> None:
    SpectraAssureApiOperations.make_logger(my_logger=logger)

    aOperationsHandle = startProg.startProg()
    r = testGroup.testListGroup(aOperationsHandle)
    if r is False:
        sys.exit(1)
    sys.exit(0)


main()

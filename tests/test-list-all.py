#! /usr/bin/env python3

import logging
import sys

import startProg
import testGroup

from spectra_assure_api_client import SpectraAssureApiOperations

logger = logging.getLogger()


def main() -> None:
    SpectraAssureApiOperations.make_logger(my_logger=logger)

    aoh = startProg.startProg()
    r = testGroup.testListGroup(aoh)
    if r is False:
        sys.exit(1)
    sys.exit(0)


main()

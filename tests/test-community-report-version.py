#! /usr/bin/env python3

from typing import (
    # Dict,
    # List,
    Any,
)

import sys

# import os
# import json
# import uuid
import logging

from spectra_assure_api_client import (
    SpectraAssureApiOperations,
)

import startProg

logger = logging.getLogger()

"""
path Parameters
    repository [required] string  validate: in COMMUNITIES
        Open source community identifier of the software repository that hosts the requested software package.
        Must match one of the software repositories supported by Spectra Assure Community.
    namespace [optional] string
        Namespace of the requested software package
        (according to the purl schema pkg:repository/[namespace/]package@version).
    package [required] string
        Name of the requested software package
        (according to the purl schema pkg:repository/[namespace/]package@version).
    version [optional] string
        Version of the requested software package
        (according to the purl schema pkg:repository/[namespace/]package[@version]).
        Note the Match* Query parameters
"""


def testCommunityReportPackage(
    aOperationsHandle: SpectraAssureApiOperations,
) -> bool:
    """
    query Parameters
        artifact string ::
            Qualifier that specifies the artifact file of the requested software package
            (according to the purl schema pkg:repository/[namespace/]package@version?artifact=filename.ext).
            Note that some software repositories (communities) do not support searching for artifacts.
        artifact_tag string ::
            Qualifier that specifies the artifact file of the requested software package
                by a repository-specific tag
            (according to the purl schema pkg:repository/[namespace/]package@version?artifact_tag=example_tag).
            Note that some software repositories (communities) do not support searching for artifacts.
    """

    qp: Any = None
    repository = "pypi"
    package = "numpy"
    namespace = ""
    version = "2.3.5"

    result = aOperationsHandle.community_report_version(
        repository=repository,
        package=package,
        namespace=namespace,
        version=version,
        qp=qp,
        auto_adapt_to_throttle=True,
    )

    print(f"result: {result.text}")

    return True


def main() -> None:
    SpectraAssureApiOperations.make_logger(my_logger=logger)
    aOperationsHandle = startProg.startProg()

    r = testCommunityReportPackage(aOperationsHandle)
    if r is False:
        sys.exit(1)
    sys.exit(0)


main()

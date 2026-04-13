#! /usr/bin/env python3

import logging
import os
import sys
import uuid
from typing import (
    Any,
)

import startProg
import testPackage
import testProject
import testVersion

from spectra_assure_api_client import (
    SpectraAssureApiOperations,
    SpectraAssureDownloadCriteria,
)

logger = logging.getLogger()
INPUT_PATH = os.getenv("INPUT_PATH", None)


def makeProj(aOperationsHandle: SpectraAssureApiOperations) -> str | None:
    aa = aOperationsHandle.get_additional_args()
    k = "project"
    exists = False
    if aa.get(k):
        project = str(aa.get(k))
        exists = testProject.testListProjectOnly(
            aOperationsHandle=aOperationsHandle,
            project=project,
        )
    else:
        project = f"PrTestMboot-{uuid.uuid4()}"

    if exists is False:
        r = testProject.testCreateProject(
            aOperationsHandle,
            project,
        )
        if r is False:
            return None

    return project


def makePack(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
) -> str | None:
    aa = aOperationsHandle.get_additional_args()
    k = "package"
    exists = False
    if aa.get(k):
        package = str(aa.get(k))
        exists = testPackage.testListPackageOnly(
            aOperationsHandle=aOperationsHandle,
            project=project,
            package=package,
        )
    else:
        package = f"PrTestMboot-{uuid.uuid4()}"

    if exists is False:
        r = testPackage.testCreatePackage(
            aOperationsHandle=aOperationsHandle,
            project=project,
            package=package,
        )
        if r is False:
            return None
    return package


def makeVersions(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> bool:
    filepath = str(INPUT_PATH)

    for z in ["a", "b", "c", "d"]:
        version = f"v-{uuid.uuid4()}-{z}"
        version = f"v1.2.3-{z}"

        exists = testVersion.testListVersion(
            aOperationsHandle=aOperationsHandle,
            project=project,
            package=package,
            version=version,
        )

        if exists is False:
            r = testVersion.testCreateVersion(
                aOperationsHandle=aOperationsHandle,
                project=project,
                package=package,
                version=version,
                filePath=filepath,
            )
            if r is False:
                return r

    return True


def doDownload(
    *,
    aOperationsHandle: SpectraAssureApiOperations,
    targetDir: str,
    project: str,
    package: str,
    version: str | None = None,
) -> dict[str, dict[str, Any]] | None:

    downloadcriteria = SpectraAssureDownloadCriteria(
        with_overwrite_existing_files=False,
        with_verify_existing_files=True,
        with_verify_after_download=True,
        current_strategy=[
            "AllApproved",
            "LatestApproved_ByApprovalTimeStamp",
        ][1],
    )

    return aOperationsHandle.download(
        project=project,
        package=package,
        version=version,
        target_dir=targetDir,
        download_criteria=downloadcriteria,
    )


def testVersionSteps(
    aOperationsHandle: SpectraAssureApiOperations,
) -> bool:

    project = makeProj(aOperationsHandle)
    if project is None:
        return False

    package = makePack(aOperationsHandle, project)
    if package is None:
        return False

    r = makeVersions(
        aOperationsHandle=aOperationsHandle,
        project=project,
        package=package,
    )
    if r is False:
        return r

    aa = aOperationsHandle.get_additional_args()
    targetdir = aa.get("downloadPath")
    if targetdir is None:
        targetdir = "."

    version = None

    what = doDownload(
        aOperationsHandle=aOperationsHandle,
        targetDir=targetdir,
        project=project,
        package=package,
        version=version,
    )

    action = "download latest version from package"
    print(action, what)

    k = "project"
    if aa.get(k) is None:
        # dont delete any project we did not create
        r = testProject.testDeleteProject(
            aOperationsHandle,
            project,
        )
        if r is False:
            return r

    return True


def main() -> None:
    SpectraAssureApiOperations.make_logger(my_logger=logger)

    if INPUT_PATH is None or INPUT_PATH.strip() == "":
        print("FATAL: environment var 'INPUT_PATH' is not set", file=sys.stderr)
        sys.exit(1)

    aoh = startProg.startProg()
    r = testVersionSteps(aoh)
    if r is False:
        sys.exit(1)
    sys.exit(0)


main()

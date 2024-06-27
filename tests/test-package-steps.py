#! /usr/bin/env python3

import sys
import uuid
import logging

from spectra_assure_api_client import SpectraAssureApiOperations

import testPackage
import testProject
import startProg


def testPackageSteps(
    aOperationsHandle: SpectraAssureApiOperations,
) -> bool:
    project = f"ProjTestMboot-{uuid.uuid4()}"
    projectDescription = "just a test Project"

    r = testProject.testCreateProject(
        aOperationsHandle=aOperationsHandle,
        project=project,
        description=projectDescription,
    )
    if r is False:
        return r

    package = f"PackTestMboot-{uuid.uuid4()}"
    packageDescription = "just a test Package"

    r = testPackage.testCreatePackage(
        aOperationsHandle=aOperationsHandle,
        project=project,
        package=package,
        description=packageDescription,
    )
    if r is False:
        return r

    r = testPackage.testListPackage(
        aOperationsHandle,
        project=project,
        package=package,
    )
    if r is False:
        return r

    r = testPackage.testEditPackage(
        aOperationsHandle=aOperationsHandle,
        project=project,
        package=package,
        description="Just another Package description test",
    )
    if r is False:
        return r

    r = testPackage.testListPackage(
        aOperationsHandle,
        project=project,
        package=package,
    )

    tail = "-1234"
    newName = package + tail
    r = testPackage.testEditPackage(
        aOperationsHandle=aOperationsHandle,
        project=project,
        package=package,
        newName=newName,
    )
    if r is False:
        return r

    package = newName
    r = testPackage.testListPackage(
        aOperationsHandle,
        project=project,
        package=package,
    )
    if r is False:
        return r

    r = testPackage.testDeletePackage(
        aOperationsHandle,
        project=project,
        package=package,
    )
    if r is False:
        return r

    r = testProject.testDeleteProject(
        aOperationsHandle,
        project,
    )
    if r is False:
        return r

    return True


logger = logging.getLogger()


def main() -> None:
    SpectraAssureApiOperations.make_logger(my_logger=logger)

    aOperationsHandle = startProg.startProg()
    r = testPackageSteps(aOperationsHandle)
    if r is False:
        sys.exit(1)
    sys.exit(0)


main()

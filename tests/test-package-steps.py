#! /usr/bin/env python3

import logging
import sys
import uuid

import startProg
import testPackage
import testProject

from spectra_assure_api_client import SpectraAssureApiOperations


def testPackageSteps(
    aOperationsHandle: SpectraAssureApiOperations,
) -> bool:
    project = f"ProjTestMboot-{uuid.uuid4()}"
    projectdescription = "just a test Project"

    r = testProject.testCreateProject(
        aOperationsHandle=aOperationsHandle,
        project=project,
        description=projectdescription,
    )
    if r is False:
        return r

    package = f"PackTestMboot-{uuid.uuid4()}"
    packagedescription = "just a test Package"

    r = testPackage.testCreatePackage(
        aOperationsHandle=aOperationsHandle,
        project=project,
        package=package,
        description=packagedescription,
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
    newname = package + tail

    r = testPackage.testEditPackage(
        aOperationsHandle=aOperationsHandle,
        project=project,
        package=package,
        newName=newname,
    )
    if r is False:
        return r

    package = newname
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

    aoh = startProg.startProg()
    r = testPackageSteps(aoh)
    if r is False:
        sys.exit(1)
    sys.exit(0)


main()

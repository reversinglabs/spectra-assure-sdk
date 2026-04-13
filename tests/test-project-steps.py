#! /usr/bin/env python3

import logging
import sys
import uuid

import startProg
import testProject

from spectra_assure_api_client import SpectraAssureApiOperations


def testProjectSteps(
    aOperationsHandle: SpectraAssureApiOperations,
) -> bool:
    project = f"PrTestMboot-{uuid.uuid4()}"
    description = "just a test"

    r = testProject.testCreateProject(
        aOperationsHandle,
        project,
        description,
    )
    if r is False:
        return r

    r = testProject.testListProject(
        aOperationsHandle,
        project,
    )
    if r is False:
        return r

    r = testProject.testEditProject(
        aOperationsHandle=aOperationsHandle,
        project=project,
        description="Just another description test",
    )
    if r is False:
        return r

    r = testProject.testListProject(aOperationsHandle, project)
    if r is False:
        return r

    tail = "-1234"
    newname = project + tail

    r = testProject.testEditProject(
        aOperationsHandle=aOperationsHandle,
        project=project,
        description="Just changing the name here",
        newName=newname,
    )
    if r is False:
        return r

    r = testProject.testListProject(
        aOperationsHandle,
        newname,
    )
    if r is False:
        return r

    r = testProject.testDeleteProject(
        aOperationsHandle,
        newname,
    )
    if r is False:
        return r

    return True


logger = logging.getLogger()


def main() -> None:
    SpectraAssureApiOperations.make_logger(my_logger=logger)

    aoh = startProg.startProg()
    r = testProjectSteps(aoh)
    if r is False:
        sys.exit(1)
    sys.exit(0)


main()

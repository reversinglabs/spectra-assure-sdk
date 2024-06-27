#! /usr/bin/env python3

import sys
import uuid
import logging

from spectra_assure_api_client import SpectraAssureApiOperations

import testProject
import startProg


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
    newName = project + tail

    r = testProject.testEditProject(
        aOperationsHandle=aOperationsHandle,
        project=project,
        description="Just changing the name here",
        newName=newName,
    )
    if r is False:
        return r

    r = testProject.testListProject(
        aOperationsHandle,
        newName,
    )
    if r is False:
        return r

    r = testProject.testDeleteProject(
        aOperationsHandle,
        newName,
    )
    if r is False:
        return r

    return True


logger = logging.getLogger()


def main() -> None:
    SpectraAssureApiOperations.make_logger(my_logger=logger)

    aOperationsHandle = startProg.startProg()
    r = testProjectSteps(aOperationsHandle)
    if r is False:
        sys.exit(1)
    sys.exit(0)


main()

#! /usr/bin/env python3

from typing import (
    Dict,
    Any,
)

import sys
import os
import uuid
import datetime
import logging

from spectra_assure_api_client import SpectraAssureApiOperations

import testProject
import testPackage
import testVersion
import startProg
import testing

INPUT_PATH = os.getenv("INPUT_PATH", None)


def testVersionSteps(
    aOperationsHandle: SpectraAssureApiOperations,
) -> bool:
    # test: project: create, list, modify, list, delete: DONE

    # ----------------------------------------
    project = f"PrTestMboot-{uuid.uuid4()}"
    description = "just a test Project"

    r = testProject.testCreateProject(
        aOperationsHandle,
        project,
        description,
    )
    if r is False:
        return r

    # ----------------------------------------
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

    # ----------------------------------------
    version = f"{uuid.uuid4()}"
    qp: Dict[str, Any] = {
        "publisher": "ReversingLabs Testing",
        "product": "a reversingLabs test",
        "category": "Development",  # test also a error category , 400 {"error":"category: Invalid software category"}
        "license": "Do What The F*ck You Want To Public License",
        "platform": "Containers",  # 400 {"error":"platform: Invalid software platform"} if not one of enum
        "release_date": f"{datetime.datetime.now()}",
        "build": "version",  # try "repro"
    }
    filePath = str(INPUT_PATH)

    action = "Scan Version"
    print(f"{action} {project}/{package}@{version}: {filePath} :: {qp}")

    # create a version with upload (scan)
    data = aOperationsHandle.scan(
        project=project,
        package=package,
        version=version,
        file_path=filePath,
        auto_adapt_to_throttle=True,  # optional
        **qp,
    )

    r = testing.standardReturn(action, data)
    if r is False:
        return r

    # ----------------------------------------
    # list the version
    r = testVersion.testListVersion(
        aOperationsHandle=aOperationsHandle,
        project=project,
        package=package,
        version=version,
    )
    if r is False:
        return r

    # ----------------------------------------
    # do various edit-list actions
    action = "Edit Version"
    qp = {
        "publisher": "ReversingLabs Testing 2",
        "product": "a reversingLabs test 2",
        "category": "Administration",  # test also a erro category , 400 {"error":"category: Invalid software category"}
        "license": "iMatix Standard Function Library Agreement",
        "platform": "Linux",  # 400 {"error":"platform: Invalid software platform"} if not one of enum
        "release_date": "2023-12-30T00:00:00Z",
        "is_released": True,
    }
    data = aOperationsHandle.edit(
        project=project,
        package=package,
        version=version,
        auto_adapt_to_throttle=True,  # optional
        **qp,
    )

    r = testing.standardReturn(action, data)
    if r is False:
        return r

    # ----------------------------------------
    # list the version
    r = testVersion.testListVersion(
        aOperationsHandle=aOperationsHandle,
        project=project,
        package=package,
        version=version,
    )
    if r is False:
        return r

    for reportName in aOperationsHandle.current_report_names():
        qp = {}
        r = testVersion.testReportVersion(
            aOperationsHandle,
            project=project,
            package=package,
            version=version,
            reportType=reportName,
            **qp,
        )

    # ----------------------------------------
    r = testPackage.testListPackageOnly(
        aOperationsHandle=aOperationsHandle,
        project=project,
        package=package,
    )
    if r is False:
        return r

    # ----------------------------------------
    r = testPackage.testDeletePackage(
        aOperationsHandle=aOperationsHandle,
        project=project,
        package=package,
    )
    if r is False:
        return r

    # ----------------------------------------
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

    if INPUT_PATH is None or INPUT_PATH.strip() == "":
        print("FATAL: environment var 'INPUT_PATH' is not set", file=sys.stderr)
        sys.exit(1)
    print(f"INFO: INPUT_PATH: {INPUT_PATH}", file=sys.stderr)

    aOperationsHandle = startProg.startProg()
    r = testVersionSteps(aOperationsHandle)
    if r is False:
        sys.exit(1)
    sys.exit(0)


main()

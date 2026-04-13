#! /usr/bin/env python3

import datetime
import logging
import os
import sys
import uuid
from typing import (
    Any,
)

import startProg
import testing
import testPackage
import testProject
import testVersion

from spectra_assure_api_client import SpectraAssureApiOperations

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
    packagedescription = "just a test Package"

    r = testPackage.testCreatePackage(
        aOperationsHandle=aOperationsHandle,
        project=project,
        package=package,
        description=packagedescription,
    )
    if r is False:
        return r

    # ----------------------------------------
    version = f"{uuid.uuid4()}"
    qp: dict[str, Any] = {
        "publisher": "ReversingLabs Testing",
        "product": "a reversingLabs test",
        "category": "Development",  # test also a error category , 400 {"error":"category: Invalid software category"}
        "license": "Do What The F*ck You Want To Public License",
        "platform": "Containers",  # 400 {"error":"platform: Invalid software platform"} if not one of enum
        "release_date": f"{datetime.datetime.now()}",
        "build": "version",  # try "repro"
    }
    file_path = str(INPUT_PATH)

    action = "Scan Version"
    print(f"{action} {project}/{package}@{version}: {file_path} :: {qp}")

    # create a version with upload (scan)
    data = aOperationsHandle.scan(
        project=project,
        package=package,
        version=version,
        file_path=file_path,
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

    is_done = False
    while not is_done:
        # is the analysis finished (otherwise no reports are ready)
        z = testVersion.testStatusVersion(
            aOperationsHandle=aOperationsHandle,
            project=project,
            package=package,
            version=version,
        )
        print(z)
        if z.get("analysis", {}).get("status", "") != "PROCESSING":
            is_done = True

    for reportname in aOperationsHandle.current_report_names():
        qp = {}
        print(reportname)
        r = testVersion.testReportVersion(
            aOperationsHandle,
            project=project,
            package=package,
            version=version,
            reportType=reportname,
            **qp,
        )
        # print(r)

    r = testVersion.testVersionRlSafe(
        aOperationsHandle,
        project=project,
        package=package,
        version=version,
        **qp,
    )
    if r is False:
        return r

    # ----------------------------------------
    # list the version
    r = testVersion.testSyncVersion(
        aOperationsHandle=aOperationsHandle,
        project=project,
        package=package,
        version=version,
    )
    if r is False:
        return r

    if 1:
        r = testVersion.testRejectVersion(
            aOperationsHandle=aOperationsHandle,
            project=project,
            package=package,
            version=version,
        )
        if r is False:
            return r
    else:
        r = testVersion.testApproveVersion(
            aOperationsHandle=aOperationsHandle,
            project=project,
            package=package,
            version=version,
        )
        if r is False:
            return r

        r = testVersion.testRevokeVersion(
            aOperationsHandle=aOperationsHandle,
            project=project,
            package=package,
            version=version,
        )
        if r is False:
            return r

    r = testVersion.testListVersion(
        aOperationsHandle=aOperationsHandle,
        project=project,
        package=package,
        version=version,
    )
    if r is False:
        return r

    # ----------------------------------------
    r = testPackage.testListPackageOnly(
        aOperationsHandle=aOperationsHandle,
        project=project,
        package=package,
    )
    if r is False:
        return r

    if 0:
        return True

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

    aoh = startProg.startProg()
    r = testVersionSteps(aoh)
    if r is False:
        sys.exit(1)
    sys.exit(0)


main()

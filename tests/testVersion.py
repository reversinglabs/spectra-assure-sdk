# python3

from typing import (
    Any,
    Dict,
)

import datetime

from spectra_assure_api_client import SpectraAssureApiOperations
import testing


def testReportVersion(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    reportType: str,
    **qp: Any,
) -> bool:
    action = "Report Version"
    data = aOperationsHandle.report(
        project=project,
        package=package,
        version=version,
        reportType=reportType,
        auto_adapt_to_throttle=True,
        **qp,
    )

    return testing.standardReturn(action, data)


def testStatusVersion(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    **qp: Any,
) -> bool:
    action = "Status Version"

    qp = {
        "download": True,
    }

    data = aOperationsHandle.status(
        project=project,
        package=package,
        version=version,
        auto_adapt_to_throttle=True,
        **qp,
    )

    r = testing.standardReturn(action, data)
    if r is False:
        return r

    # "analysis/report/info/portal/download"
    jData = data.json()
    download = jData.get("analysis", {}).get("report", {}).get("info", {}).get("portal", {}).get("download", None)
    print(action, "DOWNLOAD", f"{download}")

    return True


def testChecksVersion(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
) -> bool:
    action = "Checks Version"

    data = aOperationsHandle.checks(
        project=project,
        package=package,
        version=version,
        auto_adapt_to_throttle=True,
    )

    return testing.standardReturn(action, data)


def testListVersion(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
) -> bool:
    action = "List Version"

    data = aOperationsHandle.list(
        project=project,
        package=package,
        version=version,
        auto_adapt_to_throttle=True,
    )

    return testing.standardReturn(action, data)


def testDeleteVersion(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
) -> bool:

    data = aOperationsHandle.delete(
        project=project,
        package=package,
        version=version,
        auto_adapt_to_throttle=True,
    )

    action = "Delete Version"
    return testing.standardReturn(action, data)


def testCreateVersion(
    *,
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    filePath: str,
) -> bool:
    qp: Dict[str, Any] = {
        "publisher": "ReversingLabs Testing",
        "product": "a reversingLabs test",
        "category": "Development",  # test also a error category , 400 {"error":"category: Invalid software category"}
        "license": "MIT License Modern Variant",
        "platform": "Containers",  # 400 {"error":"platform: Invalid software platform"} if not one of enum
        "release_date": f"{datetime.datetime.now()}",
        "build": "version",  # try "repro"
    }

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

    return True

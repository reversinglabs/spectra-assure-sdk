# python3

from typing import (
    Any,
    Dict,
)

import datetime

from spectra_assure_api_client import SpectraAssureApiOperations
import testing


def testVersionRlSafe(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    **qp: Any,
) -> bool:
    action = "Rl-Safe"

    data = aOperationsHandle.rl_safe(
        project=project,
        package=package,
        version=version,
        auto_adapt_to_throttle=True,
        **qp,
    )
    print(f"{action}:: {project}/{package}@{version} :: {data}")

    data2 = aOperationsHandle.rl_safe_download(
        target_dir="./downloads",
        project=project,
        package=package,
        version=version,
        auto_adapt_to_throttle=True,
        **qp,
    )
    print(f"{action}:: {project}/{package}@{version} :: {data2}")

    return testing.standardReturn(action, data)


def testReportVersion(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    reportType: str,
    **qp: Any,
) -> bool:
    action = f"Report Version {reportType}"
    data = aOperationsHandle.report(
        project=project,
        package=package,
        version=version,
        report_type=reportType,
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
) -> Any:
    # action = "Status Version"

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

    jData = data.json()
    return jData


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


def testSyncVersion(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
) -> bool:
    action = "Sync Version"

    data = aOperationsHandle.sync(
        project=project,
        package=package,
        version=version,
        auto_adapt_to_throttle=True,
    )

    return testing.standardReturn(action, data)


def testApproveVersion(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
) -> bool:
    action = "Approve Version"

    qp: Dict[str, Any] = {
        "reason": f"some dummy reason: {action}",
    }

    data = aOperationsHandle.approve(
        project=project,
        package=package,
        version=version,
        auto_adapt_to_throttle=True,
        **qp,
    )

    return testing.standardReturn(action, data)


def testRejectVersion(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
) -> bool:
    action = "Reject Version"

    qp: Dict[str, Any] = {
        "reason": f"some dummy reason: {action}",
    }

    data = aOperationsHandle.reject(
        project=project,
        package=package,
        version=version,
        auto_adapt_to_throttle=True,
        **qp,
    )

    return testing.standardReturn(action, data)


def testRevokeVersion(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
) -> bool:
    action = "Revoke Version"

    qp: Dict[str, Any] = {
        "reason": f"some dummy reason: {action}",
    }

    data = aOperationsHandle.revoke(
        project=project,
        package=package,
        version=version,
        auto_adapt_to_throttle=True,
        **qp,
    )

    return testing.standardReturn(action, data)

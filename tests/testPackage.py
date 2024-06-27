# python3
from typing import (
    Dict,
    Any,
)

from spectra_assure_api_client import SpectraAssureApiOperations
import testVersion
import testing


def testEditPackage(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
    description: str | None = None,
    newName: str | None = None,
) -> bool:
    action = "Edit Package"

    qp = {}
    if description is not None:
        qp["description"] = description
    if newName is not None:
        qp["name"] = newName

    data = aOperationsHandle.edit(
        project=project,
        package=package,
        auto_adapt_to_throttle=True,
        **qp,
    )
    return testing.standardReturn(action, data)


def testDeletePackage(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> bool:
    action = "Delete Package"

    data = aOperationsHandle.delete(
        project=project,
        package=package,
        auto_adapt_to_throttle=True,
    )

    return testing.standardReturn(action, data)


def testListPackageOnly(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> bool:
    action = "List Package"

    data = aOperationsHandle.list(
        project=project,
        package=package,
        auto_adapt_to_throttle=True,
    )

    return testing.standardReturn(action, data)


def testListPackage(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> bool:
    action = "List Package"

    data = aOperationsHandle.list(
        project=project,
        package=package,
        auto_adapt_to_throttle=True,
    )

    r = testing.standardReturn(action, data)
    if r is False:
        return r

    jData = data.json()
    for p in jData.get("versions"):
        version = p.get("version")

        r = testVersion.testListVersion(
            aOperationsHandle,
            project=project,
            package=package,
            version=version,
        )
        if r is False:
            return r

        r = testVersion.testChecksVersion(
            aOperationsHandle,
            project=project,
            package=package,
            version=version,
        )
        if r is False:
            return r

        qp: Dict[str, Any] = {}
        r = testVersion.testStatusVersion(
            aOperationsHandle,
            project=project,
            package=package,
            version=version,
            **qp,
        )
        if r is False:
            return r

        qp = {"download": True}  # status download=true
        r = testVersion.testStatusVersion(
            aOperationsHandle,
            project=project,
            package=package,
            version=version,
            **qp,
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
            if r is False:
                return r

    return True


def testCreatePackage(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
    description: str | None = None,
) -> bool:
    action = "Create Package"

    qp = {}
    if description is not None:
        qp["description"] = description

    data = aOperationsHandle.create(
        project=project,
        package=package,
        auto_adapt_to_throttle=True,
        **qp,
    )

    return testing.standardReturn(action, data)

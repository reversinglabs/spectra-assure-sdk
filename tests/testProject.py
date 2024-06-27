# python3

from spectra_assure_api_client import SpectraAssureApiOperations

import testPackage
import testing


def testListProjectOnly(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
) -> bool:
    action = "List Project"

    data = aOperationsHandle.list(
        project=project,
        auto_adapt_to_throttle=True,
    )

    r = testing.standardReturn(action, data)
    if r is False:
        return r

    return True


def testListProject(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
) -> bool:
    action = "List Project"

    data = aOperationsHandle.list(
        project=project,
        auto_adapt_to_throttle=True,
    )

    r = testing.standardReturn(action, data)
    if r is False:
        return r

    jData = data.json()
    for p in jData.get("packages"):
        package = p.get("name")
        print(action, f"package: {package}")

        r = testPackage.testListPackage(
            aOperationsHandle,
            project=project,
            package=package,
        )
        if r is False:
            return r

    return True


def testCreateProject(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    description: str | None = None,
) -> bool:
    action = "Create Project"

    qp = {}
    if description is not None:
        qp["description"] = description

    data = aOperationsHandle.create(
        project=project,
        auto_adapt_to_throttle=True,
        **qp,
    )

    return testing.standardReturn(action, data)


def testEditProject(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    description: str | None = None,
    newName: str | None = None,
) -> bool:
    action = "Edit Project"

    qp = {}

    if description is not None:
        qp["description"] = description

    if newName is not None:
        qp["name"] = newName

    data = aOperationsHandle.edit(
        project=project,
        auto_adapt_to_throttle=True,
        **qp,
    )

    return testing.standardReturn(action, data)


def testDeleteProject(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
) -> bool:
    action = "Delete Project"

    data = aOperationsHandle.delete(
        project=project,
        auto_adapt_to_throttle=True,
    )

    return testing.standardReturn(action, data)

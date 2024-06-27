# python3

from spectra_assure_api_client import SpectraAssureApiOperations
import testProject

import testing


def testListGroup(
    aOperationsHandle: SpectraAssureApiOperations,
) -> bool:
    action = "List Group"
    # testing group: show all current projects or none

    data = aOperationsHandle.list(auto_adapt_to_throttle=True)
    r = testing.standardReturn(action, data)
    if r is False:
        return r

    jData = data.json()
    for p in jData.get("projects"):
        project = p.get("name")
        print(action, f"Project = {project}")

        if project == "SAP Crystal Server":  # reports are to large
            continue

        r = testProject.testListProject(
            aOperationsHandle=aOperationsHandle,
            project=project,
        )
        if r is False:
            return r

    return True

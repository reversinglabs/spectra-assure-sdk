# python3

import testing
import testProject

from spectra_assure_api_client import SpectraAssureApiOperations


def testListGroup(
    aOperationsHandle: SpectraAssureApiOperations,
) -> bool:
    action = "List Group"
    # testing group: show all current projects or none

    data = aOperationsHandle.list(auto_adapt_to_throttle=True)
    r = testing.standardReturn(action, data)
    if r is False:
        return r

    jd = data.json()
    for p in jd.get("projects"):
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

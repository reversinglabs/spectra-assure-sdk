# SpectraAssureApiOperationsList

Execute a list() API call.

## Targets

- Group
- Project
- Package
- Version

When 'project' is not specified, we list all projects in the current group.
When 'package' is not specified, we list all packages in the current project.
When 'version' is not specified, we list all versions in the current package.
When a 'version' is specified, we list the details of this version.

## Arguments

- project: str | None, optional.
- package: str | None, optional.
- version: str | None, optional.
- auto_adapt_to_throttle: bool, default False, optional.

## Query parameters

None

## Responses

Returns the 'requests.result' of the list() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [listGroup](https://docs.secure.software/api-reference/#tag/Group/operation/listGroupProjects)
- [listProject](https://docs.secure.software/api-reference/#tag/Project/operation/listPackages)
- [listPackage](https://docs.secure.software/api-reference/#tag/Package/operation/listVersions)
- [listVersion](https://docs.secure.software/api-reference/#tag/Version/operation/versionInfo)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)

```python

def list_projects(
    api_client: SpectraAssureApiOperations,
) -> Any:
    response = api_client.list()
    data = response.json()
    print("Projects: ", json.dumps(data, indent=2))
    return data


def list_project(
    api_client: SpectraAssureApiOperations,
    project: str,
) -> Any:
    project_info = api_client.list(project=project)
    project_data = project_info.json()
    print("Project detail: ", json.dumps(project_data, indent=2))
    return project_data


def list_package(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> Any:
    package_info = api_client.list(
        project=project,
        package=package,
    )
    package_data = package_info.json()
    print("Package details: ", json.dumps(package_data, indent=2))
    return package_data


def list_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
) -> None:
    version_info = api_client.list(
        project=project,
        package=package,
        version=version,
    )
    version_data = version_info.json()
    print("Version details: ", json.dumps(version_data, indent=2))
    return version_data
```

# SpectraAssureApiOperationsCreate

Execute a create() API call to create a new project or a new package in the Spectra Assure Portal.

For creating a version, use scan().

## Targets

- Project
- Package

If we only specify 'project', we create a new 'project' in the specified 'group'.
If we specify 'project' and 'package', we create a new 'package' in that 'project'.

## Arguments

- project: str, mandatory.
- package: str | None, optional.
- auto_adapt_to_throttle: bool, default False, optional.
- qp: Dict[str,Any], optional.

## Query parameters

| Name          | Type                  | Default   | Validation |
| --            | --                    | --        | --         |
| description   | `string`              |           | <= 500 characters |

'description' is supported as a query parameter for both 'project' and 'package'.

## Responses

Returns the 'requests.result' of the create() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.post().

## Portal API documentation

- [createPackage](https://docs.secure.software/api-reference/#tag/Package/operation/postPackage)
- [createProject](https://docs.secure.software/api-reference/#tag/Project/operation/postProject)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)

```python

def create_project(
    api_client: SpectraAssureApiOperations,
    project: str,
) -> None:
    qp: Dict[str, Any] = {
        "description": "SDK created project",
    }
    rr = api_client.create(
        project=project,
        **qp,
    )
    print("Create project", rr.status_code, rr.text)


def create_package(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> None:
    qp: Dict[str, Any] = {
        "description": "SDK created project",
    }

    rr = api_client.create(
        project=project,
        package=package,
        **qp,
    )
    print("Create package", rr.status_code, rr.text)
```

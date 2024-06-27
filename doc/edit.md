# SpectraAssureApiOperationsEdit

Execute an edit() API call to modify the details for the specified item.

## Targets

- Project
- Package
- Version

## Arguments

- project: str, mandatory.
- package: str | None, optional.
- version: str | None, optional.
- auto_adapt_to_throttle: bool, default False, optional.
- qp: Dict[str,Any], optional.


## Query parameters

**Project and Package**

| Name          | Type                  | Default   | Validation |
| --            | --                    | --        | --         |
| name          | `string`              |           | Special characters \/:*?"<>\| are not supported. |
| description   | `string`              |           | <= 500 characters |


**Version**

| Name          | Type                  | Default   | Validation |
| --            | --                    | --        | --         |
| is_released   | `boolean`             |           |       |
| product       | `string`              |           | <= 200 characters |
| publisher     | `string`              |           | <= 200 characters |
| category      | `string`              | "Other"   | Enum: |
| license       | `string`              | "Unknown" | Enum: |
| platform      | `string`              | "Other"   | Enum: |
| release_date  | `string` <date-time>  |           |       |


## Responses

Returns the 'requests.result' of the edit() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.patch().

## Portal API documentation

- [editProject](https://docs.secure.software/api-reference/#tag/Project/operation/patchProject)
- [editPackage](https://docs.secure.software/api-reference/#tag/Package/operation/patchPackage)
- [editVersion](https://docs.secure.software/api-reference/#tag/Version/operation/patchVersion)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def edit_project(
    api_client: SpectraAssureApiOperations,
    project: str,
) -> None:
    qp: Dict[str, Any] = {
        "description": "API edited",
        "name": project,
    }
    rr = api_client.edit(
        project=project,
        **qp,
    )
    print("Update project", rr.status_code, rr.text)


def edit_package(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> None:
    qp: Dict[str, Any] = {
        "description": "API edited",
        "name": package,
    }
    rr = api_client.edit(
        project=project,
        package=package,
        **qp,
    )
    print("Update package", rr.status_code, rr.text)


def edit_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
) -> None:
    qp: Dict[str, Any] = {
        "publisher": "ReversingLabs Testing 2",
        "product": "a reversingLabs test 2",
        "license": "iMatix Standard Function Library Agreement",
    }

    rr = api_client.edit(
        project=project,
        package=package,
        version=version,
        **qp,
    )
    print("Update version", rr.status_code, rr.text)
```

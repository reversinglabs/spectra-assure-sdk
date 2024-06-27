# SpectraAssureApiOperationsDelete

Execute a delete() API call.

## Targets

- Project
- Package
- Version

If we only specify 'project', we delete that 'project' and all its 'packages' and 'versions'.
If we specify 'project' and 'package', we delete that 'package' and all its 'versions'.
If we specify 'project', 'package' and 'version', we delete only that 'version'.

## Arguments

- project: str, mandatory.
- package: str | None, optional.
- version: str | None, optional.
- auto_adapt_to_throttle: bool, default False, optional.
- qp: Dict[str,Any], optional.

## Query parameters

| Name          | Type                  | Default   | Validation |
| --            | --                    | --        | --         |
| build   | `string`              |     'version'      | Enum: 'repro', 'version' |

The optional 'build' query parameter is supported only for the 'version' target.
It should be used when working with reproducible builds. The parameter specifies if the request should apply to the main artifact (version) or to the reproducible build artifact (repro).

## Responses

Returns the 'requests.result' of the delete() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [deleteProject](https://docs.secure.software/api-reference/#tag/Project/operation/deleteProject)
- [deletePackage](https://docs.secure.software/api-reference/#tag/Package/operation/deletePackage)
- [deleteVersion](https://docs.secure.software/api-reference/#tag/Version/operation/deleteVersion)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)

```python

def delete_project(
    api_client: SpectraAssureApiOperations,
    project: str,
) -> None:
    rr = api_client.delete(
        project=project,
    )
    print(f"Delete Project {project}", rr.status_code, rr.text)


def delete_package(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> None:
    rr = api_client.delete(
        project=project,
        package=package,
    )
    print(f"Delete Package {package}", rr.status_code, rr.text)


def delete_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
) -> None:
    rr = api_client.delete(
        project=project,
        package=package,
        version=version,
    )
    print(f"Delete Version {version}", rr.status_code, rr.text)
```

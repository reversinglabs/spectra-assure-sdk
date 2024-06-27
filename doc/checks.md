# SpectraAssureApiOperationsChecks

Execute a checks() API call for the specified `project`, `package`, `version`.

## Targets

- Version

## Arguments

- project: str, mandatory.
- package: str, mandatory.
- version: str, mandatory.
- auto_adapt_to_throttle: bool, default False, optional.

## Query parameters

None

## Responses

Returns the 'requests.result' of the checks() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [versionChecks](https://docs.secure.software/api-reference/#tag/Version/operation/getVersionChecks)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)

```python

def check_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
) -> None:
    rr = api_client.checks(
        project=project,
        package=package,
        version=version,
    )
    print("Version check:", json.dumps(rr.json(), indent=2))
```

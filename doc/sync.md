# SpectraAssureApiOperationsSync

Execute a sync() API call. (Rescan a version.)

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

Returns the 'requests.result' of the sync() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [syncVersion](https://docs.secure.software/api-reference/#tag/Version/operation/syncVersion)

## Code example

```python

def sync_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
) -> None:
    rr = api_client.sync(
        project=project,
        package=package,
        version=version,
    )
    print("Sync Version", rr.status_code, rr.text)
    return int(rr.status_code)```

# SpectraAssureApiOperationsRevoke

Execute a revoke() API call.

## Targets

- Version

## Arguments

- project: str, mandatory.
- package: str, mandatory.
- version: str, mandatory.
- reason: str, mandatory. Why the approval status is changed. It is passed as a keyword argument to the request body.
- auto_adapt_to_throttle: bool, default False, optional.

## Body parameters

| Name          | Type      | Default   | Validation |
| --            | --        | --        | --         |
| reason        | `string`  | mandatory | The API sets no minimum length. |

The Portal API requires a `reason`. Leaving it out, or passing anything that is not a string (`None` included),
raises `SpectraAssureInvalidAction` before any request is sent.

## Responses

Returns the 'requests.result' of the revoke() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception; also raised when `reason` is missing or is not a string.
- any other exception from requests.get().

## Portal API documentation

- [revokeVersion](https://docs.secure.software/api-reference/#tag/Version/operation/revokeVersion)

## Code example

```python

def revoke_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    reason: str,
) -> Any:
    rr = api_client.revoke(
        project=project,
        package=package,
        version=version,
        reason=reason,
    )
    print("Version revoke", rr.status_code, rr.text)
    return rr
```

# SpectraAssureApiOperationsReject

Execute a reject() API call.

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

Returns the 'requests.result' of the reject() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception; also raised when `reason` is missing or is not a string.
- any other exception from requests.get().

## Portal API documentation

- [rejectVersion](https://docs.secure.software/api-reference/#tag/Version/operation/rejectVersion)

## Code example

```python

def reject_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    reason: str,
) -> Any:
    rr = api_client.reject(
        project=project,
        package=package,
        version=version,
        reason=reason,
    )
    print("Version reject", rr.status_code, rr.text)
    return rr
```

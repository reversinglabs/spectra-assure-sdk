# SpectraAssureApiOperationsFilestream.filestream_approve

Execute a filestream_approve() API call to approve the specified `file_id`.

> **Note:**
> File Stream files are standalone: they do not belong to a project or a package
> and they have no versions.
> The server-generated `file_id`, returned when the file is created, is the only handle.

## Targets

- File Stream file

> **Note:**
> `reason` is **mandatory** here.
> On the project/package/version equivalent it is optional.
> An empty `reason` raises `SpectraAssureInvalidAction`.

`reason` is sent in the request body, not as a query parameter.

The file must have the 'Undetermined' or 'Rejected' approval status.
The file must also be fully processed: the API answers 400 while the analysis is
still running. `filestream_sync()` may start a new analysis, so run it after the
approval calls rather than before.

The approval states are `Undetermined`, `Approved`, `ApprovedAutomatically`,
`ApprovalRejected` and `ApprovalRevoked`.

## Arguments

- file_id: str, mandatory.
- reason: str, **mandatory**.
- auto_adapt_to_throttle: bool | None, default None (inherit the client setting), optional.

## Responses

Returns the 'requests.result' of the filestream_approve() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [approveFilestreamFile](https://docs.secure.software/api-reference/#tag/File-Stream/operation/approveFilestreamFile)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def filestream_approve_file(
    api_client: SpectraAssureApiOperations,
    file_id: str,
    reason: str,
) -> Any:
    # unlike the project/package/version approve(), 'reason' is mandatory here
    rr = api_client.filestream_approve(
        file_id=file_id,
        reason=reason,
    )
    print("Filestream approve", rr.status_code, rr.text)
    return rr
```

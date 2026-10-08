# SpectraAssureApiOperationsFilestream.filestream_reject

Execute a filestream_reject() API call to reject the specified `file_id`.

> **Note:**
> File Stream files are standalone: they do not belong to a project or a package
> and they have no versions.
> The server-generated `file_id`, returned when the file is created, is the only reference to a File Stream file.

## Targets

- File Stream file

> **Note:**
> `reason` is **mandatory** here.
> On the project/package/version equivalent it is optional.
> An empty `reason` raises `SpectraAssureInvalidAction`.

`reason` is sent in the request body, not as a query parameter.

The file must have the 'Undetermined' approval status.
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

Returns the 'requests.result' of the filestream_reject() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [rejectFilestreamFile](https://docs.secure.software/api-reference/#tag/File-Stream/operation/rejectFilestreamFile)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def filestream_reject_file(
    api_client: SpectraAssureApiOperations,
    file_id: str,
    reason: str,
) -> Any:
    # unlike the project/package/version reject(), 'reason' is mandatory here
    rr = api_client.filestream_reject(
        file_id=file_id,
        reason=reason,
    )
    print("Filestream reject", rr.status_code, rr.text)
    return rr
```

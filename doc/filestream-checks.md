# SpectraAssureApiOperationsFilestream.filestream_checks

Execute a filestream_checks() API call to show the checks performed on the specified `file_id`.

> **Note:**
> File Stream files are standalone: they do not belong to a project or a package
> and they have no versions.
> The server-generated `file_id`, returned when the file is created, is the only reference to a File Stream file.

## Targets

- File Stream file

## Arguments

- file_id: str, mandatory.
- auto_adapt_to_throttle: bool | None, default None (inherit the client setting), optional.

## Responses

Returns the 'requests.result' of the filestream_checks() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [getFilestreamFileChecks](https://docs.secure.software/api-reference/#tag/File-Stream/operation/getFilestreamFileChecks)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def filestream_check_file(
    api_client: SpectraAssureApiOperations,
    file_id: str,
) -> None:
    rr = api_client.filestream_checks(
        file_id=file_id,
    )
    print("Filestream check:", rr.status_code)
```

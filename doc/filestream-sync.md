# SpectraAssureApiOperationsFilestream.filestream_sync

Execute a filestream_sync() API call to re-analyze the specified `file_id`, for example after an engine update.

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

Returns the 'requests.result' of the filestream_sync() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [syncFilestreamFile](https://docs.secure.software/api-reference/#tag/File-Stream/operation/syncFilestreamFile)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def filestream_sync_file(
    api_client: SpectraAssureApiOperations,
    file_id: str,
) -> Any:
    # 202: a re-scan was started. 200: the analysis is already up to date.
    rr = api_client.filestream_sync(
        file_id=file_id,
    )
    print("Filestream sync", rr.status_code, rr.text)
    return rr
```

# SpectraAssureApiOperationsFilestream.filestream_rl_safe

Execute a filestream_rl_safe() API call to create a download link for the [RL-SAFE archive](https://docs.secure.software/concepts/analysis-reports#rl-safe-archive) of the specified `file_id`.

> **Note:**
> File Stream files are standalone: they do not belong to a project or a package
> and they have no versions.
> The server-generated `file_id`, returned when the file is created, is the only reference to a File Stream file.

## Targets

- File Stream file

`filestream_rl_safe()` returns the response containing the `download_link`.

`filestream_rl_safe_download()` additionally fetches the archive into `target_dir`:

- target_dir: str, mandatory. The directory where the file will be downloaded; MUST exist.
- file_id: str, mandatory.
- rename_archive: bool, default True, optional.
- max_wait_time_for_archive: int, default 300, optional. Seconds to wait while the API answers 202.
- auto_adapt_to_throttle: bool | None, default None, optional.

With `rename_archive=True` the archive is renamed to `<file_id>.rl-safe`.
For project/package/version archives the name is derived from the purl,
but a File Stream file has no purl, so the file ID is used instead.

It returns a tuple: `(download_ok: bool, file_path: str)`.

The 200 response includes `download_link`, `file_name` and `expiration_timestamp`.
`filestream_rl_safe_download()` names the archive after the file ID rather than
the returned `file_name`, because the file ID is the reference to the file used in all calls.

### Waiting for the archive

The API answers 202 while the analysis is in progress because the archive does not
exist yet. 
`filestream_rl_safe()` returns that response as-is, for callers that want to
decide for themselves.

`filestream_rl_safe_download()` waits it out and re-requests the archive until
the API answers 200, for up to `max_wait_time_for_archive` seconds (default 300).
Pass 0 to fail immediately instead. If that time runs out while the API is still
answering 202, it raises `SpectraAssureWaitTimeoutExceeded`.

Any other non-200 status is a real error and is raised immediately, without waiting.

Two messages can be returned for a 202 status: the file is *not done with analysis*, or it *does not have complete analysis*.
The second may never resolve, and is waited out just the same; the exception text includes the API's message.

## Arguments

- file_id: str, mandatory.
- auto_adapt_to_throttle: bool | None, default None (inherit the client setting), optional.

## Responses

Returns the 'requests.result' of the filestream_rl_safe() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [getRlSafeFilestreamArchive](https://docs.secure.software/api-reference/#tag/File-Stream/operation/getRlSafeFilestreamArchive)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def filestream_rl_safe_file(
    api_client: SpectraAssureApiOperations,
    file_id: str,
) -> Any:
    # 202 means the analysis has not finished yet; the archive is not ready
    rr = api_client.filestream_rl_safe(
        file_id=file_id,
    )
    print("Filestream rl_safe", rr.status_code, rr.text)
    return rr


def filestream_rl_safe_with_download_and_rename(
    api_client: SpectraAssureApiOperations,
    target_dir: str,
    file_id: str,
    max_wait_time_for_archive: int = 300,
) -> Any:
    # the archive is renamed to '<file_id>.rl-safe':
    # File Stream files have no purl to name the archive after.
    #
    # While the analysis is still running the API answers 202 and no archive
    # exists yet; the SDK waits up to 'max_wait_time_for_archive' seconds for it.
    # Pass 0 to fail immediately instead of waiting.
    download_ok, file_path = api_client.filestream_rl_safe_download(
        target_dir=target_dir,
        file_id=file_id,
        rename_archive=True,
        max_wait_time_for_archive=max_wait_time_for_archive,
    )
    print("Filestream rl_safe download", download_ok, file_path)
    return download_ok, file_path
```

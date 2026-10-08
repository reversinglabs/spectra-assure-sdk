# SpectraAssureApiOperationsFilestream.filestream_download

A custom download implementation for File Stream files, combining `filestream_status()` and `filestream_list()` to download an approved file.

> **Note:**
> File Stream files are standalone: they do not belong to a project or a package
> and they have no versions.
> The server-generated `file_id`, returned when the file is created, is the only reference to a File Stream file.

## Targets

- File Stream file

As requesting a download URL impacts your Portal download capacity,
the download link is only requested when the file has passed all the criteria.

### SpectraAssureDownloadCriteria

The criteria that select between candidate *versions* have no effect here:
a File Stream file is a single file with no versions,
so `current_strategy` is ignored.

These criteria do apply:

- `wait_for_scan_done`: wait until the analysis reports 'DONE'.
- `max_wait_time_for_scan_done`: how long to wait for that, in seconds.
- `must_be_approved`: only download the file if it has been approved.
- `with_overwrite_existing_files`
- `with_verify_after_download`
- `with_verify_existing_files`

> **Note:**
> The approval status is not part of the `filestream_status()` response,
> so when `must_be_approved` is set, `filestream_list()` is paged through to find the file.
> Both `Approved` and `ApprovedAutomatically` count as approved.

## Arguments

- target_dir: str, mandatory. The directory where the file will be downloaded; MUST exist.
- file_id: str, mandatory.
- download_criteria: SpectraAssureDownloadCriteria | None, default None, optional.
- auto_adapt_to_throttle: bool | None, default None (inherit the client setting), optional.

## Responses

Returns a dict keyed by `file_id`, or None if the file was skipped
(not finished processing, or not approved while `must_be_approved` is set).

The shape matches `download()` so both can be handled alike:

```python
{
    "<file_id>": {
        "analysis": "done",
        "approved": "approved",
        "hashes": {"md5": "...", "sha1": "...", "sha256": "..."},
        "downloaded": True,
        "target_file_path": "/abs/path/to/file",
    }
}
```

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidPath: the target directory does not exist or is not a directory.
- SpectraAssureUnexpectedNoDataFound: our exception.
- SpectraAssureNoDownloadUrlInResult: our exception.
- any other exception from requests.get().

## Portal API documentation

- [getFilestreamFileStatus](https://docs.secure.software/api-reference/#tag/File-Stream/operation/getFilestreamFileStatus)
- [listFilestreamFiles](https://docs.secure.software/api-reference/#tag/File-Stream/operation/listFilestreamFiles)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def filestream_download_file(
    api_client: SpectraAssureApiOperations,
    target_dir: str,
    file_id: str,
) -> Any:
    download_criteria = SpectraAssureDownloadCriteria(
        wait_for_scan_done=True,
        max_wait_time_for_scan_done=60,
        with_overwrite_existing_files=False,
        with_verify_after_download=True,
        with_verify_existing_files=True,
        # 'current_strategy' has no effect here:
        # there are no versions to choose between
    )

    download_data = api_client.filestream_download(
        target_dir=target_dir,
        file_id=file_id,
        download_criteria=download_criteria,
    )
    print("Filestream download:", json.dumps(download_data, indent=2, default=str))
    return download_data
```

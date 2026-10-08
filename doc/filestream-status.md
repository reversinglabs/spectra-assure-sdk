# SpectraAssureApiOperationsFilestream.filestream_status

Execute a filestream_status() API call for the specified `file_id`.

> **Note:**
> File Stream files are standalone: they do not belong to a project or a package
> and they have no versions.
> The server-generated `file_id`, returned when the file is created, is the only reference to a File Stream file.

## Targets

- File Stream file

If `download=true` is specified, the file is not automatically downloaded.
This parameter only returns the download URL in the response for further processing.
However, requesting the download URL affects your Portal download capacity.
The capacity gets reduced by the artifact's file size even if you don't download it from the link.

By default, every download link is valid only for 60 seconds, after which it can be requested again.

The `analysis.status` field reports 'PROCESSING' or 'DONE'.


## Arguments

- file_id: str, mandatory.
- auto_adapt_to_throttle: bool | None, default None (inherit the client setting), optional.
- qp: Dict[str,Any], optional.

## Query parameters

| Name | Type | Default | Validation |
| -- | -- | -- | -- |
| download | `boolean` | false |  |

## Responses

Returns the 'requests.result' of the filestream_status() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [getFilestreamFileStatus](https://docs.secure.software/api-reference/#tag/File-Stream/operation/getFilestreamFileStatus)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def filestream_status_file(
    api_client: SpectraAssureApiOperations,
    file_id: str,
    with_download_url: bool = False,
) -> Any:
    qp: dict[str, Any] = {}

    if with_download_url is True:
        qp["download"] = True  # this will subtract from your quota

    response = api_client.filestream_status(
        file_id=file_id,
        **qp,
    )
    print(f"Filestream status check: {response.status_code}")
    # print(json.dumps(response.json(), indent=2))
    return response.json()


def filestream_wait_for_analysis(
    api_client: SpectraAssureApiOperations,
    file_id: str,
    max_wait: int = 600,
) -> None:
    n = 0
    step = 10

    while True:
        status = filestream_status_file(
            api_client=api_client,
            file_id=file_id,
        )
        state = status.get("analysis", {}).get("status", "").lower()
        if state == "done":
            return
        if state == "error":
            raise RuntimeError(f"the analysis of File Stream file {file_id} ended in ERROR")
        if n >= max_wait:
            raise RuntimeError(f"the analysis of File Stream file {file_id} took more than {max_wait} s")

        time.sleep(step)  # give the analyzer time to finish
        n = n + step
        print(f"wait for filestream scan status to complete: {n}")
```

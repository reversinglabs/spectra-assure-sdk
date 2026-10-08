# SpectraAssureApiOperationsFilestream.filestream_scan

Execute a filestream_scan() API call to upload a file to the File Stream and scan it.

> **Note:**
> File Stream files are standalone: they do not belong to a project or a package
> and they have no versions.
> The server-generated `file_id`, returned when the file is created, is the only reference to a File Stream file.

## Targets

- File Stream file

If the file is not readable (or does not exist in the provided path),
the operation will raise an exception `SpectraAssureInvalidAction`.

Only one file can be uploaded per request.
The File Stream does not support uploading multiple versions of the same file or creating diffs.
Use Portal Projects for those features.

The file is streamed as an `application/octet-stream` request body, with the file
name carried in the `Content-Disposition` header and the size in `Content-Length`.
This is the path intended for large uploads.

The call answers 201 on success.
The response contains the server-generated file ID in the `id` field.
This file ID is required by every other File Stream call to work with the uploaded file.

## Arguments

- file_path: str, mandatory, must exist and be readable.
- auto_adapt_to_throttle: bool | None, default None (inherit the client setting), optional.
- qp: Dict[str,Any], optional.

## Query parameters

| Name | Type | Default | Validation |
| -- | -- | -- | -- |
| version | `string` | 'Generic' | <= 200 characters. Metadata only: File Stream files have no versions in the sense of separate software packages in the Portal. |
| product | `string` |  | <= 200 characters |
| publisher | `string` |  | <= 200 characters |
| category | `string` | "Other" | Enum: |
| license | `string` | "Unknown" | Enum: |
| platform | `string` | "Other" | Enum: |
| release_date | `string` <date-time> |  |  |

## Responses

Returns the 'requests.result' of the filestream_scan() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [scanFilestreamFile](https://docs.secure.software/api-reference/#tag/File-Stream/operation/scanFilestreamFile)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def filestream_scan_file(
    api_client: SpectraAssureApiOperations,
    file_path: str,
) -> str:
    qp: dict[str, Any] = {
        "publisher": "ReversingLabs Testing",
        "product": "a reversingLabs test",
        "category": "Development",
        "license": "MIT License Modern Variant",
        "platform": "Containers",
        "release_date": f"{datetime.datetime.now()}",
        "version": "2026.04.09",  # metadata only: File Stream files have no versions
    }

    rr = api_client.filestream_scan(
        file_path=file_path,
        **qp,
    )
    print("Filestream scan", rr.status_code, rr.text)

    if rr.status_code not in [200, 201]:
        raise RuntimeError(f"expected 200 or 201, got {rr.status_code}: {rr.text[:300]}")

    file_id = str(rr.json().get("id"))
    print("Filestream scan, new file_id:", file_id)
    return file_id
```

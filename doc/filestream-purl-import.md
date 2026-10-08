# SpectraAssureApiOperationsFilestream.filestream_purl_import

Execute a filestream_purl_import() API call to import a file into the File Stream from a package URL (PURL).

> **Note:**
> File Stream files are standalone: they do not belong to a project or a package
> and they have no versions.
> The server-generated `file_id`, returned when the file is created, is the only reference to a File Stream file.

## Targets

- File Stream file

The file to import may require authentication.
Provide either `auth_user` together with `auth_pass`, or `bearer_token`.
Combining a bearer token with a user name and password raises `SpectraAssureInvalidAction`.

The SDK takes these as `auth_user`, `auth_pass` and `bearer_token`,
and maps them to the `auth-user`, `auth-pass` and `bearer-token` fields the API expects.

The specified PURL must be in one of the
[supported formats](https://docs.secure.software/portal/filestream#supported-urls-and-purls).

The file is downloaded and analyzed asynchronously.
The response contains the server-generated file ID in the `id` field;
use `filestream_status()` to track the download and analysis progress.

## Arguments

- purl: str, mandatory.
- auth_user: str | None, default None, optional.
- auth_pass: str | None, default None, optional.
- bearer_token: str | None, default None, optional.
- auto_adapt_to_throttle: bool | None, default None (inherit the client setting), optional.
- qp: Dict[str,Any], optional.

## Query parameters

| Name | Type | Default | Validation |
| -- | -- | -- | -- |
| version | `string` | 'Generic' | <= 200 characters. Metadata only: File Stream files have no versions. |
| product | `string` |  | <= 200 characters |
| publisher | `string` |  | <= 200 characters |
| category | `string` | "Other" | Enum: |
| license | `string` | "Unknown" | Enum: |
| platform | `string` | "Other" | Enum: |
| release_date | `string` <date-time> |  |  |
| max_size | `integer` |  | Maximum file size to attempt to download, in bytes. |

## Responses

Returns the 'requests.result' of the filestream_purl_import() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [importFilestreamPURL](https://docs.secure.software/api-reference/#tag/File-Stream/operation/importFilestreamPURL)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def filestream_purl_import_file(
    api_client: SpectraAssureApiOperations,
    purl: str,
    auth_user: str | None = None,
    auth_pass: str | None = None,
    bearer_token: str | None = None,
) -> str:
    # purl: pkg:pypi/pyaudio@0.2.13?artifact=PyAudio-0.2.13-cp311-cp311-win_amd64.whl
    qp: dict[str, Any] = {
        "publisher": "ReversingLabs Testing",
        "product": "a reversingLabs test",
        "category": "Development",
        "license": "MIT License Modern Variant",
        "platform": "Containers",
        "release_date": f"{datetime.datetime.now()}",
    }

    rr = api_client.filestream_purl_import(
        purl=purl,
        auth_user=auth_user,
        auth_pass=auth_pass,
        bearer_token=bearer_token,
        **qp,
    )
    print("Filestream purl_import", rr.status_code, rr.text)

    if rr.status_code not in [200, 201]:
        raise RuntimeError(f"expected 200 or 201, got {rr.status_code}: {rr.text[:300]}")

    return str(rr.json().get("id"))
```

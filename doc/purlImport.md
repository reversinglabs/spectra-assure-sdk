# SpectraAssureApiOperationsPurlImport

Execute a purl-import() API call that downloads a file from a PURL and uploads it for scanning on the Portal.
The specified PURL must be in one of the [supported formats](https://docs.secure.software/portal/filestream#supported-urls-and-purls).
The file is imported to the Portal as a new version in a project and package.

## Targets

- Version

## Arguments

- project: str, mandatory.
- package: str, mandatory.
- version: str, mandatory.
- purl: str, mandatory, max len: 4096, must start with `pkg:`.
- auth_user: str, optional
- auth_pass: str, optional
- bearer_token: str , optional
- auto_adapt_to_throttle: bool, default False, optional.
- qp: Dict[str,Any], optional.

This operation always needs the package URL for the file to be provided in the parameter `purl`.

## Query parameters

| Name          | Type                  | Default   | Validation |
| --            | --                    | --        | --    |
| replace       | `boolean`             | false     |       |
| force         | `boolean`             | false     |       |
| diff_with     | `string`              |           |       |
| product       | `string`              |           | <= 200 characters |
| publisher     | `string`              |           | <= 200 characters |
| category      | `string`              | "Other"   | Enum: |
| license       | `string`              | "Unknown" | Enum: |
| platform      | `string`              | "Other"   | Enum: |
| release_date  | `string` <date-time>  |           |       |
| max_size      | `int`                 |           |       |

&nbsp;

If the target version already exists, use 'replace'.

If you have reached the maximum amount of versions allowed on the Portal,
use 'force' to delete the oldest version and make room for the new one.

## Responses

Returns the 'requests.result' of the url-import() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [importVersionPURL](https://docs.secure.software/api-reference/#tag/Version/operation/importVersionPURL)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def purl_import_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    purl: str,
    auth_user: str | None = None,
    auth_pass: str | None = None,
    bearer_token: str | None = None,
) -> int:
    # e.g. purl: "pkg:pypi/pyaudio@0.2.13?artifact=PyAudio-0.2.13-cp311-cp311-win_amd64.whl"
    qp: dict[str, Any] = {
        "replace": False,
        "force": True,
        "publisher": "ReversingLabs Testing",
        "product": "a reversingLabs test",
        "category": "Development",
        "license": "MIT License Modern Variant",
        "platform": "Containers",
        "release_date": f"{datetime.datetime.now()}",
        "build": "version",
    }

    # create a version with upload via url (url_import)
    rr = api_client.purl_import(
        project=project,
        package=package,
        version=version,
        purl=purl,
        auth_user=auth_user,
        auth_pass=auth_pass,
        bearer_token=bearer_token,
        **qp,
    )

    print("purl_import Version", rr.status_code, rr.text)
    return int(rr.status_code)

```

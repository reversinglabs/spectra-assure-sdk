# SpectraAssureApiOperationsUrlImport

Execute a url-import() API call that downloads a file from a URL and uploads it for scanning on the Portal. The file is imported to the Portal as a new version in a project and package.

## Targets

- Version

## Arguments

- project: str, mandatory.
- package: str, mandatory.
- version: str, mandatory.
- url: str, mandatory, max len: 4096, must be in URI format (having '://').
- auth_user: str, optional
- auth_pass: str, optional
- bearer_token: str , optional
- auto_adapt_to_throttle: bool, default False, optional.
- qp: Dict[str,Any], optional.

This operation always needs the URL to the file to be provided in the parameter `url`.

## Query parameters

| Name          | Type                  | Default   | Validation |
| --            | --                    | --        | --    |
| max_size      | `int`                 |           |       |
| replace       | `boolean`             | false     |       |
| force         | `boolean`             | false     |       |
| diff_with     | `string`              |           |       |
| product       | `string`              |           | <= 200 characters |
| publisher     | `string`              |           | <= 200 characters |
| category      | `string`              | "Other"   | Enum: |
| license       | `string`              | "Unknown" | Enum: |
| platform      | `string`              | "Other"   | Enum: |
| release_date  | `string` <date-time>  |           |       |

&nbsp;

If the target version already exists, use 'replace'.

If you have reached the maximum amount of versions allowed on the Portal, use 'force' to delete the oldest version and make room for the new one.

## Responses

Returns the 'requests.result' of the url-import() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [importVersion](https://docs.secure.software/api-reference/#tag/Version/operation/importVersion)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def url_import_version(
    *,
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    url: str,
    auth_user: str | None = None,
    auth_pass: str | None = None,
    bearer_token: str | None = None,
) -> int:
    qp: Dict[str, Any] = {
        "replace": False,
        "force": True,
        "publisher": "ReversingLabs Testing",
        "product": "A ReversingLabs test",
        "category": "Development",
        "license": "MIT License Modern Variant",
        "platform": "Containers",
        "release_date": f"{datetime.datetime.now()}",
        "build": "version",
    }

    # create a version with upload via url (url_import)
    rr = api_client.url_import(
        project=project,
        package=package,
        version=version,
        url=url,
        auth_user=auth_user,
        auth_pass=auth_pass,
        bearer_token=bearer_token,
        **qp,
    )

    print("url_import Version", rr.status_code, rr.text)
    return int(rr.status_code)
```

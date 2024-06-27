# SpectraAssureApiOperationsScan

Execute a scan() API call to upload a file and scan it, creating a version in a Portal project and package.

## Targets

- Version

## Arguments

- project: str, mandatory.
- package: str, mandatory.
- version: str, mandatory.
- filePath: str, mandatory, must exist.
- auto_adapt_to_throttle: bool, default False, optional.
- qp: Dict[str,Any], optional.


This operation always needs the path to the file to be provided in the parameter `filePath`.

If the file is not readable (or does not exist in the provided path), the operation will raise an exception `InvalidAction`.

## Query parameters

| Name          | Type                  | Default   | Validation |
| --            | --                    | --        | --         |
| build         | `string`              | 'version' | Enum: 'repro', 'version' |
| replace       | `boolean`             | false     | |
| force         | `boolean`             | false     | This parameter is incompatible with build=repro. |
| diff_with     | `string`              |           | This parameter is incompatible with build=repro. |
| product       | `string`              |           | <= 200 characters |
| publisher     | `string`              |           | <= 200 characters |
| category      | `string`              | "Other"   | Enum: |
| license       | `string`              | "Unknown" | Enum: |
| platform      | `string`              | "Other"   | Enum: |
| release_date  | `string` <date-time>  |           |       |


If re-scanning the same file/version, use 'replace'.

If you have reached the maximum amount of versions allowed on the Portal, use 'force' to delete the oldest version and make room for the new one.

## Responses

Returns the 'requests.result' of the scan() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [scanVersion](https://docs.secure.software/api-reference/#tag/Version/operation/scanVersion)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def scan_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    file_path: str,
) -> int:
    qp: Dict[str, Any] = {
        "publisher": "ReversingLabs Testing",
        "product": "a reversingLabs test",
        "category": "Development",
        "license": "MIT License Modern Variant",
        "platform": "Containers",
        "release_date": f"{datetime.datetime.now()}",
        "build": "version",
    }

    # create a version with upload (scan)
    rr = api_client.scan(
        project=project,
        package=package,
        version=version,
        file_path=file_path,
        **qp,
    )
    print("Create/Scan Version", rr.status_code, rr.text)
    return int(rr.status_code)
```

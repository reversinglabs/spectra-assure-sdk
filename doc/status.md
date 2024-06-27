# SpectraAssureApiOperationsStatus

Execute a status() API call for the specified `project`, `package`, `version`.

## Targets

- Version

## Arguments

- project: str, mandatory.
- package: str, mandatory.
- version: str, mandatory.
- auto_adapt_to_throttle: bool, default False, optional.
- qp: Dict[str,Any], optional.

## Query parameters

| Name          | Type                  | Default   | Validation |
| --            | --                    | --        | --         |
| build         | `string`              | 'version' | Enum: "repro", "version" |
| download      | `boolean`             | false     |            |

If `download=true` is specified, the file is not automatically downloaded.
This parameter only returns the download URL in the response for further processing.
However, requesting the download URL affects your Portal download capacity.
The capacity gets reduced by the artifact's file size even if you don't download it from the link.

If your user account doesn't have permission to download files from the Portal, the API responds with an error and the download capacity remains unaffected.

By default, every download link is valid only for 60 seconds, after which it can be requested again.

## Responses

Returns the 'requests.result' of the status() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [versionStatus](https://docs.secure.software/api-reference/#tag/Version/operation/getVersionStatus)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def status_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    with_download_url: bool = False,
) -> Any:
    qp: Dict[str, Any] = {}

    if with_download_url is True:
        qp["download"] = True  # this will subtract from your quota

    version_check_response = api_client.status(
        project=project,
        package=package,
        version=version,
        **qp,
    )
    print("Version status check:")
    print(json.dumps(version_check_response.json(), indent=2))
    return version_check_response.json()
```

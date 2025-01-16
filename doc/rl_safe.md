# SpectraAssureApiOperationsRlSafe

Execute a rl_safe() API call for the specified `project`, `package`, `version`.

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
| build         | `string`              | 'version' | Enum: 'repro', 'version' |

This optional parameter specifies if the request should apply to the main artifact (version) or to the reproducible build artifact (repro).

## Responses

Returns the 'requests.result' of the status() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

### Download and rename the RL-SAFE archive

By default, the response includes the URL from which you can download the RL-SAFE archive. 
When the URL expires, you have to send a new request to get it again.

As the URL expires relatively quickly, an additional call `version_rl_safe_with_download_and_rename` is available to simplify the process.
It downloads the RL-SAFE archive from the URL and renames the archive to:

`<target_dir>/<purl>.rl_safe`

The `target_dir` should alread exist. The subdirectory `<project>` will be automatically created.

The resulting file name is generated according to the purl:

`<target_dir>/<package>@<version>.rl_safe`


## Portal API documentation

- [getRlSafeVersionArchive](https://docs.secure.software/api-reference/#tag/Version/operation/getRlSafeVersionArchive)


## Code example

```python
def version_rl_safe(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    **qp: Any,
) -> bool:
    action = "Rl-Safe"

    rr = aOperationsHandle.rl_safe(
        project=project,
        package=package,
        version=version,
        auto_adapt_to_throttle=True,
        **qp,
    )
    print("Version ", action, rr.status_code, rr.text)
    return rr


def version_rl_safe_with_download_and_rename(
    aOperationsHandle: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    **qp: Any,
) -> bool:
    action = "Rl-Safe with download and rename"

    download_ok, file_path = aOperationsHandle.rl_safe_download(
        target_dir=".",
        project=project,
        package=package,
        version=version,
        auto_adapt_to_throttle=True,
        **qp,
    )

    if download_ok is True:
        print("Version ", action, file_path)

    return download_ok, file_path
```

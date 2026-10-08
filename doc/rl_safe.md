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

Returns the 'requests.result' of the rl_safe() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

### Download and rename the RL-SAFE archive

By default, the response includes the URL from which you can download the RL-SAFE archive. 
When the URL expires, you have to send a new request to get it again.

As the URL expires relatively quickly, an additional call `rl_safe_download()` is available to simplify the process.
It requests the URL, downloads the RL-SAFE archive and renames the archive to:

`<target_dir>/<project>/<package>@<version>.rl-safe`

The `target_dir` must already exist. The subdirectory `<project>` is created automatically.
An existing archive with that name is replaced.
With `rename_archive=False` the archive keeps the name it was downloaded under.

Arguments of `rl_safe_download()`:

- target_dir: str, mandatory.
- project: str, mandatory.
- package: str, mandatory.
- version: str, mandatory.
- rename_archive: bool, default True, optional.
- max_wait_time_for_archive: int, default 300, optional. Seconds to wait while the API answers 202.
- auto_adapt_to_throttle: bool | None, default None, optional.
- qp: Dict[str,Any], optional. Query parameters, as for `rl_safe()`.

It returns `(downloaded: bool, file_path: str)`.

#### Waiting for the archive

The API answers 202 while the analysis is in progress because the archive does not exist yet.
`rl_safe()` returns that response as it is, for callers that want to decide for themselves.

`rl_safe_download()` waits it out and re-requests the archive until the API answers 200,
for up to `max_wait_time_for_archive` seconds (default 300).
Pass 0 to fail immediately instead.
If that time runs out while the API is still answering 202, it raises `SpectraAssureWaitTimeoutExceeded`.

Any other status than 200 is a real error and raises `SpectraAssureInvalidAction` at once, without waiting.

The API can return one of two messages for the 202 status: the version is *not done with analysis*, or it *does not have complete analysis*.
The first resolves by itself; the second may not.
The SDK does not tell them apart, so a version whose analysis will never complete uses up the whole
`max_wait_time_for_archive` before `SpectraAssureWaitTimeoutExceeded` is raised.
The exception text includes the message the API sent, so the cause can be read from it.
Decrease the `max_wait_time_for_archive` value to shorten the waiting time.

> **Note:**
> Earlier versions raised `SpectraAssureInvalidAction` on a 202 instead of waiting.
> Code that relied on that can pass `max_wait_time_for_archive=0` and catch `SpectraAssureWaitTimeoutExceeded`.


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

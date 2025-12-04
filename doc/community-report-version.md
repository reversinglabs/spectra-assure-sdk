# SpectraAssureApiOperationsCommunityReportVersion

Execute a community_report_version() API call to view the report for a package version in Spectra Assure Community.

## Targets

Spectra Assure Community

## Arguments

- repository: string , mandatory. Must match one of the software repositories supported by Spectra Assure Community.
- namespace: string , optional.
- package: string, mandatory.
- version: string, optional.
- auto_adapt_to_throttle: bool, default False, optional.
- qp: Dict[str,Any], optional.


For valid query types, see the [Portal API documentation](https://docs.secure.software/api-reference/#tag/Community).

## Query parameters

| Name             | Type     | Default | Validation |
| --               | --       | --      | --         |
| artifact         | `string` |         | optional   |
| artifact_tag     | `string` |         | optional   |

## Responses

Returns the 'requests.result' of the community_report_version() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.post().

## Portal API documentation

- [CommunityVersionAssessment](https://docs.secure.software/api-reference/#tag/Community/operation/getCommunityVersionAssessment)

## Code example

From [examples/api_client_example.py](../examples/api_client_example.py)

```python
def community_report_version(
    api_client: SpectraAssureApiOperations,
):
    qp: Any = None
    repository = "pypi"
    package = "numpy"
    namespace = ""
    version = "2.3.5"

    result = api_client.community_report_version(
        repository=repository,
        package=package,
        namespace=namespace,
        version=version,
        qp=qp,
        auto_adapt_to_throttle=True,
    )

    if result.status_code == 200:
        print(json.dumps(json.loads(result.text), indent=2))

    return None
```

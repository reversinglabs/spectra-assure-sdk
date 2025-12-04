# SpectraAssureApiOperationsCommunityReportPackage

Execute a community_report_package() API call to report on a packages in the secure.software community.

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
| match_pattern    | `string` |         | Should not be used together with `version` or `match_expression`. |
| match_expression | `string` |         | Should not be used together with `version` or `match_pattern`. |
| offset_integer   | `int`    | 0       | optional   |
| limit            | `int`    | 5       | range [1 .. 100] |

## Responses

Returns the 'requests.result' of the community_report_package() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.post().

## Portal API documentation

- [CommunityPackageAssessment](https://docs.secure.software/api-reference/#tag/Community/operation/getCommunityPackageMetadata)

## Code example

From [examples/api_client_example.py](../examples/api_client_example.py)

```python
def community_report_package(
    api_client: SpectraAssureApiOperations,
):
    qp: Any = None
    repository = "pypi"
    package = "numpy"

    result = api_client.community_report_package(
        repository=repository,
        package=package,
        qp=qp,
        auto_adapt_to_throttle=True,
    )

    if result.status_code == 200:
        print(json.dumps(json.loads(result.text), indent=2))

    return None
```

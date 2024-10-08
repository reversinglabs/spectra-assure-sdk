# SpectraAssureApiOperationsReport

Execute a report() API call for the specified `project`, `package`, `version`.

## Targets

- Version

## Arguments

- project: str, mandatory.
- package: str, mandatory.
- version: str, mandatory.
- report_type: str, mandatory, must be one of:
    - cyclonedx
    - rl-checks
    - rl-cve
    - rl-json
    - rl-uri
    - sarif
    - spdx
- auto_adapt_to_throttle: bool, default False, optional.
- qp: Dict[str,Any], optional.


This operation always needs the report name string specified in the parameter `report_type`.

The current valid list of report names is available from `SpectraAssureApiOperations.current_report_names()`.

If the requested report name is invalid, the operation will raise an exception `SpectraAssureInvalidAction`.

## Query parameters

| Name          | Type                  | Default   | Validation |
| --            | --                    | --        | --         |
| build         | `string`              | 'version' | Enum: 'repro', 'version' |

This optional parameter specifies if the request should apply to the main artifact (version) or to the reproducible build artifact (repro).

## Responses

Returns the 'requests.result' of the report() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

The result data is not always in the JSON format. Specifically, the 'rl-cve' and 'rl-uri' reports are comma-separated (CSV) data, so don't use automatic result.json() format.

When a new report format is introduced on the Portal, and the new report does not exist yet for the specified 'version', expect 404 as a result when requesting the new report format. You will need to rescan the uploaded file to produce a new set of reports. After the rescan, you can request the report in the new format.

## Portal API documentation

- [versionReport](https://docs.secure.software/api-reference/#tag/Version/operation/getVersionReport)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def report_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    report_type: str,
) -> Any:
    report_data = api_client.report(
        project=project,
        package=package,
        version=version,
        report_type=report_type,
    )
    if report_type in ['rl-cve', 'rl-uri']:
        print("Report details:", report_data.text)
        return report_data.text

    report_details = report_data.json()
    print("Report details:", json.dumps(report_details, indent=2))
    return report_details
```

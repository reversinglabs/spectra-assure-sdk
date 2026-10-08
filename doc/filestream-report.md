# SpectraAssureApiOperationsFilestream.filestream_report

Execute a filestream_report() API call to download an analysis report for the specified `file_id`.

> **Note:**
> File Stream files are standalone: they do not belong to a project or a package
> and they have no versions.
> The server-generated `file_id`, returned when the file is created, is the only reference to a File Stream file.

## Targets

- File Stream file

Only one report type can be downloaded per request.

The supported report types are:

- `cyclonedx`
- `rl-checks`
- `rl-cve`
- `rl-json`
- `rl-summary-pdf`
- `rl-uri`
- `sarif`
- `spdx`

`SpectraAssureApiOperations.filestream_report_types()` returns this list.

> **Note:**
> `rl-diff` is **not** available for File Stream files: there are no versions to diff against.
> Requesting it raises `SpectraAssureInvalidAction`.


> **Note:**
> The API answers 202 while the analysis has not finished:
> the report is not available yet, try again later.

## Arguments

- file_id: str, mandatory.
- report_type: str, mandatory. Case-insensitive.
- auto_adapt_to_throttle: bool | None, default None (inherit the client setting), optional.

## Responses

Returns the 'requests.result' of the filestream_report() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [getFilestreamReport](https://docs.secure.software/api-reference/#tag/File-Stream/operation/getFilestreamReport)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def filestream_report_file(
    api_client: SpectraAssureApiOperations,
    file_id: str,
    report_type: str,
) -> Any:
    # The supported report types are: cyclonedx, rl-checks, rl-cve, rl-json,
    # rl-summary-pdf, rl-uri, sarif, spdx.
    # 'rl-diff' is not supported: File Stream files have no versions to diff.
    print("Supported report types:", api_client.filestream_report_types())

    # 202 means the analysis has not finished yet; until_ready asks again
    report_data = until_ready(
        lambda: api_client.filestream_report(
            file_id=file_id,
            report_type=report_type,
        ),
        f"Filestream report {report_type}",
    )
    print(f"Filestream report {report_type}: {report_data.status_code}")

    # not all reports are json: rl-summary-pdf returns a pdf document
    if report_type in ["rl-summary-pdf"]:
        return report_data.content

    return report_data.json()
```

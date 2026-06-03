# SpectraAssureApiOperationsAuditLogExport

Start the export of an audit log file from the Portal. Logs can be exported in the following formats: CEF, NDJSON. Optionally, log contents can be controlled by applying one or more filters.

## Targets

The audit log interface.

## Arguments

- name: str, mandatory.
- datetime_start: str, mandatory.
- datetime_end: str, mandatory.
- should_create_cef: bool, mandatory.
- should_create_ndjson: bool, mandatory.
- filters: list[Any] | None, optional.
- auto_adapt_to_throttle: bool, default False, optional.

## Query parameters

None

## Responses

Returns the 'requests.result' of the community_user_account() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.post().

## Portal API documentation

- [Start an audit log export](https://docs.secure.software/api-reference/#tag/Audit/operation/createAuditExportAPI)

## Code example

From [examples/api_client_example.py](../examples/api_client_example.py)
Audit/operation/export_job_create
```python
def audit_log_export(
    api_client: SpectraAssureApiOperations,
    *,
    name: str,
    should_create_cef: bool,
    should_create_ndjson: bool,
    datetime_start: str,
    datetime_end: str,
    filters: list[Any] | None = None,
) -> str:
    r1 = api_client.audit_log_export(
        name=name,
        should_create_cef=should_create_cef,
        should_create_ndjson=should_create_ndjson,
        datetime_end=datetime_end,
        datetime_start=datetime_start,
        filters=filters,
    )
    print("audit-log-export response", r1, r1.json())

    my_id = r1.json().get("id")
    print("audit-log-export", my_id)

    return my_id
```

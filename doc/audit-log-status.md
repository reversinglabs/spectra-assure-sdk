# SpectraAssureApiOperationsAuditLogStatus

Check the status of an audit log export. If the export is successful, the response includes the contents of the log file.


## Targets

The audit log interface.

## Arguments

- job_id: str, mandatory.
- auto_adapt_to_throttle: bool, default False, optional.

## Query parameters

None

## Responses

Returns the 'requests.result' of the community_user_account() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [Check log export status](https://docs.secure.software/api-reference/#tag/Audit/operation/getAuditExportStatus)

## Code example

From [examples/api_client_example.py](../examples/api_client_example.py)

```python
def audit_log_status(
    api_client: SpectraAssureApiOperations,
    *,
    job_id: str,
) -> Any:
    r2 = api_client.audit_log_status(
        job_id=job_id,
    )
    return r2.json
```

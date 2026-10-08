# SpectraAssureApiOperationsFilestream.filestream_list

Execute a filestream_list() API call to list the files in the File Stream of the current group.

> **Note:**
> File Stream files are standalone: they do not belong to a project or a package
> and they have no versions.
> The server-generated `file_id`, returned when the file is created, is the only reference to a File Stream file.

## Targets

- File Stream file

This is the only call that reports a file's `approval_status`;
`filestream_status()` does not include it.

> **Note:**
> The `approval_status` *filter* accepts four values, but the `approval_status`
> *reported for a file* can also be `ApprovedAutomatically`.
> Filtering on `Approved` will therefore not return files that were approved automatically.

## Arguments

- auto_adapt_to_throttle: bool | None, default None (inherit the client setting), optional.
- qp: Dict[str,Any], optional.

## Query parameters

| Name | Type | Default | Validation |
| -- | -- | -- | -- |
| limit | `integer` | 10 | Minimum 1, maximum 100. |
| offset | `integer` | 0 |  |
| file_name | `string` |  | Return only files with a matching name. |
| user | `string` |  | Email address of the uploader. Case-insensitive exact match. |
| approval_status | `string` |  | Enum: 'Undetermined', 'Approved', 'ApprovalRejected', 'ApprovalRevoked'. Case-insensitive. |
| deleted_in_days | `integer` |  |  |
| sort_by | `string` | '-upload_date' | Enum: 'file_name', '+file_name', '-file_name', 'upload_date', '+upload_date', '-upload_date' |

## Responses

Returns the 'requests.result' of the filestream_list() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

- [listFilestreamFiles](https://docs.secure.software/api-reference/#tag/File-Stream/operation/listFilestreamFiles)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def filestream_list_files(
    api_client: SpectraAssureApiOperations,
    limit: int = 10,
    offset: int = 0,
) -> Any:
    qp: dict[str, Any] = {
        "limit": limit,
        "offset": offset,
        "sort_by": "-upload_date",  # most recently uploaded first
    }

    response = api_client.filestream_list(
        **qp,
    )
    print("Filestream list:", response.status_code)
    # print(json.dumps(response.json(), indent=2))
    return response.json()
```

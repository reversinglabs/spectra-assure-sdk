# SpectraAssureApiOperationsListGroups

Execute a list_groups() API call.

> **Deprecated:** `listGroups()` is the old name of this call. It still works but emits a `DeprecationWarning`, and it will be removed in a future major release. Use `list_groups()` instead.

## Targets

- Organization

## Arguments

- auto_adapt_to_throttle: bool, default False, optional.

## Query parameters

None

## Responses

Returns the 'requests.result' of the list_groups() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

https://docs.secure.software/api-reference/#tag/Group/operation/listGroups

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)

```python
def list_groups(
    api_client: SpectraAssureApiOperations,
) -> Any:
    response = api_client.list_groups()
    data = response.json()
    print("list_groups: ", json.dumps(data, indent=2))
    return data
```

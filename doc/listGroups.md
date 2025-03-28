# SpectraAssureApiOperationsUsage

Execute a listGroups() API call.

## Targets

- Organization

## Arguments

- auto_adapt_to_throttle: bool, default False, optional.

## Query parameters

None

## Responses

Returns the 'requests.result' of the listGroups() API call.

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
    response = api_client.listGroups()
    data = response.json()
    print("listGroups: ", json.dumps(data, indent=2))
    return data
```

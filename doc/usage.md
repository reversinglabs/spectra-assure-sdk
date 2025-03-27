# SpectraAssureApiOperationsUsage

Execute a usage() API call.

## Targets

- Organization
- Group

## Arguments

- group, string | None, default None, optional.
- auto_adapt_to_throttle: bool, default False, optional.

## Query parameters

None

## Responses

Returns the 'requests.result' of the usage() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.get().

## Portal API documentation

https://docs.secure.software/api-reference/#tag/Group/operation/listOrganizationUsage
https://docs.secure.software/api-reference/#tag/Group/operation/listGroupUsage

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)

```python
def usage_organization(
    api_client: SpectraAssureApiOperations,
) -> Any:
    response = api_client.usage()
    data = response.json()
    print("ORG USAGE: ", json.dumps(data, indent=2))
    return data

def usage_group(
    api_client: SpectraAssureApiOperations,
    group: str,
) -> Any:
    response = api_client.usage(
        group=group,
    )
    data = response.json()
    print("GROUP USAGE: ", json.dumps(data, indent=2))
    return data
```

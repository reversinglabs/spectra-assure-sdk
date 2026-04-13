# SpectraAssureApiOperationsExportProfile

Export profile configuration for a Spectra Assure Portal organization or group.

## Targets

- Organization
- Group

## Arguments

- organization: str, mandatory.
- group: str, optional.
- auto_adapt_to_throttle: bool, default False, optional.
- qp: Dict[str,Any], optional.


## Query parameters

None

## Responses

Returns the 'requests.result' of the export_profile() API call.
If the call succeeds a json string will be returned.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.patch().

## Portal API documentation

- [Export organization profile](https://docs.secure.software/api-reference/#tag/Profile/operation/exportOrganizationRlProfile)
- [export group profile](https://docs.secure.software/api-reference/#tag/Profile/operation/exportGroupRlProfile)
- [the profile structure](https://docs.secure.software/cli/rl-profile-schema)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def export_profile(
    api_client: SpectraAssureApiOperations,
    organization: str,
    group: str | None = None,
) -> Any:
    qp: Any = None

    result = api_client.export_profile(
        organization=organization,
        group=group,
        qp=qp,
        auto_adapt_to_throttle=True,
    )

    if result.status_code == 200:
        data = json.dumps(json.loads(result.text))
        print(f"export_profile {organization} {group}\n {data}")
        f_name = f"export_profile.{organization}.{group}.json"
        with open(f_name, "wb") as f:
            f.write(bytes(data, "utf-8"))

    return result

```

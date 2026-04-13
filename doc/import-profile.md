# SpectraAssureApiOperationsImportProfile

Import a organization or a group profile.

## Targets

- Organization
- Group

## Arguments

- file_path: str, mandatory.
- replace: bool, default True.
- organization: str, mandatory.
- group: str, optional.
- auto_adapt_to_throttle: bool, default False, optional.

## Query parameters

None

## Responses

Returns the 'requests.result' of the import_profile() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.patch().

## Portal API documentation

- [Import organization profile](https://docs.secure.software/api-reference/#tag/Profile/operation/importOrganizationRlProfile)
- [Import group profile](https://docs.secure.software/api-reference/#tag/Profile/operation/importGroupRlProfile)
- [Profile configuration schema](https://docs.secure.software/cli/rl-profile-schema)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def import_profile(
    api_client: SpectraAssureApiOperations,
    *,
    file_path: str,
    organization: str,
    group: str | None = None,
    replace: bool = True,  # default is to replace the full profile
) -> Any:

    result = api_client.import_profile(
        file_path=file_path,
        organization=organization,
        group=group,
        replace=replace,
        auto_adapt_to_throttle=True,
    )

    print(f"import_profile, {file_path} {organization} {group} {replace} {result.status_code}")

    return None

```

# SpectraAssureApiOperationsCommunityUserAccount

Execute a community_user_account() API call to show information such as subscription details and token usage for the current user.

## Targets

Spectra Assure Community

## Arguments

- auto_adapt_to_throttle: bool, default False, optional.


## Query parameters

None

## Responses

Returns the 'requests.result' of the community_user_account() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.post().

## Portal API documentation

- [getUserAccountDetails](https://docs.secure.software/api-reference/#tag/Community/operation/getUserAccountDetails)

## Code example

From [examples/api_client_example.py](../examples/api_client_example.py)

```python
def community_user_account(
    api_client: SpectraAssureApiOperations,
):
    result = api_client.community_user_account(
        auto_adapt_to_throttle=True,
    )

    print(f"community_user_account: {result.status_code}")
    if result.status_code == 200:
        print(json.dumps(json.loads(result.text), indent=2))

    return None
```

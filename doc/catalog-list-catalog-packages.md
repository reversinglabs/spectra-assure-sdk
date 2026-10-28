# SpectraAssureApiOperationsCatalog.list_catalog_packages

Execute a list_catalog_packages() API call to list the packages published in the software catalog of the current group.

> **Note:**
> The group's *software catalog* is where packages are published,
> so that their latest approved version is offered to the organization.

## Targets

- Catalog

Each package comes with the external catalog it was imported from, if any (`external_catalog`).
Packages that are not published are not listed;
that includes imported packages that have no approved version yet.

## Arguments

- auto_adapt_to_throttle: bool | None, default None (inherit the client setting), optional.

## Responses

Returns the 'requests.result' of the list_catalog_packages() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.

## Portal API documentation

- [listCatalogPackages](https://docs.secure.software/api-reference/#tag/Catalog/operation/listCatalogPackages)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def catalog_list_catalog_packages(
    api_client: SpectraAssureApiOperations,
) -> Any:
    rr = api_client.list_catalog_packages()
    print("Catalog list_catalog_packages", rr.status_code, rr.text)
    return rr.json()
```

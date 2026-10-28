# SpectraAssureApiOperationsCatalog.detach_from_catalog

Execute a detach_from_catalog() API call to unlink a package from the external catalog it was imported from.

> **Note:**
> An *external catalog* lists software, with its streams and versions, that the Portal can import.
> A package imported from one stays linked to it, so newer versions can be imported later.

## Targets

- Catalog

The package and its versions are preserved, but are no longer updated from the external catalog.
The API responds with 400 when the package is not linked to an external catalog.

## Arguments

- project: str, mandatory.
- package: str, mandatory.
- auto_adapt_to_throttle: bool | None, default None (inherit the client setting), optional.

## Responses

Returns the 'requests.result' of the detach_from_catalog() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.

## Portal API documentation

- [detachFromCatalog](https://docs.secure.software/api-reference/#tag/Catalog/operation/detachFromCatalog)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def catalog_detach_from_catalog(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> Any:
    # the package and its versions are kept, but no longer updated from the catalog
    rr = api_client.detach_from_catalog(
        project=project,
        package=package,
    )
    print("Catalog detach_from_catalog", rr.status_code, rr.text)
    return rr
```

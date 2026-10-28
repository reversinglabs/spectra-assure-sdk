# SpectraAssureApiOperationsCatalog.unpublish_package_from_catalog

Execute an unpublish_package_from_catalog() API call to remove a package from the software catalog of the current group.

> **Note:**
> The group's *software catalog* is where packages are published,
> so that their latest approved version is offered to the organization.

## Targets

- Catalog

The package and its versions are preserved on the Portal, and the package can be published again at any time.
An imported package that is unpublished is not published again automatically.
Unpublishing a package that is not published has no effect.

## Arguments

- project: str, mandatory.
- package: str, mandatory.
- auto_adapt_to_throttle: bool | None, default None (inherit the client setting), optional.

## Responses

Returns the 'requests.result' of the unpublish_package_from_catalog() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.

## Portal API documentation

- [unpublishPackageFromCatalog](https://docs.secure.software/api-reference/#tag/Catalog/operation/unpublishPackageFromCatalog)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def catalog_unpublish_package_from_catalog(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> Any:
    rr = api_client.unpublish_package_from_catalog(
        project=project,
        package=package,
    )
    print("Catalog unpublish_package_from_catalog", rr.status_code, rr.text)
    return rr
```

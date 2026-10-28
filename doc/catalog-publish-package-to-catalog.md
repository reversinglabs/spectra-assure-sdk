# SpectraAssureApiOperationsCatalog.publish_package_to_catalog

Execute a publish_package_to_catalog() API call to add a package to the software catalog of the current group.

> **Note:**
> The group's *software catalog* is where packages are published,
> so that their latest approved version is offered to the organization.

## Targets

- Catalog

The package needs at least one approved version (the API answers 400 otherwise).
Imported packages are published automatically when their first version is approved.
Publishing a package that is already published has no effect.

## Arguments

- project: str, mandatory.
- package: str, mandatory.
- auto_adapt_to_throttle: bool | None, default None (inherit the client setting), optional.

## Responses

Returns the 'requests.result' of the publish_package_to_catalog() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.

## Portal API documentation

- [publishPackageToCatalog](https://docs.secure.software/api-reference/#tag/Catalog/operation/publishPackageToCatalog)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def catalog_publish_package_to_catalog(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> Any:
    # the package needs at least one approved version
    rr = api_client.publish_package_to_catalog(
        project=project,
        package=package,
    )
    print("Catalog publish_package_to_catalog", rr.status_code, rr.text)
    return rr
```

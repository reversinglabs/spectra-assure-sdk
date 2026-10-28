# SpectraAssureApiOperationsCatalog.update_from_catalog

Execute an update_from_catalog() API call to import versions from the external catalog a package is linked to.

> **Note:**
> An *external catalog* lists software, with its streams and versions, that the Portal can import.
> A package imported from one stays linked to it, so newer versions can be imported later.

## Targets

- Catalog

The package must already exist (created with `import_from_catalog()`).
If you don't specify `versions`, every version newer than the package's latest one is imported.
If automatic sync is enabled for the package, this call is refused and the API responds with 400.

The API responds with 201 when one or more versions are imported, and with 200 when there was nothing newer. Both responses contain `imported_versions`.
If a version is already in the package, the API responds with 409.

A package can have at most 16 versions. Importing more deletes the oldest version, approved ones included.

The body is optional: when no argument is given, no body is sent.

## Arguments

- project: str, mandatory.
- package: str, mandatory.
- versions: list[str] | None, default None, optional. Catalog versions to import; None imports every newer version.
- notify_on_completion: bool | None, default None, optional. Email you when all imported versions are analyzed.
- auto_adapt_to_throttle: bool | None, default None (inherit the client setting), optional.

## Body fields

| Name | Type | Default | Validation |
| -- | -- | -- | -- |
| versions | `array` of `string` |  | At most 16; duplicates are ignored |
| notify_on_completion | `boolean` | false |  |

## Responses

Returns the 'requests.result' of the update_from_catalog() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.

## Portal API documentation

- [updateFromCatalog](https://docs.secure.software/api-reference/#tag/Catalog/operation/updateFromCatalog)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def catalog_update_from_catalog(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    versions: list[str] | None = None,
) -> Any:
    rr = api_client.update_from_catalog(
        project=project,
        package=package,
        versions=versions,  # None: every version newer than the package's newest one
    )
    print("Catalog update_from_catalog", rr.status_code, rr.text)

    # 201: versions were imported; 200: there was nothing newer
    if rr.status_code not in [200, 201]:
        raise RuntimeError(f"expected 200 or 201, got {rr.status_code}: {rr.text[:300]}")

    return rr.json().get("imported_versions")
```

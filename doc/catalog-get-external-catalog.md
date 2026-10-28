# SpectraAssureApiOperationsCatalog.get_external_catalog

Execute a get_external_catalog() API call to read the contents of an external catalog.

> **Note:**
> An *external catalog* lists software, with its streams and versions, that the Portal can import.
> A package imported from one stays linked to it, so newer versions can be imported later.

## Targets

- Catalog

The response lists every software entry in the external catalog with its streams, versions and files,
and is the same for every group.
Use it to choose what to import: `import_from_catalog()` takes an entry's `id` as `software_id`
and the `id` of one of its streams as `stream`.

The response may contain more properties than the API documents.

## Arguments

- catalog: str, mandatory. The identifier of the external catalog. Currently, the only supported value is `reversinglabs`.
- auto_adapt_to_throttle: bool | None, default None (inherit the client setting), optional.

## Responses

Returns the 'requests.result' of the get_external_catalog() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.

## Portal API documentation

- [getExternalCatalog](https://docs.secure.software/api-reference/#tag/Catalog/operation/getExternalCatalog)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def catalog_get_external_catalog(
    api_client: SpectraAssureApiOperations,
    catalog: str = "reversinglabs",
) -> Any:
    rr = api_client.get_external_catalog(
        catalog=catalog,
    )
    print("Catalog get_external_catalog", rr.status_code)

    if rr.status_code != 200:
        raise RuntimeError(f"expected 200, got {rr.status_code}: {rr.text[:300]}")

    # every entry's `id` is a software_id; each of its `streams` has an `id` to import
    return rr.json()
```

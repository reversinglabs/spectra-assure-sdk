# SpectraAssureApiOperationsCatalog.import_from_catalog

Execute an import_from_catalog() API call to create a package from software in an external catalog and import versions into it.

> **Note:**
> An *external catalog* lists software, with its streams and versions, that the Portal can import.
> A package imported from one stays linked to it, so newer versions can be imported later.

## Targets

- Catalog

The project is created if it does not exist; the package must not exist yet (the API responds with 409).
A stream can be imported into a group once. Attempting a second import of the same stream returns the 400 error response.
Pick the software and one of its streams from `get_external_catalog()`.
The package stays linked to the catalog:
use `update_from_catalog()` for newer versions, or set `auto_sync` to have them imported automatically.

A package can have at most 16 versions; importing more deletes the oldest, approved ones included.
The versions are analyzed in the background (track the analysis progress with `status()`)
and count against the group's analysis capacity. The API responds with 402 when the analysis capacity is exceeded.

The body fields are named arguments. An optional argument left at `None` is not sent,
so the Portal's default applies. Lengths and counts are checked by the Portal, not by the SDK.
An empty `software_id` or `stream` raises `SpectraAssureInvalidAction` before anything is sent.

## Arguments

- catalog: str, mandatory. The identifier of the external catalog, currently `reversinglabs`.
- project: str, mandatory.
- package: str, mandatory.
- software_id: str, mandatory. The `id` of the software entry in the external catalog.
- stream: str, mandatory. The `id` of the stream to import, one of the entry's `streams`.
- versions: list[str] | None, default None, optional. Catalog versions to import; None imports the stream's newest versions.
- auto_sync: bool | None, default None, optional. Import new versions automatically after each Portal update.
- project_description: str | None, default None, optional. Description for the project when this call creates it.
- package_description: str | None, default None, optional. Brief description of the package.
- notify_on_completion: bool | None, default None, optional. Email you when all imported versions are analyzed.
- auto_adapt_to_throttle: bool | None, default None (inherit the client setting), optional.

## Body fields

| Name | Type | Default | Validation |
| -- | -- | -- | -- |
| software_id | `string` |  | Required |
| stream | `string` |  | Required |
| versions | `array` of `string` |  | At most 16; duplicates are ignored |
| auto_sync | `boolean` | false |  |
| project_description | `string` |  | <= 500 characters |
| package_description | `string` |  | <= 500 characters |
| notify_on_completion | `boolean` | false |  |

## Responses

Returns the 'requests.result' of the import_from_catalog() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.

## Portal API documentation

- [importFromCatalog](https://docs.secure.software/api-reference/#tag/Catalog/operation/importFromCatalog)

## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)


```python

def catalog_import_from_catalog(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    software_id: str,
    stream: str,
    catalog: str = "reversinglabs",
    versions: list[str] | None = None,
) -> Any:
    # the project is created if it does not exist; the package must not exist yet
    rr = api_client.import_from_catalog(
        catalog=catalog,
        project=project,
        package=package,
        software_id=software_id,
        stream=stream,
        versions=versions,  # None: the stream's newest versions
        auto_sync=False,
        package_description="imported from the catalog",
    )
    print("Catalog import_from_catalog", rr.status_code, rr.text)

    if rr.status_code != 201:
        raise RuntimeError(f"expected 201, got {rr.status_code}: {rr.text[:300]}")

    return rr.json().get("imported_versions")
```

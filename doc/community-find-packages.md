# SpectraAssureApiOperationsCommunityFindPackages

Execute a community_find_packages() API call to find software packages in Spectra Assure Community.

## Targets

Spectra Assure Community

## Arguments

- post_data: List[Dict[str,Any]], mandatory.
- auto_adapt_to_throttle: bool, default False, optional.
- qp: Dict[str,Any], optional.

THE POST DATA SECTION IS NOT VALIDATED CURRENTLY,
only that the top level element must be a list.
Validation is done by the API endpoint.

For valid query types, see the [Portal API documentation](https://docs.secure.software/api-reference/#tag/Community).

## Query parameters

| Name    | Type   | Default | Validation |
| --      | --     | --      | --         |
| offset  | `int`  | 0       | optional   |
| limit   | `int`  | 5       | optional   |
| compact | `bool` | False   | optional   |


## Responses

Returns the 'requests.result' of the community_find_packages() API call.

May raise exceptions on issues with the HTTP connection or wrong parameters:

- SpectraAssureInvalidAction: our exception.
- any other exception from requests.post().

## Portal API documentation

- [FindPackageMetadata](https://docs.secure.software/api-reference/#tag/Community/operation/postFindPackageMetadata)

## Code example

From [examples/api_client_example.py](../examples/api_client_example.py)

```python
def makeFindQueries():
    queries = {}

    # ==================================
    myUuid = str(uuid.uuid4())
    myPurl = "pkg:pypi/numpy@2.3.5"
    query: Dict[str, str] = {
        "uuid": myUuid,
        "purl": myPurl,
    }
    queries["FindByPurlOne"] = {
        "query": query,
        "qp": {},
    }

    # ==================================
    myUuid = str(uuid.uuid4())
    myPurl = "pkg:pypi/numpy"
    query: Dict[str, str] = {
        "uuid": myUuid,
        "purl": myPurl,
    }
    queries["FindByPurlMany"] = {
        "query": query,
        "qp": {
            "offset": 1,
            "limit": 1,
            "compact": False,
        },
    }

    # ==================================
    myUuid = str(uuid.uuid4())
    sha256Hash = "fffe29a1ef00883599d1dc2c51aa2e5d80afe49523c261a74933df395c15c520"
    query: Dict[str, str] = {
        "uuid": "1.2.3",
        "sha256": sha256Hash,
    }
    queries["FindBySha256"] = {
        "query": query,
        "qp": {},
    }

    return queries


def community_find_packages(
    api_client: SpectraAssureApiOperations,
):
    print("community_find_packages")

    for qName, query in makeFindQueries().items():

        post_data: List[Any] = [query["query"]]
        qp = query["qp"]

        print(f"qp: {qp}; post_data: {post_data}")

        result = api_client.community_find_packages(
            auto_adapt_to_throttle=True,
            post_data=post_data,
            **qp,
        )

        s = f"query: {qName} {query} gives:"
        print(s)

        if result.status_code == 200:
            print(json.dumps(json.loads(result.text), indent=2))

    return None
```

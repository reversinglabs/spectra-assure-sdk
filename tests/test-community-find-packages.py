#! /usr/bin/env python3

from typing import (
    Dict,
    List,
    Any,
)

import sys

# import os
import json
import uuid
import logging

from spectra_assure_api_client import (
    SpectraAssureApiOperations,
)

import startProg

logger = logging.getLogger()

"""
query types (all need uuid as a param)

- SearchByPurl
- SearchBySha1
- SearchBySha256
- MatchPurlByPattern
- MatchPurlByExpression
- MatchArtifacts
"""


def makeFindQueries():
    queries = {}

    # ==================================
    myUuid = str(uuid.uuid4())
    myPurl = "pkg:pypi/numpy@2.3.5"
    query: Dict[str, str] = {
        "uuid": myUuid,
        "purl": myPurl,
    }
    # queries["FindByPurlOne"] = { "query": query,        "qp": {},    }

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
    # queries["FindBySha256"] = {"query": query,"qp": {},}

    return queries


def testCommunityFind(
    aOperationsHandle: SpectraAssureApiOperations,
) -> bool:
    for qName, query in makeFindQueries().items():
        post_data: List[Any] = [query["query"]]
        qp = query["qp"]
        logger.debug(f"qp: {qp}; post_data: {post_data}")

        result = aOperationsHandle.community_find_packages(
            auto_adapt_to_throttle=True,
            post_data=post_data,
            **qp,
        )

        s = f"query: {qName} {query} gives: {result.text}"
        logger.debug(s)
        print(json.dumps(json.loads(result.text), indent=2))

    return True


def main() -> None:
    SpectraAssureApiOperations.make_logger(my_logger=logger)
    aOperationsHandle = startProg.startProg()

    r = testCommunityFind(aOperationsHandle)
    if r is False:
        sys.exit(1)
    sys.exit(0)


main()

#! /usr/bin/env python3

# import os
import json
import logging
import sys
import uuid
from typing import (
    Any,
)

import startProg

from spectra_assure_api_client import (
    SpectraAssureApiOperations,
)

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


def makeFindQueries() -> dict:
    queries: dict = {}

    # ==================================
    myuuid = str(uuid.uuid4())
    mypurl = "pkg:pypi/numpy@2.3.5"
    query: dict[str, str] = {
        "uuid": myuuid,
        "purl": mypurl,
    }
    # queries["FindByPurlOne"] = { "query": query,        "qp": {},    }

    # ==================================
    myuuid = str(uuid.uuid4())
    mypurl = "pkg:pypi/numpy"
    query: dict[str, str] = {
        "uuid": myuuid,
        "purl": mypurl,
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
    myuuid = str(uuid.uuid4())
    sha256hash = "fffe29a1ef00883599d1dc2c51aa2e5d80afe49523c261a74933df395c15c520"
    query: dict[str, str] = {
        "uuid": "1.2.3",
        "sha256": sha256hash,
    }
    # queries["FindBySha256"] = {"query": query,"qp": {},}

    return queries


def testCommunityFind(
    aOperationsHandle: SpectraAssureApiOperations,
) -> bool:
    for qname, query in makeFindQueries().items():
        post_data: list[Any] = [query["query"]]
        qp = query["qp"]
        logger.debug(f"qp: {qp}; post_data: {post_data}")

        result = aOperationsHandle.community_find_packages(
            auto_adapt_to_throttle=True,
            post_data=post_data,
            **qp,
        )

        s = f"query: {qname} {query} gives: {result.text}"
        logger.debug(s)
        print(json.dumps(json.loads(result.text), indent=2))

    return True


def main() -> None:
    SpectraAssureApiOperations.make_logger(my_logger=logger)
    aoh = startProg.startProg()

    r = testCommunityFind(aoh)
    if r is False:
        sys.exit(1)
    sys.exit(0)


main()

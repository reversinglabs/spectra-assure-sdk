"""The Spectra Assure Community calls: read-only, so they need no test data (was test-community-*).

They query a well-known open-source package, numpy from PyPI, as the old
scripts and the example program do.
"""

from __future__ import annotations

import uuid

from conftest import expect

from spectra_assure_api_client import SpectraAssureApiOperations

REPOSITORY = "pypi"
PACKAGE = "numpy"
VERSION = "2.3.5"


def test_packages_can_be_found_by_purl(client: SpectraAssureApiOperations) -> None:
    query = {"uuid": str(uuid.uuid4()), "purl": f"pkg:{REPOSITORY}/{PACKAGE}"}

    response = expect(client.community_find_packages(post_data=[query], offset=1, limit=1, compact=False), 200)

    assert "community" in response.json()


def test_a_package_report_can_be_read(client: SpectraAssureApiOperations) -> None:
    response = expect(client.community_report_package(repository=REPOSITORY, package=PACKAGE), 200)

    assert "community" in response.json()


def test_a_version_report_can_be_read(client: SpectraAssureApiOperations) -> None:
    response = expect(client.community_report_version(repository=REPOSITORY, package=PACKAGE, version=VERSION), 200)

    assert "community" in response.json()


def test_the_user_account_can_be_read(client: SpectraAssureApiOperations) -> None:
    response = expect(client.community_user_account(), 200)

    assert "account" in response.json()

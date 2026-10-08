"""The organization's groups and a group's projects (was part of t1, and test-list-all)."""

from __future__ import annotations

import os
from typing import Any

import pytest
from conftest import expect

from spectra_assure_api_client import SpectraAssureApiOperations


def test_the_configured_group_is_one_of_the_organizations_groups(
    client: SpectraAssureApiOperations, settings: dict[str, Any]
) -> None:
    groups = expect(client.list_groups(), 200).json()["groups"]

    assert settings["group"] in [group["name"] for group in groups]


def test_the_group_lists_its_projects(client: SpectraAssureApiOperations) -> None:
    body = expect(client.list(), 200).json()

    assert isinstance(body["projects"], list)


@pytest.mark.skipif(
    os.environ.get("RLPORTAL_SLOW") != "1", reason="walks the whole group; set RLPORTAL_SLOW=1 to run it"
)
def test_every_project_package_and_version_of_the_group_can_be_listed(client: SpectraAssureApiOperations) -> None:
    """A very long test, not normally needed (was test-list-all)."""
    for project in expect(client.list(), 200).json()["projects"]:
        packages = expect(client.list(project=project["name"]), 200).json()["packages"]
        for package in packages:
            versions = expect(client.list(project=project["name"], package=package["name"]), 200).json()["versions"]
            for version in versions:
                expect(
                    client.list(project=project["name"], package=package["name"], version=version["version"]),
                    200,
                )

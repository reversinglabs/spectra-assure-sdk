"""A package's life inside a project: create, list, edit, delete (was test-package-steps)."""

from __future__ import annotations

from conftest import Created, expect

from spectra_assure_api_client import SpectraAssureApiOperations


def package_names(client: SpectraAssureApiOperations, project: str) -> list[str]:
    return [package["name"] for package in expect(client.list(project=project), 200).json()["packages"]]


def test_a_package_can_be_created_listed_edited_and_deleted(
    client: SpectraAssureApiOperations, created: Created
) -> None:
    project = created.project("packages")
    package = created.package(project, "package", description="an SDK test package")

    assert expect(client.list(project=project, package=package), 200).json()["description"] == "an SDK test package"
    assert package in package_names(client, project)

    expect(client.edit(project=project, package=package, description="edited by the SDK test"))
    assert expect(client.list(project=project, package=package), 200).json()["description"] == "edited by the SDK test"

    expect(client.delete(project=project, package=package), 204)
    assert package not in package_names(client, project)

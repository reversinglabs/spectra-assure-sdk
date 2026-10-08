"""A project's life: create, list, edit, delete (was test-project-steps)."""

from __future__ import annotations

from conftest import Created, expect

from spectra_assure_api_client import SpectraAssureApiOperations


def project_names(client: SpectraAssureApiOperations) -> list[str]:
    return [project["name"] for project in expect(client.list(), 200).json()["projects"]]


def test_a_project_can_be_created_listed_edited_and_deleted(
    client: SpectraAssureApiOperations, created: Created
) -> None:
    project = created.project("project", description="an SDK test project")

    assert expect(client.list(project=project), 200).json()["description"] == "an SDK test project"
    assert project in project_names(client)

    expect(client.edit(project=project, description="edited by the SDK test"))
    assert expect(client.list(project=project), 200).json()["description"] == "edited by the SDK test"

    expect(client.delete(project=project), 204)
    assert project not in project_names(client)

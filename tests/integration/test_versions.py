"""A scanned version: list, edit, checks, reports, RL-SAFE, the approval states, download, rescan, delete.

Was test-version-steps and test-download. The tests share one version, scanned
once for the module, and run in file order. One scan serves all of it, which
spares analysis capacity.

The approval steps follow the Portal's rules (the approve, reject and revoke
operations in the API specification): a new version is pending approval; only
a pending version can be rejected; a rejected one can still be approved; only
an approved one can be revoked, and revoked is final. So the version is
rejected, then approved, downloaded, and the approval revoked last.
Downloading needs an approved version; the old download test needed one
approved by hand in the Portal.
"""

from __future__ import annotations

import datetime
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from conftest import Created, expect, until_ready, wait_for_analysis

from spectra_assure_api_client import SpectraAssureApiOperations

# The version report types the Portal API documents. rl-diff compares a version
# with an earlier one; what it returns for a package's first version is not
# documented, so it is left out until that is known.
REPORT_TYPES = ["cyclonedx", "rl-checks", "rl-cve", "rl-json", "rl-summary-pdf", "rl-uri", "sarif", "spdx"]

# The metadata the old version test sent with the scan and with the edit.
SCAN_METADATA: dict[str, Any] = {
    "publisher": "ReversingLabs Testing",
    "product": "a reversingLabs test",
    "category": "Development",
    "license": "Do What The F*ck You Want To Public License",
    "platform": "Containers",
    "release_date": f"{datetime.datetime.now()}",
    "build": "version",
}
EDIT_METADATA: dict[str, Any] = {
    "publisher": "ReversingLabs Testing 2",
    "product": "a reversingLabs test 2",
    "category": "Administration",
    "license": "iMatix Standard Function Library Agreement",
    "platform": "Linux",
    "release_date": "2023-12-30T00:00:00Z",
    "is_released": True,
}


@dataclass(frozen=True)
class Version:
    project: str
    package: str
    version: str

    def coordinates(self) -> dict[str, Any]:
        return {"project": self.project, "package": self.package, "version": self.version}


@pytest.fixture(scope="module")
def scanned(client: SpectraAssureApiOperations, created: Created, artifact: Path, run_id: str) -> Version:
    project = created.project("versions")
    package = created.package(project, "package")
    found = Version(project, package, f"{run_id}-v1")

    expect(client.scan(**found.coordinates(), file_path=str(artifact), **SCAN_METADATA), 201)
    wait_for_analysis(client, **found.coordinates())
    return found


def version_names(client: SpectraAssureApiOperations, version: Version) -> list[str]:
    body = expect(client.list(project=version.project, package=version.package), 200).json()
    return [entry["version"] for entry in body["versions"]]


def test_the_scanned_version_is_listed(client: SpectraAssureApiOperations, scanned: Version) -> None:
    assert scanned.version in version_names(client, scanned)
    expect(client.list(**scanned.coordinates()), 200)


def test_the_version_can_be_edited(client: SpectraAssureApiOperations, scanned: Version) -> None:
    expect(client.edit(**scanned.coordinates(), **EDIT_METADATA))


def test_the_checks_are_available(client: SpectraAssureApiOperations, scanned: Version) -> None:
    expect(until_ready(lambda: client.checks(**scanned.coordinates()), "checks"), 200)


@pytest.mark.parametrize("report_type", REPORT_TYPES)
def test_each_report_can_be_downloaded(client: SpectraAssureApiOperations, scanned: Version, report_type: str) -> None:
    response = until_ready(
        lambda: client.report(**scanned.coordinates(), report_type=report_type), f"report {report_type}"
    )

    expect(response, 200)
    assert response.content


def test_the_rl_safe_archive_can_be_downloaded(
    client: SpectraAssureApiOperations, scanned: Version, results_dir: Path
) -> None:
    expect(until_ready(lambda: client.rl_safe(**scanned.coordinates()), "rl-safe"), 200)

    downloaded, path = client.rl_safe_download(target_dir=str(results_dir), **scanned.coordinates())

    assert downloaded, path
    assert Path(path).stat().st_size > 0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_an_unapproved_version_is_not_downloaded(
    client: SpectraAssureApiOperations, scanned: Version, results_dir: Path
) -> None:
    """download() only takes approved versions by default; it returns None and requests no link."""
    target = results_dir / "download-unapproved"
    target.mkdir(exist_ok=True)

    assert client.download(target_dir=str(target), **scanned.coordinates()) is None


def test_the_version_can_be_rejected(client: SpectraAssureApiOperations, scanned: Version) -> None:
    """Only a version still pending approval can be rejected, so this comes before the approval."""
    expect(client.reject(**scanned.coordinates(), reason="rejected by the SDK integration tests"), 200)


def test_the_version_can_be_approved(client: SpectraAssureApiOperations, scanned: Version) -> None:
    """A rejected version can still be approved."""
    expect(client.approve(**scanned.coordinates(), reason="approved by the SDK integration tests"), 200)


def test_the_approved_version_is_downloaded_unchanged(
    client: SpectraAssureApiOperations, scanned: Version, results_dir: Path, artifact: Path
) -> None:
    """The SDK checks the file against the analysis's hashes; this checks it against what was uploaded."""
    target = results_dir / "download"
    target.mkdir(exist_ok=True)

    result = client.download(target_dir=str(target), **scanned.coordinates())

    assert result is not None, "the approved version was not selected for download"
    entry = result[scanned.version]
    assert entry["downloaded"] is True
    downloaded = Path(entry["target_file_path"])
    assert sha256(downloaded) == sha256(artifact)


def test_the_approval_can_be_revoked(client: SpectraAssureApiOperations, scanned: Version) -> None:
    """Revoked is final: the version can no longer be approved or rejected, so this comes last."""
    expect(client.revoke(**scanned.coordinates(), reason="revoked by the SDK integration tests"), 200)


def test_the_version_can_be_rescanned(client: SpectraAssureApiOperations, scanned: Version) -> None:
    expect(client.sync(**scanned.coordinates()), 200, 202)


def test_the_version_can_be_deleted(client: SpectraAssureApiOperations, scanned: Version) -> None:
    expect(client.delete(**scanned.coordinates()), 204)

    assert scanned.version not in version_names(client, scanned)

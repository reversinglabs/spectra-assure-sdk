"""Community URLs: values are percent-encoded so they cannot change the shape of the URL.

The community paths are assembled by hand, because the SDK accepts a package with
its namespace folded in and treats the version as optional. Unlike every other
path they were assembled from the raw values.
"""

from __future__ import annotations

import pytest

from spectra_assure_api_client import SpectraAssureApiOperations

from .support import Recorder, install, make_client


@pytest.fixture
def client() -> SpectraAssureApiOperations:
    return make_client()


def report_url(client: SpectraAssureApiOperations, *, repository: str, package: str, version: str | None) -> str:
    return client._make_current_url_community(  # noqa: SLF001  the URL builder is the unit under test
        action="community_report_version",
        repository=repository,
        package=package,
        version=version,
    )


def tail(client: SpectraAssureApiOperations, url: str) -> str:
    prefix = f"{client.base_url}/community/report/version/"
    assert url.startswith(prefix)
    return url[len(prefix) :]


# ------------------------------------------------------- unchanged: what has always worked


@pytest.mark.parametrize(
    ("package", "version", "expected"),
    [
        ("pkg", "1.0", "pkg:npm/pkg@1.0"),
        ("pkg", None, "pkg:npm/pkg"),
        ("ns/pkg", "1.0", "pkg:npm/ns/pkg@1.0"),  # namespace folded in: the '/' is a separator
        ("a/b/c", "1.0", "pkg:npm/a/b/c@1.0"),
        ("@scope/pkg", "1.0", "pkg:npm/@scope/pkg@1.0"),  # an npm scope has always been sent as it is
        ("my-pkg_2.x", "1.0.0-rc.1", "pkg:npm/my-pkg_2.x@1.0.0-rc.1"),
    ],
)
def test_ordinary_values_produce_the_same_url_as_before(
    client: SpectraAssureApiOperations, package: str, version: str | None, expected: str
) -> None:
    assert tail(client, report_url(client, repository="npm", package=package, version=version)) == expected


# ------------------------------------------------------- changed: what used to break the URL


@pytest.mark.parametrize(
    ("version", "encoded"),
    [
        ("1.0?x=1#y", "1.0%3Fx%3D1%23y"),
        ("1.0 beta", "1.0%20beta"),
        ("1.0+build.5", "1.0%2Bbuild.5"),
        ("1.0@2", "1.0%402"),
        ("100%", "100%25"),
    ],
)
def test_a_version_cannot_start_a_query_string_or_a_fragment(
    client: SpectraAssureApiOperations, version: str, encoded: str
) -> None:
    url = report_url(client, repository="npm", package="pkg", version=version)

    assert tail(client, url) == f"pkg:npm/pkg@{encoded}"
    assert "?" not in url
    assert "#" not in url


@pytest.mark.parametrize(
    ("package", "encoded"),
    [
        ("my pkg", "my%20pkg"),
        ("ns/my pkg", "ns/my%20pkg"),  # the separator survives, the space does not
        ("pkg?x", "pkg%3Fx"),
        ("pkg#x", "pkg%23x"),
        ("100%", "100%25"),
    ],
)
def test_a_package_cannot_change_the_shape_of_the_url(
    client: SpectraAssureApiOperations, package: str, encoded: str
) -> None:
    url = report_url(client, repository="npm", package=package, version="1.0")

    assert tail(client, url) == f"pkg:npm/{encoded}@1.0"
    assert "?" not in url
    assert "#" not in url


def test_a_repository_is_encoded_too(client: SpectraAssureApiOperations) -> None:
    url = report_url(client, repository="np m/x", package="pkg", version="1.0")

    assert tail(client, url) == "pkg:np%20m%2Fx/pkg@1.0"


def test_the_package_report_is_built_the_same_way(client: SpectraAssureApiOperations) -> None:
    url = client._make_current_url_community(  # noqa: SLF001
        action="community_report_package", repository="npm", package="ns/p q", version="1.0?"
    )

    assert url == f"{client.base_url}/community/report/package/pkg:npm/ns/p%20q@1.0%3F"


def test_no_repository_still_gives_the_bare_prefix(client: SpectraAssureApiOperations) -> None:
    assert client._make_current_url_community(action="community_find_packages") == (  # noqa: SLF001
        f"{client.base_url}/community/find/packages"
    )


# ------------------------------------------------------- through the public call


def test_a_hostile_version_reaches_the_wire_as_a_path_not_a_query(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations
) -> None:
    recorder = install(monkeypatch, "get", Recorder())

    client.community_report_version(repository="npm", package="pkg", namespace="ns", version="1.0?x=1#y")

    call = recorder.calls[0]
    assert call["url"].endswith("/community/report/version/pkg:npm/ns/pkg@1.0%3Fx%3D1%23y")
    assert call["params"] == {}  # nothing smuggled into the query string

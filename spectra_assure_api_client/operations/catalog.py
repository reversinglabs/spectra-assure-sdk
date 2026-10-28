"""Catalog operations.

Two kinds of catalog meet here. An external catalog is a list of software, with
its streams and versions, that the Portal reads from outside; a package can be
imported from one and stays linked to it, so newer versions can be imported
later. The group's software catalog is where packages are published, so that
their latest approved version is offered to the organization.

Like File Stream, everything here is kept apart from the purl-based calls:
the paths sit under `/catalog/...` and are not on the
group/project/package/version ladder. The method names are the operation ids of
the specification in snake case.

The request bodies are built from named arguments. An optional argument left at
None is not sent, so the Portal's default applies. Lengths and counts (500
characters for a description, 16 versions) are left to the Portal to check, as
everywhere else in the SDK.
"""

from __future__ import annotations

import logging
from typing import (
    Any,
)

import requests

from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)

WHAT = "catalog"


class SpectraAssureApiOperationsCatalog(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):
    """The Catalog half of the public surface."""

    # ------------------------------------------------------------- helpers

    def _catalog_url(
        self,
        action: str,
        *,
        catalog: str | None = None,
        project: str | None = None,
        package: str | None = None,
    ) -> str:
        # The specification spells the path values `{project}` and `{package}`,
        # like the arguments; `_url_for` adds the organization and the group.
        operation = self._resolve(action, WHAT)
        values: dict[str, str] = {}
        if catalog is not None:
            values["catalog"] = catalog
        if project is not None:
            values["project"] = project
        if package is not None:
            values["package"] = package
        return self._url_for(operation, **values)

    @staticmethod
    def _catalog_body(**fields: Any) -> dict[str, Any]:
        """The JSON body: every field that was given. False and [] are given; None is not."""
        return {name: value for name, value in fields.items() if value is not None}

    # ------------------------------------------------------------ querying

    def get_external_catalog(
        self,
        *,
        catalog: str,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        """The document of an external catalog: its software, their streams and versions.

        The document is the same for every group. An entry's `id` and the `id` of
        one of its streams are what `import_from_catalog` takes.
        """
        return self._do_it_get(
            url=self._catalog_url("get_external_catalog", catalog=catalog),
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

    def list_catalog_packages(
        self,
        *,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        """The packages published in the group's software catalog."""
        return self._do_it_get(
            url=self._catalog_url("list_catalog_packages"),
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

    # ------------------------------------------------------------- importing

    def import_from_catalog(  # pylint: disable=too-many-arguments
        self,
        *,
        catalog: str,
        project: str,
        package: str,
        software_id: str,
        stream: str,
        versions: list[str] | None = None,
        auto_sync: bool | None = None,
        project_description: str | None = None,
        package_description: str | None = None,
        notify_on_completion: bool | None = None,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        """Create a package from software in an external catalog and import versions into it.

        The project is created if it does not exist. The package stays linked to
        the catalog; see `update_from_catalog`.
        """
        action = "import_from_catalog"

        for name, value in (("software_id", software_id), ("stream", stream)):
            if not value:
                # Both are required by the specification; refused before anything is sent.
                msg = f"'{action}' requires a non-empty '{name}'"
                raise SpectraAssureInvalidAction(message=msg)

        return self._post(
            action=action,
            url=self._catalog_url(action, catalog=catalog, project=project, package=package),
            body="json",
            post_data=self._catalog_body(
                software_id=software_id,
                stream=stream,
                versions=versions,
                auto_sync=auto_sync,
                project_description=project_description,
                package_description=package_description,
                notify_on_completion=notify_on_completion,
            ),
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

    def update_from_catalog(
        self,
        *,
        project: str,
        package: str,
        versions: list[str] | None = None,
        notify_on_completion: bool | None = None,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        """Import versions from the external catalog a package is linked to.

        Without `versions`, every version newer than the package's newest one is
        imported. The API answers 201 when versions were imported and 200 when
        there was nothing newer.
        """
        action = "update_from_catalog"

        # The specification makes the body optional: none is sent when there is
        # nothing to say, as `_body_kind` does for the other calls.
        body = self._catalog_body(versions=versions, notify_on_completion=notify_on_completion)

        return self._post(
            action=action,
            url=self._catalog_url(action, project=project, package=package),
            body="json" if body else "none",
            post_data=body or None,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

    # ------------------------------------------------------------ publishing

    def publish_package_to_catalog(
        self,
        *,
        project: str,
        package: str,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        """Add a package to the group's software catalog.

        The package needs at least one approved version. Publishing a package that
        is already published has no effect.
        """
        return self._do_it_put(
            url=self._catalog_url("publish_package_to_catalog", project=project, package=package),
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

    def unpublish_package_from_catalog(
        self,
        *,
        project: str,
        package: str,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        """Remove a package from the group's software catalog. The package itself is kept."""
        return self._do_it_delete(
            url=self._catalog_url("unpublish_package_from_catalog", project=project, package=package),
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

    def detach_from_catalog(
        self,
        *,
        project: str,
        package: str,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        """Unlink a package from the external catalog it was imported from.

        The package and its versions are kept, but are no longer updated from the catalog.
        """
        return self._do_it_delete(
            url=self._catalog_url("detach_from_catalog", project=project, package=package),
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

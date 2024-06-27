from typing import (
    Any,
    Dict,
    List,
)

import logging

from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsEdit(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes

    @staticmethod
    def qp_edit(
        *,
        what: str,
        **qp: Any,
    ) -> Dict[str, Any]:

        r: Dict[str, Any] = {}
        if what in ["project", "package"]:
            for k in ["name", "description"]:
                if k in qp:
                    r[k] = qp[k]
            return r

        if what in ["version"]:
            version_qp: List[str] = [
                "is_released",
                "product",
                "publisher",
                "category",
                "license",
                "platform",
                "release_date",
            ]
            for k in version_qp:
                if k in qp:
                    r[k] = qp[k]
            return r

        return r

    def edit(
        self,
        *,
        project: str,
        package: str | None = None,
        version: str | None = None,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Any:
        """
        Action:
            Execute an edit() API call
            to modify the details for the specified item.

        Args:
         - project: str, mandatory.
         - package: str | None, optional.
         - version: str | None, optional.
         - auto_adapt_to_throttle: bool, default False, optional.
         - qp: Dict[str,Any] , optional.

        Return:
            The 'requests.result' of the edit API call.

        Raises:
            May raise exceptions on issues with the HTTP connection or wrong parameters.
            - SpectraAssureInvalidAction: our exception.
            - <any other exception> from requests.patch().

        QueryParameters:
            'project' and 'package' support:
             - name.
             - description.

            'version' supports:
              - is_released.
              - product.
              - publisher.
              - category.
              - license.
              - platform.
              - release_date.

        Notes:
            Warning:
                Renaming your project
                will also change the report URL for all versions inside it.
                If you shared the old link, it will no longer work after the rename.
        """

        action = "edit"
        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        supported = [
            "project",
            "package",
            "version",
        ]
        if what not in supported:
            msg = f"'edit' is only supported for {'and '.join(supported)}"
            raise SpectraAssureInvalidAction(message=msg)

        valid_qp: Dict[str, Any] = self.qp_edit(what=what, **qp)

        url = self._make_current_url(action=action, project=project, package=package, version=version)
        return self.do_it_patch(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **valid_qp,
        )

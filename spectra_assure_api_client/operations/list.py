from typing import (
    Any,
)

import logging

from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)

from .base import SpectraAssureApiOperationsBase


logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsList(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def list(
        self,
        *,
        project: str | None = None,
        package: str | None = None,
        version: str | None = None,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,  # not actually used in list
    ) -> Any:
        """
        Action:
            Execute a list() API call.

        Args:
         - project: str | None, optional.
         - package: str | None, optional.
         - version: str | None, optional.
         - auto_adapt_to_throttle: bool, default False, optional.
         - qp: Dict[str,Any] , optional.

        Return:
            The 'requests.result' of the list API call.

        Raises:
            May raise exceptions on issues with the HTTP connection or wrong parameters.
            - SpectraAssureInvalidAction: our exception.
            - <any other exception> from requests.get().

        QueryParameters:
            'list' has no query parameters.

        Notes:
            When 'project' is not specified, we list all projects in the current group.
            When 'package' is not specified, we list all packages in the current project.
            When 'version' is not specified, we list all versions in the current package.
            When a 'version' is specified, we list the details of this version.
        """

        action = "list"
        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        supported = [
            "group",
            "project",
            "package",
            "version",
        ]
        if what not in supported:
            msg = f"'list' is only supported for {'and '.join(supported)}"
            raise SpectraAssureInvalidAction(message=msg)

        url = self._make_current_url(action=action, project=project, package=package, version=version)

        qp = {}
        return self.do_it_get(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

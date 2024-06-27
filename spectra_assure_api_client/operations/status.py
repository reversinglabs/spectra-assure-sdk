from typing import (
    Any,
    Dict,
)


import logging


from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)

from .base import SpectraAssureApiOperationsBase


logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsStatus(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes

    def status(
        self,
        *,
        project: str,
        package: str,
        version: str,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Any:
        """
        Action:
            Execute a status() API call
            for the specified 'project/package@version'.

        Args:
         - project: str, mandatory.
         - package: str, mandatory.
         - version: str, mandatory.
         - auto_adapt_to_throttle: bool, default False, optional.
         - qp: Dict[str,Any] , optional.

        Return:
            The 'requests.result' of the status API call.

        Raises:
            May raise exceptions on issues with the HTTP connection or wrong parameters.
            - SpectraAssureInvalidAction: our exception.
            - <any other exception> from requests.get().

        QueryParameters:
            status supports the following query parameters:
             - build
             - download

        Notes:
            Using the download query parameter has direct influence on your Spectra Assure Portal download capacity.
        """

        action = "status"
        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        supported = ["version"]
        if what not in supported:
            msg = f"'status' is only supported for {'and '.join(supported)}"
            raise SpectraAssureInvalidAction(message=msg)

        valid_qp: Dict[str, Any] = self.qp_status(
            what=what,
            **qp,
        )  # see spectraAssureApiOperationsBase

        url = self._make_current_url(action=action, project=project, package=package, version=version)

        return self.do_it_get(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **valid_qp,
        )

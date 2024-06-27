import logging
from typing import (
    Any,
)

from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)
from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsChecks(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes

    def checks(
        self,
        *,
        project: str,
        package: str,
        version: str,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,  # not actually used in checks
    ) -> Any:
        """
        Action:
            Execute a checks() API call
            for the specified 'project/package@version'.

        Args:
         - project: str, mandatory.
         - package: str, mandatory.
         - version: str, mandatory.
         - auto_adapt_to_throttle: bool, default False, optional.
         - qp: Dict[str,Any] , optional.

        Return:
            The 'requests.result' of the checks API call.

        Raises:
            May raise exceptions on issues with the HTTP connection or wrong parameters.
            - SpectraAssureInvalidAction: our exception.
            - <any other exception> from requests.get().

        QueryParameters:
            'checks' does not use any query parameters.

        """

        action = "checks"
        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        supported = [
            "version",
        ]
        if what not in supported:
            msg = f"'checks' is only supported for {'and '.join(supported)}"
            raise SpectraAssureInvalidAction(message=msg)

        url = self._make_current_url(action=action, project=project, package=package, version=version)

        return self.do_it_get(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

# https://{portalUrl}/api/public/v1/reject/{organization}/{group}/pkg:rl/{project}/{package}@{version}
# qp:: reason: str
# Set the approval status for the requested package version to 'Rejected'.
# The request will be successful only if the package version currently has the Requires Approval status.
# 'Revoked' package versions cannot have their status changed to 'Rejected'.
# note: mostlikely 'Accepted' packages also cannot change to 'Rejected'.

import logging
from typing import (
    Any,
)

from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsReject(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    @staticmethod
    def qp_reject(
        *,
        what: str,
        **qp: Any,
    ) -> dict[str, Any]:
        r: dict[str, Any] = {}

        version_qp: list[str] = [
            "reason",
        ]

        if what in ["version"]:
            for k in version_qp:
                if k in qp:
                    r[k] = qp[k]

        return r

    def reject(
        self,
        *,
        project: str,
        package: str,
        version: str,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Any:
        """Action:
            Execute a reject() API call.

        Args:
         - project: str, mandatory.
         - package: str, mandatory.
         - version: str, mandatory.
         - auto_adapt_to_throttle: bool, default False, optional.
         - qp: Dict[str,Any] , optional.

        Return:
            The 'requests.result' of the reject API call.

        Raises:
            May raise exceptions on issues with the HTTP connection or wrong parameters.
            - SpectraAssureInvalidAction: our exception.
            - <any other exception> from requests.get().

        QueryParameters:
            scan supports the following query parameters:
             - reason: str

        """
        action = "reject"
        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        supported = [
            "version",
        ]
        if what not in supported:
            msg = f"'reject' is only supported for {'and '.join(supported)}"
            raise SpectraAssureInvalidAction(message=msg)

        url = self._make_current_url(
            action=action,
            project=project,
            package=package,
            version=version,
        )

        valid_qp: dict[str, Any] = self.qp_reject(
            what=what,
            **qp,
        )
        return self.do_it_put(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **valid_qp,
        )

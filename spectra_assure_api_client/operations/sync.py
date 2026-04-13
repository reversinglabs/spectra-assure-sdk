# https://{portalUrl}/api/public/v1/sync/{organization}/{group}/pkg:rl/{project}/{package}@{version}
# no qp

import logging
from typing import (
    Any,
)

from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsSync(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def sync(
        self,
        *,
        project: str,
        package: str,
        version: str,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,  # not actually used in sync
    ) -> Any:
        """Action:
            Execute a sync() API call.

        Args:
         - project: str, mandatory.
         - package: str, mandatory.
         - version: str, mandatory.
         - auto_adapt_to_throttle: bool, default False, optional.
         - qp: Dict[str,Any] , optional.

        Return:
            The 'requests.result' of the sync API call.

        Raises:
            May raise exceptions on issues with the HTTP connection or wrong parameters.
            - SpectraAssureInvalidAction: our exception.
            - <any other exception> from requests.get().

        QueryParameters:
            'sync' has no query parameters.

        """
        action = "sync"
        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        supported = [
            "version",
        ]
        if what not in supported:
            msg = f"'sync' is only supported for {'and '.join(supported)}"
            raise SpectraAssureInvalidAction(message=msg)

        url = self._make_current_url(
            action=action,
            project=project,
            package=package,
            version=version,
        )

        qp = {}
        return self.do_it_post(
            action=action,
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

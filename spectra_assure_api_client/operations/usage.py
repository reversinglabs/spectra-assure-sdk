# base_url: https://{portalUrl}/api/public/v1/
# "<self.base_url>/usage/<ORGANIZATION_NAME>"
# "<self.base_url>/usage/<ORGANIZATION_NAME>/<GROUP_NAME>"


from typing import (
    Any,
)

import logging

from .base import SpectraAssureApiOperationsBase


logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsUsage(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def usage(
        self,
        *,
        group: str | None = None,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Any:
        """
        Action:
            Execute a usage() api call

        Args:
         - group: str, optional
         - auto_adapt_to_throttle: bool, default False, optional.
         - qp: Dict[str,Any] , optional.

        Return:
            The 'requests.result' of the usage API call.

        Raises:
            May raise exceptions on issues with the HTTP connection or wrong parameters.
            - SpectraAssureInvalidAction: our exception.
            - <any other exception> from requests.get().

        QueryParameters:
            'usage' has no query parameters.

        Notes:
            When 'group' is not specified, we list usage of the organization
        """

        url = f"{self.base_url}/usage/{self.organization}"
        if group is not None:
            url = f"{url}/{group}"

        qp = {}
        return self.do_it_get(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

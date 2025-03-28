# base_url: https://{portalUrl}/api/public/v1/
# "<self.base_url>/usage/<ORGANIZATION_NAME>"
# "<self.base_url>/usage/<ORGANIZATION_NAME>/<GROUP_NAME>"


from typing import (
    Any,
)

import logging

from .base import SpectraAssureApiOperationsBase


logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsListGroups(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def listGroups(
        self,
        *,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Any:
        """
        Action:
            Execute a list() api call, with not group only organization

        Args:
         - auto_adapt_to_throttle: bool, default False, optional.
         - qp: Dict[str,Any] , optional.

        Return:
            The 'requests.result' of the list API call.

        Raises:
            May raise exceptions on issues with the HTTP connection or wrong parameters.
            - SpectraAssureInvalidAction: our exception.
            - <any other exception> from requests.get().

        QueryParameters:
            'listGroups' has no query parameters.

        Notes:
            We list groups in the organization that the authenticated user has access to
        """

        url = f"{self.base_url}/list/{self.organization}"
        qp = {}
        return self.do_it_get(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

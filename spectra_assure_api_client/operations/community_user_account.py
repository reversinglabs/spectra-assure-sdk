# get no params only
"""
https://{portalUrl}/{community-api}/user/account
2026-04-28 Added /community/user/account to public API.
"""

import logging
from typing import (
    Any,
)

# from spectra_assure_api_client.communication.exceptions import SpectraAssureInvalidAction
from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsCommunityUserAccount(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def community_user_account(
        self,
        *,  # force name based params
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Any:
        action = "community_user_account"

        url = self._make_current_url_community(
            action=action,
        )

        logger.debug("url is now: %s", url)

        return self.do_it_get(
            action=action,
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

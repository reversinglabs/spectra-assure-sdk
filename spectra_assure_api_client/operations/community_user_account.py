import logging
from typing import (
    Any,
)

import requests

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsCommunityUserAccount(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def community_user_account(
        self,
        *,  # force name based params
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,
    ) -> requests.Response:
        action = "community_user_account"

        url = self._make_current_url_community(
            action=action,
        )

        logger.debug("url is now: %s", url)

        return self._do_it_get(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

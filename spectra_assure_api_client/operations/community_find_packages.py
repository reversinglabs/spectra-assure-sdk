import logging
from typing import (
    Any,
)

import requests

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsCommunityFindPackages(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    @staticmethod
    def _qp_comm_find_packages(
        **qp: Any,
    ) -> dict[str, Any]:
        # The query parameters come from the specification, not from a list kept here.
        return SpectraAssureApiOperationsBase._accepted_query("community_find_packages", "community", qp)

    def community_find_packages(
        self,
        *,
        post_data: list[Any],  # MUST BE IN LIST FORM
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,
    ) -> requests.Response:
        """ """
        action = "community_find_packages"

        valid_qp: dict[str, Any] = self._qp_comm_find_packages(**qp)
        url = self._make_current_url_community(
            action=action,
        )

        logger.debug("url is now: %s", url)
        logger.debug("qp is now: %s", qp)
        logger.debug("post_data is now: %s", post_data)

        return self._post(
            action=action,
            url=url,
            body="json",
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            post_data=post_data,
            **valid_qp,
        )

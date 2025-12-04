"""
def:: community-api: 'api/public/v1/community'
def:: COMMUNITIES: [ "gem" "npm" "nuget" "psgallery" "pypi" "vsx" ]

[ ] https://{portalUrl}/{community-api}/find/packages
    [ ] POST :: may return multiple packages/versions
    [ ] Request Body schema: application/json top level is a array/list

    query Parameters:
        offset [optional], integer, Default: 0
            This parameter is used for pagination to specify the starting index
            when enumerating package versions in the response.
        limit [optional] , integer, Validate [ 1 .. 100 ] , Default: 5
            Specify the maximum number of package versions to include in the response.
        compact [optional], boolean, Default: false
            When this parameter is specified in the request,
              all optional response fields are automatically removed from the response to reduce its size.
            Intended for OEM and product integrations.

    POST DATA:
            THE POST DATA SECTION IS NOT VALIDATED CURRENTLY only that the top level element must be a list
"""

import logging
from typing import (
    Any,
    Dict,
    List,
)

# from spectra_assure_api_client.communication.exceptions import SpectraAssureInvalidAction

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)

COMMUNITIES: List[str] = [
    "gem",
    "npm",
    "nuget",
    "psgallery",
    "pypi",
    "vsx",
]


class SpectraAssureApiOperationsCommunityFindPackages(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes

    @staticmethod
    def _qp_create(
        **qp: Any,
    ) -> Dict[str, Any]:
        """
        query Parameters:
            offset [optional], integer, Default: 0
                This parameter is used for pagination to specify the starting index
                when enumerating package versions in the response.
            limit [optional] , integer, Validate [ 1 .. 100 ] , Default: 5
                Specify the maximum number of package versions to include in the response.
            compact [optional], boolean, Default: false
                When this parameter is specified in the request,
                  all optional response fields are automatically removed from the response to reduce its size.
                Intended for OEM and product integrations.

        """
        r: Dict[str, Any] = {}
        for k in ["offset", "limit", "compact"]:
            if k in qp:
                r[k] = qp[k]
        return r

    def community_find_packages(
        self,
        *,  # force name based params
        post_data: List[Any],  # MUST BE IN LIST FORM
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Any:
        """ """
        action = "community_find_packages"

        valid_qp: Dict[str, Any] = self._qp_create(**qp)
        url = self._make_current_url_community(
            action=action,
        )

        logger.debug("url is now: %s", url)
        logger.debug("qp is now: %s", qp)
        logger.debug("post_data is now: %s", post_data)

        return self.do_it_post(
            action=action,
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            post_data=post_data,
            **valid_qp,
        )

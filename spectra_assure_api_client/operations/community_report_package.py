import logging
from typing import (
    Any,
)

import requests

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsCommunityReportPackage(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    @staticmethod
    def _qp_comm_report_package(
        **qp: Any,
    ) -> dict[str, Any]:
        # The query parameters come from the specification, not from a list kept here.
        return SpectraAssureApiOperationsBase._accepted_query("community_report_package", "community", qp)

    def community_report_package(
        self,
        *,  # force name based params
        repository: str,
        package: str,
        namespace: str | None = None,
        version: str | None = None,
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,
    ) -> requests.Response:

        action = "community_report_package"
        # we will the namespace to the package as the rest of the lib does not understand namespace
        if namespace is not None and len(namespace) > 0:
            package = f"{namespace}/{package}"

        valid_qp: dict[str, Any] = self._qp_comm_report_package(**qp)
        url = self._make_current_url_community(
            action=action,
            repository=repository,
            package=package,
            version=version,
        )
        logger.debug("url is now: %s", url)

        return self._do_it_get(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **valid_qp,
        )

import logging
from typing import (
    Any,
)

import requests

from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsAuditLogExport(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def audit_log_export(
        self,
        *,
        name: str,
        datetime_start: str,
        datetime_end: str,
        should_create_cef: bool = False,
        should_create_ndjson: bool = False,
        filters: list[Any] | None = None,
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,  # ignored
    ) -> requests.Response:
        if filters:
            if not isinstance(filters, list):
                msg = "when filters is specified it must be a list"
                raise SpectraAssureInvalidAction(message=msg)

        action = "audit_log_export"
        url = self._url_for(self._resolve("audit_log_export", "organization"))
        logger.debug("url is now: %s", url)

        post_data = {
            "name": name,
            "should_create_cef": should_create_cef,
            "should_create_ndjson": should_create_ndjson,
            "datetime_start": datetime_start,
            "datetime_end": datetime_end,
        }

        if filters:
            z: list[Any] = []
            for item in filters:
                z.append(item)
            post_data["filters"] = z
        logger.debug("post_data is now: %s", post_data)

        return self._post(
            action=action,
            url=url,
            body="json",
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            post_data=post_data,
        )

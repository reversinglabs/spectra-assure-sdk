import logging
from typing import (
    Any,
)

import requests

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsAuditLogStatus(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def audit_log_status(
        self,
        *,
        job_id: str,
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,
    ) -> requests.Response:
        action = "audit_log_status"  # noqa: F841  retained for log readability
        url = self._url_for(
            self._resolve("audit_log_status", "organization"),
            job_id=job_id,
        )
        logger.debug("url is now: %s", url)

        return self._do_it_get(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

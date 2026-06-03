"""
/audit-log/{job_id}/status:
  parameters:
    - $ref: '#/components/parameters/jobId'
  get:
    operationId: export_job_status
    summary: Check status of an export job
    description: >
      Check status of an export job.
    tags:
      - Audit
"""

import logging
from typing import (
    Any,
)

from .base import SpectraAssureApiOperationsBase

# from spectra_assure_api_client.communication.exceptions import SpectraAssureInvalidAction

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsAuditLogStatus(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def audit_log_status(
        self,
        *,  # force name based params
        job_id: str,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Any:
        action = "audit_log_status"
        url = self._make_current_url_community(
            action=action,
        )
        url = url + f"/{job_id}/status"
        logger.debug("url is now: %s", url)

        return self.do_it_get(
            action=action,
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

import logging
from typing import (
    Any,
)

import requests

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsRevoke(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def revoke(
        self,
        *,
        project: str,
        package: str,
        version: str,
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,
    ) -> requests.Response:
        self._require_reason(action="revoke", qp=qp)

        supported = [
            "version",
        ]

        return self._simple_operation(
            project=project,
            package=package,
            version=version,
            action="revoke",
            verb="put",
            supported=supported,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

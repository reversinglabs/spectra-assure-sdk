# https://{portalUrl}/api/public/v1/sync/{organization}/{group}/pkg:rl/{project}/{package}@{version}
# no qp

import logging
from typing import (
    Any,
)

import requests

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsSync(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def sync(
        self,
        *,
        project: str,
        package: str,
        version: str,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        supported = [
            "version",
        ]

        qp: dict[str, Any] = {}
        return self._simple_operation(
            project=project,
            package=package,
            version=version,
            action="sync",
            verb="post",
            supported=supported,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

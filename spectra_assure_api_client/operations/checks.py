import logging
from typing import (
    Any,
)

import requests

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsChecks(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def checks(
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
            action="checks",
            verb="get",
            supported=supported,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

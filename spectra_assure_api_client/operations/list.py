import logging
from typing import (
    Any,
)

import requests

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsList(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def list(
        self,
        *,
        project: str | None = None,
        package: str | None = None,
        version: str | None = None,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        supported = [
            "group",
            "project",
            "package",
            "version",
        ]

        qp: dict[str, Any] = {}

        return self._simple_operation(
            project=project,
            package=package,
            version=version,
            action="list",
            verb="get",
            supported=supported,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

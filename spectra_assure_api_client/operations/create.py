import logging
from typing import (
    Any,
)

import requests

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsCreate(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def create(
        self,
        *,
        project: str,
        package: str | None = None,
        version: str | None = None,
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,
    ) -> requests.Response:
        supported = [
            "project",
            "package",
        ]

        return self._simple_operation(
            project=project,
            package=package,
            version=version,
            action="create",
            verb="post",
            supported=supported,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

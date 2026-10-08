import logging
from typing import (
    Any,
)

import requests

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsDelete(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def delete(
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
            "version",
        ]

        return self._simple_operation(
            project=project,
            package=package,
            version=version,
            action="delete",
            verb="delete",
            supported=supported,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

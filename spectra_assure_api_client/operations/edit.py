import logging
from typing import (
    Any,
)

import requests

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsEdit(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def edit(
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
            action="edit",
            verb="patch",
            supported=supported,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

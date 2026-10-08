import logging
import os
from typing import (
    Any,
)

import requests

from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsScan(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def scan(  # pylint: disable=too-many-arguments
        self,
        *,
        project: str,
        package: str,
        version: str,
        file_path: str,
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,
    ) -> requests.Response:
        action = "scan"
        supported = ["version"]

        if not (os.path.isfile(file_path) and os.access(file_path, os.R_OK)):
            msg = f"'{action}' needs the specified file '{file_path}' to exist and be readable"
            raise SpectraAssureInvalidAction(message=msg)

        return self._simple_operation(
            project=project,
            package=package,
            version=version,
            action=action,
            verb="post",
            supported=supported,
            file_path=file_path,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

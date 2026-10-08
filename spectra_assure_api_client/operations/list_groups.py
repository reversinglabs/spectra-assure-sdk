import logging
from typing import (
    Any,
)

import requests

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsListGroups(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def list_groups(
        self,
        *,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        url = self._url_for(self._resolve("list_groups", "group"))
        qp: dict[str, Any] = {}
        return self._do_it_get(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

# base_url: https://{portalUrl}/api/public/v1/
# "<self.base_url>/usage/<ORGANIZATION_NAME>"
# "<self.base_url>/usage/<ORGANIZATION_NAME>/<GROUP_NAME>"


import logging
from typing import (
    Any,
)

import requests

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsUsage(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def usage(
        self,
        *,
        group: str | None = None,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        # The group argument overrides the client's configured group here:
        # `usage(group=...)` reports on that group, not on the session default.
        if group is None:
            operation = self._resolve("usage", "organization")
            url = self._url_for(operation)
        else:
            operation = self._resolve("usage", "group")
            url = self._url_for(operation, group=group)

        qp: dict[str, Any] = {}
        return self._do_it_get(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

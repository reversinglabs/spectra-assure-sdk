import logging
from typing import (
    Any,
)

import requests

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsExportProfile(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def export_profile(
        self,
        *,
        organization: str,
        group: str | None = None,
        auto_adapt_to_throttle: bool | None = None,
        # **qp: Any,  # ignored
    ) -> requests.Response:
        # organization and group are arguments here, not session context:
        # the caller chooses whose profile to export.
        if group is None:
            operation = self._resolve("export_profile", "organization")
            url = self._url_for(operation, organization=organization)
        else:
            operation = self._resolve("export_profile", "group")
            url = self._url_for(operation, organization=organization, group=group)

        qp: dict[str, Any] = {}
        return self._do_it_get(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

import logging
from typing import (
    Any,
)

import requests

from .core import (
    SpectraAssureApiCore,
)

logger = logging.getLogger(__name__)


class SpectraAssureApiPatch(
    SpectraAssureApiCore,
):
    def _do_it_patch(
        self,
        *,
        url: str,
        auto_adapt_to_throttle: bool | None,
        **qp: Any,
    ) -> requests.Response:
        logger.debug(url)
        return self._basic_xx(
            url=url,
            headers=self._make_headers(),
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            action="PATCH",
            **qp,
        )

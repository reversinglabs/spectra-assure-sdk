import logging
from typing import (
    Any,
)

import requests

from .core import (
    SpectraAssureApiCore,
)

logger = logging.getLogger(__name__)


class SpectraAssureApiGet(
    SpectraAssureApiCore,
):
    def _do_it_get(
        self,
        *,
        url: str,
        auto_adapt_to_throttle: bool | None,
        **qp: Any,
    ) -> requests.Response:
        logger.debug("URL: %s", url)
        logger.debug("QUERY PARAMS: %s", qp)

        return self._basic_xx(
            url=url,
            headers=self._make_headers(),
            action="GET",
            url_params=qp,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

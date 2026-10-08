import logging
from typing import (
    Any,
)

import requests

from .core import (
    SpectraAssureApiCore,
)

logger = logging.getLogger(__name__)


class SpectraAssureApiPut(
    SpectraAssureApiCore,
):
    def _do_it_put(
        self,
        *,
        url: str,
        auto_adapt_to_throttle: bool | None,
        url_params: dict[str, str] | None = None,
        **qp: Any,
    ) -> requests.Response:
        logger.debug(url)
        return self._basic_xx(
            url=url,
            headers=self._make_headers(),
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            action="PUT",
            url_params=url_params,
            **qp,
        )

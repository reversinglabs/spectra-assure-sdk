import logging
from typing import (
    Any,
)

import requests

from .core import (
    SpectraAssureApiCore,
)

logger = logging.getLogger(__name__)


class SpectraAssureApiDelete(
    SpectraAssureApiCore,
):
    def _do_it_delete(
        self,
        *,
        url: str,
        auto_adapt_to_throttle: bool | None,
        url_params: dict[str, str] | None = None,
        **qp: Any,
    ) -> requests.Response:
        """Delete a project, package or version.

        `url_params` carries anything the specification declares as a query parameter
        -- `build` on a version delete.
        Without it those values would land in the request body, where the Portal does not look for them.
        The keyword mirrors `_do_it_put`, which has always had one.
        """
        logger.debug(url)

        return self._basic_xx(
            url=url,
            headers=self._make_headers(),
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            action="DELETE",
            url_params=url_params,
            **qp,
        )

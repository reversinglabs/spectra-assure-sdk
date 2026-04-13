import logging
from typing import (
    Any,
)

import requests

from .core import (
    Executor,
    SpectraAssureApiCore,
)

logger = logging.getLogger(__name__)


class SpectraAssureApiPut(
    SpectraAssureApiCore,
):
    def _put_with_retry(
        self,
        *,
        url: str,
        payload: dict[str, Any] | None,
        headers: dict[str, str],
        auto_adapt_to_throttle: bool = False,
    ) -> requests.Response | None:
        executor = Executor(
            url=url,
            proxies=self.proxies,
            timeout=self.timeout,
            payload=payload,
            headers=headers,
            url_params=None,
            request_callable=requests.put,
        )

        logger.debug("Proxies: %s", self.proxies)
        return self.execute_with_retry(
            auto_adapt_to_throttle=auto_adapt_to_throttle or self.auto_adapt_to_throttle,
            executor=executor,
        )

    def _basic_put(
        self,
        *,
        url: str,
        headers: dict[str, str],
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> requests.Response:

        response = self._put_with_retry(
            url=url,
            payload=qp,
            headers=headers,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )
        assert response is not None

        return self._log_response_status(
            url=url,
            response=response,
        )

    def _basic_put_with_exception_handled(
        self,
        *,
        url: str,
        headers: dict[str, str],
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> tuple[int, Any]:
        try:
            r = self._basic_put(
                url=url,
                headers=headers,
                auto_adapt_to_throttle=auto_adapt_to_throttle,
                **qp,
            )
            return r.status_code, r
        except Exception as e:  # pylint:disable=broad-exception-caught; later
            logger.exception("get: %s raises: %s", url, e)
            raise e

    def do_it_put(
        self,
        *,
        url: str,
        auto_adapt_to_throttle: bool,
        **qp: Any,
    ) -> requests.Response:
        logger.debug(url)

        headers = self._make_headers()

        return self._basic_put(
            url=url,
            headers=headers,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

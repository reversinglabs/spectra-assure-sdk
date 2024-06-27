import logging
from typing import (
    Any,
    Dict,
    Tuple,
)

import requests

from .core import (
    SpectraAssureApiCore,
    Executor,
)

logger = logging.getLogger(__name__)


class SpectraAssureApiGet(
    SpectraAssureApiCore,
):

    def _get_with_retry(
        self,
        *,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        url_params: Dict[str, str] | None,
        auto_adapt_to_throttle: bool = False,
    ) -> requests.Response | None:
        executor = Executor(
            url=url,
            proxies=self.proxies,
            timeout=self.timeout,
            payload=payload,
            headers=headers,
            url_params=url_params,
            request_callable=requests.get,
        )

        logger.debug("Proxies: %s", self.proxies)
        return self.execute_with_retry(
            auto_adapt_to_throttle=auto_adapt_to_throttle or self.auto_adapt_to_throttle,
            executor=executor,
        )

    def _basic_get(
        self,
        *,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> requests.Response:
        logger.debug("URL: %s", url)
        logger.debug("QUERY PARAMS: %s", qp)

        response = self._get_with_retry(
            url=url,
            payload=payload,
            headers=headers,
            url_params=qp,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

        assert response is not None

        return self._log_response_status(
            url=url,
            response=response,
        )

    def _basic_get_with_exception_handled(
        self,
        *,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Tuple[int, Any]:
        try:
            r = self._basic_get(
                url=url,
                payload=payload,
                headers=headers,
                auto_adapt_to_throttle=auto_adapt_to_throttle,
                **qp,
            )
            return r.status_code, r
        except Exception as e:  # pylint:disable=broad-exception-caught; later
            logger.exception("get: %s raises: %s", url, e)
            raise e

    def do_it_get(
        self,
        *,
        url: str,
        auto_adapt_to_throttle: bool,
        **qp: Any,
    ) -> requests.Response:
        logger.debug(url)

        payload: Dict[Any, Any] = {}
        headers = self._make_headers()

        return self._basic_get(
            url=url,
            payload=payload,
            headers=headers,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

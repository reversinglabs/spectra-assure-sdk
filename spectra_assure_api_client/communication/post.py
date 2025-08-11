import logging
import os
import time
from typing import (
    Any,
    Dict,
    Tuple,
)

import requests

from .core import SpectraAssureApiCore
from .exceptions import (
    SpectraAssureInvalidAction,
)

logger = logging.getLogger(__name__)


class SpectraAssureApiPost(
    SpectraAssureApiCore,
):

    def _post_with_retry(  # pylint: disable=too-many-arguments
        self,
        *,
        url: str,
        payload: Dict[str, Any] | None,
        headers: Dict[str, str],
        auto_adapt_to_throttle: bool = False,
        file_path: Any | None = None,
        **qp: Any,
    ) -> requests.Response:
        max_try = 1
        current_try = 0
        if auto_adapt_to_throttle or self.auto_adapt_to_throttle:
            max_try = 5

        logger.debug("%s", url)
        logger.debug("%s", qp)

        while current_try < max_try:
            current_try += 1

            if file_path:
                with open(file_path, "rb") as fh:
                    response = requests.post(
                        url,
                        params=qp,
                        headers=headers,
                        timeout=self.timeout,
                        proxies=self.proxies,
                        data=fh,  # payload is now a fileHandle
                    )
            else:
                response = requests.post(
                    url,
                    params=qp,
                    headers=headers,
                    timeout=self.timeout,
                    proxies=self.proxies,
                    json=payload,  # payload here is dict
                )

            if response.status_code != 429:
                break

            # first try for Throttle
            if response.status_code == 429 and current_try < max_try:  # auto retry 5 times if requested
                logger.warning(
                    "THROTTLE: %s; %s: current try: %s",
                    url,
                    response.text,
                    current_try,
                )
                delay_time = self._get_throttle_delay(response.text)
                time.sleep(delay_time)
                continue

        return response

    def _basic_post(  # pylint: disable=too-many-arguments
        self,
        *,
        url: str,
        payload: Dict[str, Any] | None,
        headers: Dict[str, str],
        auto_adapt_to_throttle: bool = False,
        file_path: Any | None = None,
        **qp: Any,
    ) -> requests.Response:
        response = self._post_with_retry(
            url=url,
            payload=payload,
            headers=headers,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            file_path=file_path,
            **qp,
        )
        return self._log_response_status(
            url=url,
            response=response,
        )

    def _basic_post_with_exception_handled(  # pylint: disable=too-many-arguments
        self,
        *,
        url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        auto_adapt_to_throttle: bool = False,
        file_path: str | None = None,
        **qp: Any,
    ) -> Tuple[int, Any]:
        try:
            r = self._basic_post(
                url=url,
                headers=headers,
                payload=payload,
                auto_adapt_to_throttle=auto_adapt_to_throttle,
                file_path=file_path,
                **qp,
            )
            return r.status_code, r
        except Exception as e:  # pylint:disable=broad-exception-caught; later
            logger.exception("get: %s raises: %s", url, e)
            raise e

    def do_it_post(
        self,
        *,
        action: str,
        url: str,
        auto_adapt_to_throttle: bool,
        file_path: str | None = None,
        post_data: Dict[str, Any] | None = None,
        **qp: Any,
    ) -> requests.Response:
        logger.debug(url)

        # post comes in 3 forms currently:
        #  1: create/sync/
        #  2: scan: use file_path
        #  3: url-import: use post_data
        if action == "scan":
            if file_path is None:
                msg = "'scan' needs a filename, none was given"
                logger.error(msg)
                raise SpectraAssureInvalidAction(message=msg)

            file_name = os.path.basename(file_path)
            h: Dict[str, str] = {
                "Content-Disposition": f"attachment; filename={file_name}",
                "Content-Type": "application/octet-stream",
            }
            headers = self._make_headers(h)
            payload = None
        elif action == "url_import":
            assert post_data is not None
            headers = self._make_headers()
            payload = post_data
        else:
            payload = qp
            headers = self._make_headers()

        # may raise IOError if the file does not exist or is not readable
        return self._basic_post(
            url=url,
            headers=headers,
            payload=payload,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            file_path=file_path,
            **qp,
        )

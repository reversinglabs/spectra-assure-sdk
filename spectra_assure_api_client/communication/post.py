"""
explicit multipart/form-data with additional args beside the file:

    import requests
    url = 'https://api.example.com/upload'
    data = {
      'description': 'My File',
      'extra': 'Some extra data'
    }
    files = {
      'file_upload': open('report.pdf', 'rb')
    }
    r = requests.post(
        url,
        data=data,
        files=files,
    )
"""

import logging
import os
import time
from typing import (
    Any,
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
        payload: Any,
        headers: dict[str, str],
        auto_adapt_to_throttle: bool = False,
        file_path: Any | None = None,
        use_multipart: bool = False,
        origin_call: str | None = None,
        **qp: Any,
    ) -> requests.Response:
        max_try = 1
        current_try = 0
        if auto_adapt_to_throttle or self.auto_adapt_to_throttle:
            max_try = 5
        msg = f"""
_post_with_retry:
    url:        {url}
    payload:    {payload}
    headers:    {headers}
    file_path:  {file_path}
    timeout:    {self.timeout}
    proxies:    {self.proxies}
    use_multipart {use_multipart}
    query params: {qp}
"""
        logger.debug(msg)

        verify = self.no_ssl_verify == False  # noqa: E712

        while current_try < max_try:
            current_try += 1

            if not file_path:
                logger.debug("Not filePath")
                response = requests.post(
                    url,
                    params=qp,
                    headers=headers,
                    timeout=self.timeout,
                    proxies=self.proxies,
                    json=payload,  # payload here is dict/list
                    verify=verify,
                )
            else:
                logger.debug("have filePath")
                if not use_multipart:
                    logger.debug("not multipart")
                    with open(file_path, "rb") as fh:
                        response = requests.post(
                            url,
                            params=qp,
                            headers=headers,
                            timeout=self.timeout,
                            proxies=self.proxies,
                            data=fh,  # payload is now a fileHandle
                            verify=verify,
                        )

                else:
                    file_name = os.path.basename(file_path)

                    logger.debug("with multipart")
                    logger.debug("file_name: %s", file_name)

                    hard_name = file_name
                    if origin_call in ["import_org_profile", "import_group_profile"]:
                        hard_name = "configuration_file"

                    with open(file_path, "rb") as fh:
                        files = {hard_name: fh}
                        logger.debug("files: %s", files)

                        response = requests.post(
                            url,
                            headers=headers,
                            timeout=self.timeout,
                            proxies=self.proxies,
                            data=payload,
                            files=files,
                            verify=verify,
                        )

            logger.debug("response.status: %d, %s", response.status_code, response.text)

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
        payload: Any,
        headers: dict[str, str],
        auto_adapt_to_throttle: bool = False,
        file_path: Any | None = None,
        use_multipart: bool = False,
        origin_call: str | None = None,
        **qp: Any,
    ) -> requests.Response:
        logger.debug("_basic_post")

        response = self._post_with_retry(
            url=url,
            payload=payload,
            headers=headers,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            file_path=file_path,
            use_multipart=use_multipart,
            origin_call=origin_call,
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
        headers: dict[str, str],
        payload: Any,
        auto_adapt_to_throttle: bool = False,
        file_path: str | None = None,
        use_multipart: bool = False,
        origin_call: str | None = None,
        **qp: Any,
    ) -> tuple[int, Any]:
        logger.debug("_basic_post_with_exception_handled")

        try:
            r = self._basic_post(
                url=url,
                headers=headers,
                payload=payload,
                auto_adapt_to_throttle=auto_adapt_to_throttle,
                file_path=file_path,
                use_multipart=use_multipart,
                origin_call=origin_call,
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
        post_data: Any = None,
        use_multipart: bool = False,
        origin_call: str | None = None,
        **qp: Any,
    ) -> requests.Response:
        logger.debug("do_it_post")
        logger.debug(url)
        logger.debug(action)

        # post comes in 3 forms currently:
        #  1: create/sync/
        #  2: scan: uses file_path
        #  3: url-import: uses post_data
        #  3: purl-import: uses post_data
        if action == "scan":
            if file_path is None:
                msg = f"'{action}' needs a filename, none was given"
                logger.error(msg)
                raise SpectraAssureInvalidAction(message=msg)

            file_name = os.path.basename(file_path)
            h: dict[str, str] = {
                "Content-Disposition": f"attachment; filename={file_name}",
                "Content-Type": "application/octet-stream",
            }
            headers = self._make_headers(h)
            payload = None
        elif action == "url_import":
            assert post_data is not None
            headers = self._make_headers()
            payload = post_data
        elif action == "purl_import":
            assert post_data is not None
            headers = self._make_headers()
            payload = post_data
        elif action == "community_find_packages":
            assert post_data is not None
            headers = self._make_headers()
            payload = post_data
        elif action in ["import_org_profile", "import_group_profile"]:
            use_multipart = True

            if file_path is None:
                msg = f"'{action}' needs a filename, none was given"
                logger.error(msg)
                raise SpectraAssureInvalidAction(message=msg)

            assert post_data is not None  # the replace bool goes here

            payload = post_data

            # Request Body schema: multipart/form-data
            headers = self._make_headers()
            # remove  "Content-Type" for multipart it will be set by the files param to post
            key = "Content-Type"
            if key in headers:
                del headers[key]
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
            use_multipart=use_multipart,
            origin_call=action,
            **qp,
        )

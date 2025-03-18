from typing import (
    Dict,
    Callable,
    Any,
)

import os
import logging
import time
import requests
import urllib.request

from .exceptions import (
    SpectraAssureInvalidAction,
)

from spectra_assure_api_client.version import VERSION


logger = logging.getLogger(__name__)


class Executor:
    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        url: str,
        proxies: Dict[str, str],
        timeout: int,
        payload: Dict[str, Any] | None,
        headers: Dict[str, str],
        url_params: Dict[str, str] | None,
        request_callable: Callable[..., requests.Response] | None = None,
        no_ssl_verify: bool = False,
    ):
        self.url = url
        self.proxies = proxies
        self.payload = payload
        self.timeout = timeout
        self.headers = headers
        self.url_params = url_params
        self.request_callable = request_callable
        self.no_ssl_verify = no_ssl_verify

    # note actually not used during post

    def execute(self) -> requests.Response:
        assert self.request_callable is not None
        if self.no_ssl_verify is True:
            os.environ["REQUESTS_CA_BUNDLE"] = ""

        return self.request_callable(
            self.url,
            params=self.url_params,
            json=self.payload,  # and what about the file upload
            headers=self.headers,
            proxies=self.proxies,
            timeout=self.timeout,
        )


class SpectraAssureApiCore:
    def __init__(  # pylint: disable=too-many-arguments,too-many-instance-attributes
        self,
        *,
        token: str,
        #
        timeout: int = (60 * 60),  # in seconds
        auto_adapt_to_throttle: bool = False,
        #
        proxy_server: str | None = None,
        proxy_port: int | None = None,
        proxy_user: str | None = None,
        proxy_password: str | None = None,
        #
        no_ssl_verify: bool = False,
    ) -> None:
        self.token = token
        self.timeout = timeout
        self.auto_adapt_to_throttle = auto_adapt_to_throttle

        self.proxy_server = proxy_server
        self.proxy_port = proxy_port
        self.proxy_user = proxy_user
        self.proxy_password = proxy_password

        self.proxies: Dict[str, str] = {}

        self._set_proxy(
            server=self.proxy_server,
            port=self.proxy_port,
            user=self.proxy_user,
            password=self.proxy_password,
        )

        if len(self.proxies) == 0:
            # also parse for default proxies using case insensitive http(s)_proxy
            self.proxies = urllib.request.getproxies()

        self.no_ssl_verify = no_ssl_verify

    @staticmethod
    def _get_throttle_delay(
        s: str,
    ) -> int:
        # s is something like: Expected available in %d seconds?.
        z = s.lower()
        try:
            k = "available in "
            s = z[z.index(k) + len(k) :]

            k = " second"  # 1 second, 2 seconds
            s = s[: s.index(k)]

            n = int(s) + 1  # add one extra second
            if n > 0:
                return n

        except Exception as e:  # pylint:disable=broad-exception-caught; later
            logger.exception("cannot find delay in throttle message: %s; %s, using 60 seconds", s, e)

        return 60

    def _validate_proxy_server_and_port(self) -> None:
        if self.proxy_server is None:
            return

        if self.proxy_port is None:
            msg = "when specifying a proxy server, you also must specify a proxy port"
            raise SpectraAssureInvalidAction(message=msg)

    def _set_proxy(
        self,
        *,
        server: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        self._validate_proxy_server_and_port()  # may raise exception

        if server is None:
            return

        if user is None:
            self.proxies = {
                "http": f"http://{server}:{port}",
                "https": f"http://{server}:{port}",
            }
            return

        self.proxies = {
            "http": f"http://{user}:{password}@{server}:{port}",
            "https": f"http://{user}:{password}@{server}:{port}",
        }

    def _make_headers(
        self,
        a_dict: Dict[str, str] | None = None,
    ) -> Dict[str, str]:
        assert self.token is not None
        assert len(self.token) > 0

        # common defaults
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": f"Spectra Assure SDK {VERSION}",
            "Content-Type": "application/json",
        }
        if a_dict:
            headers.update(a_dict)  # merge additional header info

        return headers

    @staticmethod
    def _log_response_status(
        url: str,
        response: requests.Response,
    ) -> requests.Response:

        if response.status_code == 429:
            logger.warning(
                "THROTTLE: %s; %s",
                url,
                response.text,
            )
            return response

        if 200 <= response.status_code < 300:
            logger.info(
                "%s %s",
                url,
                response.status_code,
            )
            return response

        if response.status_code == 404:  # Not found
            logger.info(
                "NotFound: %s %s %s",
                url,
                response.status_code,
                response.text,
            )
            return response

        if 400 <= response.status_code < 500:
            logger.warning(
                "%s %s %s",
                url,
                response.status_code,
                response.text,
            )
            return response

        if response.status_code >= 500:
            logger.critical(
                "%s %s %s",
                url,
                response.status_code,
                response.text,
            )
            return response

        logger.warning(
            "unexpected: %s %s %s",
            url,
            response.status_code,
            response.text,
        )
        return response

    def execute_with_retry(
        self,
        auto_adapt_to_throttle: bool,
        executor: Executor,
    ) -> requests.Response:

        max_try = 1
        current_try = 0
        if auto_adapt_to_throttle:
            max_try = 5

        while current_try < max_try:
            current_try += 1

            response = executor.execute()

            if response.status_code != 429:
                return response

            # first try for Throttle
            if response.status_code == 429 and current_try < max_try:  # auto retry 5 times if requested
                logger.warning(
                    "THROTTLE: %s; %s: current try: %d",
                    executor.url,
                    response.text,
                    current_try,
                )
                delay_time = SpectraAssureApiCore._get_throttle_delay(
                    response.text,
                )
                time.sleep(delay_time)
                continue

        return response

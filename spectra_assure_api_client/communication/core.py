"""HTTP transport: proxies, headers, and throttle handling.

`Executor` builds each attempt from scratch rather than holding a pre-built request,
so the upload case reopens its file on every try and needs no separate code path.
"""

from __future__ import annotations

import logging
import os
import re
import time
import urllib
import urllib.parse
import urllib.request
from collections.abc import Mapping
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import (
    Any,
    TypeVar,
)

import requests

from spectra_assure_api_client.version import VERSION

from .constants import (
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_READ_TIMEOUT,
    FALLBACK_THROTTLE_DELAY,
    HTTP_TOO_MANY_REQUESTS,
    MAX_DATE_THROTTLE_DELAY,
    MAX_THROTTLE_ATTEMPTS,
)
from .exceptions import (
    SpectraAssureInvalidAction,
)

logger = logging.getLogger(__name__)


# scheme://user:PASSWORD@host. The password is everything between the first ':'
# after the user name and the last '@', so an '@' inside it cannot end it early.
# This is a pattern rather than a URL parser on purpose: the SDK builds these URLs
# with a password whose '/' is not escaped, and a parser then finds no
# credentials in exactly the URL that has some. When in doubt this over-masks.
_PROXY_CREDENTIALS = re.compile(
    r"^(?P<head>[A-Za-z][A-Za-z0-9+.-]*://[^:/@]*:).*(?P<tail>@[^@]*)$",
    re.DOTALL,
)


def _redact_proxy_url(url: str) -> str:
    """Replace the password in a proxy URL with '***'; the user name and host stay readable."""
    return _PROXY_CREDENTIALS.sub(r"\g<head>***\g<tail>", url)


def redact_proxies(proxies: Mapping[str, str]) -> dict[str, str]:
    """A copy of `proxies` that is safe to log: any password in a proxy URL is masked.

    Proxy URLs carry credentials, whether they come from the `proxy_*` arguments
    or from the `HTTP(S)_PROXY` environment variables.
    """
    return {scheme: _redact_proxy_url(url) for scheme, url in proxies.items()}


class Executor:  # pylint: disable=too-many-instance-attributes
    """One request, re-issuable.

    `execute()` may be called several times; each call builds a fresh request.
    That matters for uploads, where the body is a file that has to be reopened
    before every attempt.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        url: str,
        proxies: dict[str, str],
        payload: Any,
        method: str,
        session: requests.Session,
        headers: dict[str, str],
        timeout: int = DEFAULT_READ_TIMEOUT,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
        read_timeout: int = DEFAULT_READ_TIMEOUT,
        url_params: dict[str, str] | None,
        no_ssl_verify: bool | None = None,
        file_path: str | None = None,
        use_multipart: bool = False,
        multipart_field_name: str | None = None,
    ):
        self.url = url
        self.proxies = proxies
        self.payload = payload
        #
        self.timeout = timeout
        self.read_timeout = read_timeout
        self.connect_timeout = connect_timeout
        #
        self.headers = headers
        self.url_params = url_params
        self.method = method
        self.session = session
        self.file_path = file_path
        #
        self.use_multipart = use_multipart
        self.multipart_field_name = multipart_field_name
        #
        if no_ssl_verify is None:
            no_ssl_verify = False
        self.no_ssl_verify = no_ssl_verify
        logger.debug("no_ssl_verify: %s", self.no_ssl_verify)

    def _common(self, *, with_body: bool = True) -> dict[str, Any]:
        return {
            "params": self.url_params,
            "headers": self._headers(with_body=with_body),
            "proxies": self.proxies,
            "timeout": self._timeout(),
            "verify": not self.no_ssl_verify,
        }

    def _timeout(self) -> tuple[int, int] | int:
        """The timeout for one attempt.

        requests takes `(connect, read)` as a pair. Without a connect timeout a
        host that never answers ties the call up for the whole read timeout,
        which defaults to an hour.
        """
        if not self.connect_timeout:
            return self.read_timeout

        return (self.connect_timeout, self.read_timeout)

    def _headers(self, *, with_body: bool) -> dict[str, str]:
        """The headers for one attempt.

        `Content-Type` describes a body, so it is dropped when there is none: a
        GET that declares `application/json` and sends nothing is describing
        something that is not there.

        A copy is returned rather than the stored dict, because an Executor is
        re-executed on every retry and must not mutate its own state.
        """
        if with_body:
            return dict(self.headers)

        return {k: v for k, v in self.headers.items() if k.lower() != "content-type"}

    def _send(self, **kwargs: Any) -> requests.Response:
        """Issue one request through the client's session."""
        return self.session.request(self.method, self.url, **kwargs)

    def _has_body(self) -> bool:
        """Whether this request carries a JSON body at all.

        The argument bag doubles as the body, and for GET, DELETE and a
        parameterless POST such as sync() it is empty. Serialising that as `{}`
        put a two-byte body on requests that have nothing to say: unusual on a
        GET, and on a kept-alive connection anything that fails to drain it
        corrupts the next request on that socket.

        An empty list is a real body -- community_find_packages() may send one --
        so only None and {} count as absent.
        """
        return self.payload is not None and self.payload != {}

    def execute(self) -> requests.Response:
        logger.debug("no_ssl_verify: %s", self.no_ssl_verify)

        if self.file_path is None:
            if self._has_body():
                return self._send(json=self.payload, **self._common())

            # No body at all, so no Content-Type either. requests still sets
            # Content-Length: 0 on the methods that need it, and omits it on GET.
            return self._send(**self._common(with_body=False))

        # Reopened per attempt: a handle consumed by a throttled attempt cannot
        # be rewound reliably for the next one.
        if not self.use_multipart:
            with open(self.file_path, "rb") as fh:
                return self._send(data=fh, **self._common())

        # The multipart Content-Type carries a boundary, so it is left for
        # requests to set; callers strip it from the headers beforehand.
        field = self.multipart_field_name or os.path.basename(self.file_path)
        with open(self.file_path, "rb") as fh:
            return self._send(
                data=self.payload,
                files={field: fh},
                **self._common(),
            )


# The type of `self`, for methods that return it. `typing.Self` does this on
# Python 3.11 and later; this package still supports 3.10.
_CoreT = TypeVar("_CoreT", bound="SpectraAssureApiCore")


class SpectraAssureApiCore:
    def __init__(  # pylint: disable=too-many-arguments,too-many-instance-attributes
        self,
        *,
        token: str,
        #
        timeout: int | None = None,  # alias of read_timeout, kept for existing callers
        connect_timeout: int | None = DEFAULT_CONNECT_TIMEOUT,  # in seconds, waiting for the connection
        read_timeout: int | None = None,  # in seconds, waiting for the response
        auto_adapt_to_throttle: bool = False,
        #
        proxy_server: str | None = None,
        proxy_port: int | None = None,
        proxy_user: str | None = None,
        proxy_password: str | None = None,
        #
        no_ssl_verify: bool | None = None,
    ) -> None:
        self.token = token
        #
        # `timeout` and `read_timeout` are one setting. Only the read timeout ever
        # reached requests, so `timeout=60` used to leave the effective read
        # timeout at an hour. Both names now report the same value.
        self.read_timeout = read_timeout or timeout or DEFAULT_READ_TIMEOUT
        self.timeout = self.read_timeout
        self.connect_timeout = DEFAULT_CONNECT_TIMEOUT if connect_timeout is None else connect_timeout
        #
        self.auto_adapt_to_throttle = auto_adapt_to_throttle
        #
        self.proxy_server = proxy_server
        self.proxy_port = proxy_port
        self.proxy_user = proxy_user
        self.proxy_password = proxy_password
        #
        self.proxies: dict[str, str] = {}

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

        # One session for the life of the client. Previously every call went
        # through `requests.get`/`requests.post`, each of which builds a session,
        # opens a TCP connection and runs a TLS handshake, then discards all
        # three. Reusing one connection matters most where several requests are
        # issued in a row, such as download() and filestream_download().
        #
        # NOTE: requests.Session is not thread-safe. Give each thread its own
        # client rather than sharing one.
        self.session = requests.Session()

    def close(self) -> None:
        """Release the pooled connections.

        Safe to call more than once, and the client keeps working afterwards:
        requests opens a new connection on the next call.
        """
        self.session.close()

    def __enter__(self: _CoreT) -> _CoreT:
        # Returns the type it was called on. Annotated as the base class, this made
        # `with SpectraAssureApiOperations(...) as client` type `client` as the
        # transport layer, so a type checker rejected every operation on it.
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def _throttle_setting(self, per_call: bool | None) -> bool:
        """Decide whether this call retries on 429.

        `None` means inherit the client-wide setting; an explicit `True` or `False` wins.
        """
        if per_call is None:
            return bool(self.auto_adapt_to_throttle)
        return bool(per_call)

    @staticmethod
    def _log_response_status(
        url: str,
        response: requests.Response,
    ) -> requests.Response:

        if response.status_code == HTTP_TOO_MANY_REQUESTS:
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

    @staticmethod
    def _delay_from_retry_after(value: str) -> int | None:
        """Read `Retry-After`, which RFC 9110 allows in two forms.

        Either a number of seconds, or an HTTP-date giving the moment the next
        attempt may be made. Only the seconds form was understood before, so a
        date fell through to the fixed fallback -- and a date that happens to
        begin with a number, such as "21 Oct 2026 07:28:00 GMT", was read as
        that number of seconds.

        Returns None when the header says neither.
        """
        value = value.strip()

        if value.isdigit():
            return int(value)

        try:
            when = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None

        if when is None:
            return None

        # A date without a zone is UTC by the same RFC.
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)

        seconds = int((when - datetime.now(timezone.utc)).total_seconds())

        if seconds <= 0:
            # Already in the past: retry now rather than not at all.
            return 0

        if seconds > MAX_DATE_THROTTLE_DELAY:
            # Guards against a clock skew between us and the Portal turning into
            # an arbitrarily long sleep. The seconds form is left uncapped,
            # because it says what it means and has always been trusted.
            logger.warning(
                "Retry-After is %ds away, which looks like clock skew; waiting %ds instead",
                seconds,
                MAX_DATE_THROTTLE_DELAY,
            )
            return MAX_DATE_THROTTLE_DELAY

        return seconds

    @staticmethod
    def _get_throttle_delay(
        response: requests.Response,
    ) -> int:
        """How long to wait before retrying a throttled request.

        Prefer the `Retry-After` header, which the specification documents as
        accompanying every 429. Fall back to the wait embedded in the response
        text, then to a fixed delay.
        """
        retry = response.headers.get("Retry-After")
        if retry:
            delay = SpectraAssureApiCore._delay_from_retry_after(retry)
            if delay is not None:
                return delay
            logger.debug("Retry-After is neither seconds nor a date: %r", retry)

        # s is something like: Expected available in %d seconds?.
        s = response.text
        z = s.lower()
        try:
            k = "available in "
            s = z[z.index(k) + len(k) :]

            k = " second"  # 1 second, 2 seconds
            s = s[: s.index(k)]

            n = int(s) + 1  # add one extra second
            if n > 0:
                return n

        except ValueError:
            # Expected whenever the body does not carry a wait: not exceptional,
            # so it is not logged as an exception with a stack trace.
            logger.debug(
                "no delay found in the throttle message; using %ds",
                FALLBACK_THROTTLE_DELAY,
            )

        return FALLBACK_THROTTLE_DELAY

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

        if bool(user) != bool(password):  # either both or none is ok, else fail
            msg = "when specifying a proxy user, you also must specify a proxy password and vice versa"
            raise SpectraAssureInvalidAction(message=msg)

        if server is None:
            return

        if user is None:
            self.proxies = {
                "http": f"http://{server}:{port}",
                "https": f"http://{server}:{port}",
            }
            return

        if user and password:
            # Both are percent-encoded completely (safe=""), because requests
            # percent-decodes both when it builds the Proxy-Authorization header.
            # quote() on its own leaves '/' alone, and the user name was not
            # encoded at all, so a '/' in either one cut the URL short: the proxy
            # URL became unparseable, or parsed to a different host.
            u = urllib.parse.quote(user, safe="")
            p = urllib.parse.quote(password, safe="")
            tail = f"http://{u}:{p}@{server}:{port}"
            self.proxies = {
                "http": f"{tail}",
                "https": f"{tail}",
            }

    def _make_headers(
        self,
        a_dict: dict[str, str] | None = None,
    ) -> dict[str, str]:
        if self.token is None:
            msg = "token must not be None"
            raise SpectraAssureInvalidAction(message=msg)

        if len(self.token) == 0:
            msg = "token must not be empty"
            raise SpectraAssureInvalidAction(message=msg)

        # common defaults
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": f"Spectra Assure SDK {VERSION}",
            "Content-Type": "application/json",
        }
        if a_dict:
            headers.update(a_dict)  # merge additional header info

        return headers

    def _xx_with_retry(  # pylint: disable=too-many-arguments
        self,
        *,
        url: str,
        payload: Any,
        headers: dict[str, str],
        action: str,
        auto_adapt_to_throttle: bool | None = None,
        url_params: dict[str, str] | None = None,
        file_path: str | None = None,
        use_multipart: bool = False,
        multipart_field_name: str | None = None,
    ) -> requests.Response:
        executor = Executor(
            url=url,
            proxies=self.proxies,
            #
            timeout=self.timeout,
            connect_timeout=self.connect_timeout,
            read_timeout=self.read_timeout,
            #
            payload=payload,
            headers=headers,
            url_params=url_params,
            method=action,
            session=self.session,
            no_ssl_verify=self.no_ssl_verify,
            file_path=file_path,
            use_multipart=use_multipart,
            multipart_field_name=multipart_field_name,
        )

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Proxies: %s", redact_proxies(self.proxies))
        return self._execute_with_retry(
            self._throttle_setting(auto_adapt_to_throttle),
            executor,
        )

    def _basic_xx(  # pylint: disable=too-many-arguments
        self,
        *,
        url: str,
        headers: dict[str, str],
        action: str,
        url_params: dict[str, str] | None = None,
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,
    ) -> requests.Response:

        response = self._xx_with_retry(
            url=url,
            payload=qp,
            headers=headers,
            url_params=url_params,
            action=action,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

        return self._log_response_status(
            url=url,
            response=response,
        )

    def _execute_with_retry(
        self,
        auto_adapt_to_throttle: bool,
        executor: Executor,
    ) -> requests.Response:
        """Issue a request, waiting out throttles when asked to.

        Every path through the client ends up here, uploads included. On the
        final attempt the 429 is handed back to the caller:
        there would be no attempt left to use the wait for.
        """
        max_attempts = MAX_THROTTLE_ATTEMPTS if auto_adapt_to_throttle else 1

        for attempt in range(1, max_attempts + 1):
            response = executor.execute()

            if response.status_code != HTTP_TOO_MANY_REQUESTS:
                return response

            if attempt == max_attempts:
                break

            delay_time = self._get_throttle_delay(response)
            logger.warning(
                "THROTTLE: %s; %s: attempt %d of %d, waiting %ds",
                executor.url,
                response.text,
                attempt,
                max_attempts,
                delay_time,
            )
            time.sleep(delay_time)

        return response

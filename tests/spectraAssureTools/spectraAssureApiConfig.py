# python3

import logging
from typing import (
    Any,
)

logger = logging.getLogger(__name__)


class SpectraAssureApiConfig:
    def __init__(
        self,
        *,
        host: str | None = None,
        server: str | None = None,
        organization: str | None = None,
        group: str | None = None,
        token: str | None = None,
        #
        apiVersion: str = "v1",
        #
        proxy_server: str | None = None,
        proxy_port: int | None = None,
        proxy_user: str | None = None,
        proxy_password: str | None = None,
        #
        timeout: int = 10,
        autoAdaptToThrottle: bool = False,
        **additionalArgs: Any,
    ) -> None:
        self.host = host
        self.server = server
        self.organization = organization
        self.group = group
        #
        self.token = token
        #
        self.apiVersion = apiVersion
        #
        self.proxy_server = proxy_server
        self.proxy_port = proxy_port
        self.proxy_user = proxy_user
        self.proxy_password = proxy_password

        self.timeout: int = timeout
        self._validateTimeout()
        self.autoAdaptToThrottle = autoAdaptToThrottle

        self.additionalArgs = {}
        for k, v in additionalArgs.items():
            self.additionalArgs[k] = v

    def _validateTimeout(self) -> None:
        if self.timeout > 3600:
            self.timeout = 3600

        if self.timeout < 10:
            self.timeout = 10

    # PUBLIC

    def validateMinimalConfigComplete(self) -> tuple[bool, str | None]:
        """Validate if the minimal mandatory params have been provided.

        Note:
            exits the program if not all mandatory parameters have been provided

        """
        tests = [
            self.server is None and self.host is None,
            self.organization is None,
            self.group is None,
            self.token is None,
        ]

        if any(tests):  # test if any of the tests is True
            ll = [
                f"HOST, optional: {self.host}; SERVER, optional: {self.server}; cannot be both empty.",
                f"ORGANIZATION, mandatory: {self.organization}; cannot be empty.",
                f"GROUP, mandatory: {self.group}; cannot be empty.",
                f"TOKEN is None, mandatory: {self.token is None}; cannot be True.",
            ]
            msg = "FATAL: minimal required parameters are not set properly; " + ", ".join(ll)
            return False, msg

        return True, None

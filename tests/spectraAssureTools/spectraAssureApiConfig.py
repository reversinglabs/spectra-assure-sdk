# python3

from typing import (
    Any,
    Tuple,
)

import logging

logger = logging.getLogger(__name__)


class SpectraAssureApiConfig:

    def __init__(
        self,
        *,
        server: str | None = None,
        organization: str | None = None,
        group: str | None = None,
        token: str | None = None,
        #
        host: str = "my.secure.software",
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
        self.server = server
        self.organization = organization
        self.group = group
        self.token = token
        #
        self.host = host
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

    def validateMinimalConfigComplete(self) -> Tuple[bool, str | None]:
        """Validate if the minimal mandatory params have been provided.

        Note:
            exits the program if not all mandatory parameters have been provided
        """

        tests = [
            self.server is None,
            self.organization is None,
            self.group is None,
            self.token is None,
        ]

        if any(tests):  # test if any of the tests is True
            ll = [
                f"SERVER: {self.server}",
                f"ORGANIZATION: {self.organization}",
                f"GROUP: {self.group}",
                f"TOKEN is None: {self.token is None}",
            ]
            msg = "FATAL: minimal required parameters are not set properly; " + ", ".join(ll)
            return False, msg

        return True, None

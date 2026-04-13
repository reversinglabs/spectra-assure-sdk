# python 3

import logging
import os
from typing import (
    Any,
)

prefix = "RLPORTAL_"
pprefix = "RLSECURE_PROXY_"


logger = logging.getLogger(__name__)


class SpectraAssureEnvironmentVars:
    ENVNAMESDEFAULT: dict[str, dict[str, Any]] = {
        "host": {
            "env": f"{prefix}HOST",
            "vType": "str",
        },
        "server": {
            "env": f"{prefix}SERVER",
            "vType": "str",
        },
        "organization": {
            "env": f"{prefix}ORG",
            "vType": "str",
        },
        "group": {
            "env": f"{prefix}GROUP",
            "vType": "str",
        },
        "token": {
            "env": f"{prefix}ACCESS_TOKEN",
            "vType": "str",
        },
        "proxy_server": {
            "env": f"{pprefix}SERVER",
            "vType": "str",
        },
        "proxy_port": {
            "env": f"{pprefix}PORT",
            "vType": "int",
            "default": 3128,
        },
        "proxy_user": {
            "env": f"{pprefix}USER",
            "vType": "str",
        },
        "proxy_password": {
            "env": f"{pprefix}PASSWORD",
            "vType": "str",
        },
    }

    def __init__(
        self,
        *,
        externalEnvVarsInfo: dict[str, dict[str, Any]] | None = None,
    ):
        super().__init__()

        self._prepEnvironmentVars(externalEnvVarsInfo)

    @staticmethod
    def coerceType(
        value: Any,
        valueType: str,
    ) -> Any:
        if value is None:
            return None

        # convert enforce values str, int, bool
        if valueType == "str":
            return str(value)

        if valueType == "int":
            return int(value)

        if valueType == "bool":
            return bool(value)

        return value

    def _prepEnvironmentVars(
        self,
        externalEnvVarsInfo: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.envVarsInfo = self.ENVNAMESDEFAULT
        if externalEnvVarsInfo:
            self.envVarsInfo = externalEnvVarsInfo

    # PUBLIC
    def processEnvironmentVars(self) -> dict[str, Any]:
        envDict: dict[str, Any] = {}

        if self.envVarsInfo is None:
            return envDict

        for name, inf in self.envVarsInfo.items():
            k = inf.get("env")
            if k is None:
                continue

            assert k is not None
            z = os.getenv(k)
            if z is None:
                continue

            assert z is not None
            value = z

            valueType = inf.get("vType")
            if valueType is None:
                valueType = "str"

            assert valueType is not None
            try:
                envDict[name] = self.coerceType(value, valueType)
            except Exception as e:
                logger.error(
                    "cannot coerce value: %s to type: %s for key: %s; %s",
                    value,
                    valueType,
                    k,
                    e,
                )
                continue

        logger.debug("%s", envDict)
        return envDict

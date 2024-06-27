# python 3

from typing import (
    Dict,
    Any,
)

import os
import logging


prefix = "RLPORTAL_"
pprefix = "RLSECURE_PROXY_"


logger = logging.getLogger(__name__)


class SpectraAssureEnvironmentVars:
    ENVNAMESDEFAULT: Dict[str, Dict[str, Any]] = {
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
        externalEnvVarsInfo: Dict[str, Dict[str, Any]] | None = None,
    ):
        super().__init__()

        self._prepEnvironmentVars(externalEnvVarsInfo)

    @staticmethod
    def coerceType(value: Any, valueType: str) -> Any:
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
        externalEnvVarsInfo: Dict[str, Dict[str, Any]] | None = None,
    ) -> None:
        self.envVarsInfo = self.ENVNAMESDEFAULT
        if externalEnvVarsInfo:
            self.envVarsInfo = externalEnvVarsInfo

    # PUBLIC

    def processEnvironmentVars(self) -> Dict[str, Any]:
        envDict: Dict[str, Any] = {}

        if self.envVarsInfo is None:
            return envDict

        for name, inf in self.envVarsInfo.items():
            k = inf.get("env")
            if k is None:
                continue

            z = os.getenv(str(k))
            if z is None:
                continue

            value = str(z)

            valueType = inf.get("vType")
            if valueType is None:
                valueType = "str"
            valueType = str(valueType)

            envDict[name] = self.coerceType(value, str(valueType))

        logger.info(f"Env: {envDict}")

        return envDict

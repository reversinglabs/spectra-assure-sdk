# python 3

from typing import (
    Dict,
    Any,
)

import json

from .spectraAssureConfigFile import SpectraAssureConfigFile

import logging

logger = logging.getLogger(__name__)


class SpectraAssureConfigFileJson(
    SpectraAssureConfigFile,
):
    def __init__(
        self,
        *,
        configOptions: Dict[str, Dict[str, str]] | None = None,
        configFileJson: str | None = None,
    ) -> None:
        super().__init__(configOptions=configOptions)

        self._addConfigFile(configFileJson)

    def _loadConfig(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        if self.configFile is None:
            return data

        try:
            with open(str(self.configFile), "r") as f:
                d = json.load(f)
                for k, v in d.items():
                    data[k] = v
        except Exception as e:
            msg = f"cannot load the config file: {self.configFile}:: {e}"
            logger.exception(msg)

        return data

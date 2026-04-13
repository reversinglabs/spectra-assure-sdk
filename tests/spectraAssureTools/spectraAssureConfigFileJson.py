# python 3

import json
import logging
from typing import (
    Any,
)

from .spectraAssureConfigFile import SpectraAssureConfigFile

logger = logging.getLogger(__name__)


class SpectraAssureConfigFileJson(
    SpectraAssureConfigFile,
):
    def __init__(
        self,
        *,
        configOptions: dict[str, dict[str, str]] | None = None,
        configFileJson: str | None = None,
    ) -> None:
        super().__init__(configOptions=configOptions)

        self._addConfigFile(configFileJson)

    def _loadConfig(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.configFile is None:
            return data

        try:
            with open(str(self.configFile)) as f:
                d = json.load(f)
                for k, v in d.items():
                    data[k] = v
        except Exception as e:
            msg = f"cannot load the config file: {self.configFile}:: {e}"
            logger.exception(msg)

        return data

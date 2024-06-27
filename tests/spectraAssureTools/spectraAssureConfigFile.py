# python 3

from typing import (
    Dict,
    Any,
)

import os
import logging

from pathlib import Path
from abc import ABC, abstractmethod

from .spectraAssureExceptions import (
    InvalidAction,
)


logger = logging.getLogger(__name__)


class SpectraAssureConfigFile(
    ABC,
):
    configOptions: Dict[str, Dict[str, str]] = {
        "server": {"vType": "str"},
        "organization": {"vType": "str"},
        "group": {"vType": "str"},
        "token": {"vType": "str"},
        #
        "proxy_server": {"vType": "str"},
        "proxy_port": {"vType": "int"},
        "proxy_user": {"vType": "str"},
        "proxy_password": {"vType": "str"},
        #
        "autoAdaptToThrottle": {"vType": "bool"},
        "timeout": {"vType": "int"},
    }

    def __init__(
        self,
        *,
        configOptions: Dict[str, Dict[str, str]] | None = None,
    ) -> None:
        super().__init__()

        self.startupDone = False
        self.configData: Dict[str, Any] = {}

        if configOptions:
            self.configOptions = configOptions

    @staticmethod
    def _simplePathToPosix(targetPath: str) -> str:
        """return a path with more POSIX-like separators (path does not need to exist)"""
        return targetPath.replace("\\", "/")

    def _existsFile(
        self,
        itemPath: str,
    ) -> str:
        """test if path exists and is a file, return the POSIX realpath
        raises exception if path does not exist or is not a file
        """

        fp = Path(itemPath)
        exists = fp.exists()

        if exists is False:
            msg = "the config file must exist if specified"
            raise InvalidAction(msg)

        if fp.is_dir():
            msg = "the config file must be a file"
            raise InvalidAction(msg)

        itemPath = self._simplePathToPosix(itemPath)
        return os.path.realpath(itemPath)

    @abstractmethod
    def _loadConfig(self) -> Dict[str, Any]:  # Interface only
        data: Dict[str, Any] = {}
        return data

    def _addConfigFile(
        self,
        configFile: str | None = None,
    ) -> None:
        self.configFile = None
        if configFile is None:
            return
        self.configFile = self._existsFile(configFile)

    def _processConfigFile(self) -> Dict[str, Any]:
        rr: Dict[str, Any] = {}

        if self.configFile is None:
            return rr

        data = self._loadConfig()
        for k, v in data.items():
            if k not in self.configOptions:
                msg = f"ignore item '{k}' it is not part of the current configOptions"
                logger.warning(msg)
                continue

            try:
                t = self.configOptions[k].get("vType")
                rr[k] = self.coerceType(v, str(t))
            except Exception as e:
                msg = f"ignore item '{k}' value '{v}' does not convert to type '{t}': {e}"
                logger.exception(msg)

        return rr

    # PUBLIC

    @staticmethod
    def coerceType(value: Any, valueType: str) -> Any:
        # convert enforce values str, int, bool, float

        if valueType == "str":
            return str(value)

        if valueType == "int":
            return int(value)

        if valueType == "bool":
            return bool(value)

        if valueType == "float":
            return float(value)

        return value

    def getConfigOptions(self) -> Dict[str, Dict[str, str]]:
        return self.configOptions

    def addConfigOption(
        self,
        key: str,
        typeName: str | None = None,
    ) -> None:
        """add one config key and type to the current config items

        Args:
         - key: str; mandatory
            Add a config item with name given by the key strings

         - typeName: str | None = None
            Optionally specify what type the value should be (we can validate str, int, bool currently)

        Note:
            After creating the object with its default config read from a file,
            you can add additional config items with this function.
            All config values get processed only once
            and returned on the values() call.
            After that, the config will no longer change.

        """
        t = "vType"
        if self.startupDone is True:
            logger.warning("startup has completed - no further changes to the config can be done")
            return

        if key in self.configOptions:
            logger.warning(f"you are redefining a existing config: {key} -> {self.configOptions[key]}")

        self.configOptions[key] = {t: ""}
        if typeName is None:
            return

        typeNames = ["int", "bool", "str", "float"]
        if typeName not in typeNames:
            logger.warning(f"we currently support validating {typeNames}, your type {typeName} will not be validated")
        self.configOptions[key][t] = typeName

    def getValues(self) -> Dict[str, Any]:
        """process the file and return the data

        Note:
            We process only once;
            after that, only the processed data is returned
        """

        if self.startupDone is False:
            self.configData = self._processConfigFile()
            self.startupDone = True

        return self.configData

    def getConfigFileNow(self) -> Dict[str, Any]:
        cfDict: Dict[str, Any] = {}

        cf = self.getConfigOptions()
        for key, value in self.getValues().items():
            valueType = cf.get(key, {}).get("vType")
            cfDict[key] = self.coerceType(value, str(valueType))

        logger.info(f"config file: {cfDict}")

        return cfDict

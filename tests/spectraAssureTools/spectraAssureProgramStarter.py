# python 3

from typing import (
    Dict,
    Any,
    Tuple,
    List,
)

import sys
import os
import argparse
import logging

from spectraAssureTools import (
    SpectraAssureApiConfig,
)


from .spectraAssureConfigFile import SpectraAssureConfigFile
from .spectraAssureEnvironmentVars import SpectraAssureEnvironmentVars


logger = logging.getLogger(__name__)


class SpectraAssureProgramStarter:

    def __init__(
        self,
        *,
        progName: str | None = None,
        description: str | None = None,
        epilog: str | None = None,
        #
        externalEnvVarsInfo: Dict[str, Dict[str, Any]] | None = None,
        configFileHandle: SpectraAssureConfigFile | None = None,
        **additionalKwArgs: Any,
    ) -> None:
        """
        Args:

         - progName: str | None, default None
            If required, you can override the program name from the default:
            - os.path.basename(sys.argv[0])

         - description: str | None, default None
            If required, set the description for this program

         - epilog: str | None, default None
            If required, set the epilog for this program.
            The epilog is shown at the end of the usage() in case of errors
            or if -h, --help is specified

         - externalEnvVarsInfo: Dict | None , default None
            By default, the program knows about standard environment variables used by SpectraAssureApi.
            You can override the naming of the environment variables here.
            The environment variables will be merged into the final parameterList,
            according to the 'strategyLoadConfigParams' in getConfig()

         - configFileHandle:  SpectraAssureConfigFile | None , default None
            When using an external config file (currently JSON), you pass a SpactraAssureConfigFile parameter here.
            The config file will be merged into the final parameterList,
            according to the 'strategyLoadConfigParams' in getConfig()

         - additionalKwArgs: Any
            Nonstandard parameters specified will be collected in the
            additionalConfig Dict for later use by the program

        Note:
            Positional arguments are not supported,
            all arguments have to be named

        """
        self.configFileHandle: SpectraAssureConfigFile | None = configFileHandle  # allow a external config file
        self.apiConfig: SpectraAssureApiConfig | None = None
        self.startupDone = False

        self._setProgName(progName)
        self._setDescription(description)
        self._setEpilog(epilog)

        self.envVars = SpectraAssureEnvironmentVars(
            externalEnvVarsInfo=externalEnvVarsInfo,
        )
        self._prepAdditionalConfig(
            **additionalKwArgs,
        )

        self.parser = argparse.ArgumentParser(
            prog=self.progName,
            description=self.description,
            epilog=self.epilog,
        )

    def _startupCliArgs(self) -> None:
        if self.startupDone is True:
            return

        self._parseMyApiArgs()
        self._parseMyOptionalArgs()
        self._parseMyProxyArgs()

    def _setProgName(self, progName: str | None = None) -> None:
        self.progName = os.path.basename(sys.argv[0])
        if progName:
            self.progName = progName

    def _setDescription(self, description: str | None = None) -> None:
        self.description = "This program uses the Spectra Assure Portal"
        if description:
            self.description = description

    def _setEpilog(self, epilog: str | None = None) -> None:
        self.epilog = """
            Interfacing with the Spectra Assure Portal API

            Parameters are evaluated only after all elements
            of the strategy list have been loaded and merged.

            The strategy list by default is: CONFIGFILE -> CLI -> ENV.

            Any parameter (re)specified in a later stage wins.
            Additional parameters are collected and become available as:

             - apiConfig, additionalConfig = mySpectraAssureProgramStarter.getConfig()
        """

        if epilog:
            self.epilog = epilog

    def _prepAdditionalConfig(
        self,
        **additionalKwArgs: Any,
    ) -> None:
        self.additionalConfig: Dict[str, Any] = {}
        for k, v in additionalKwArgs.items():
            self.additionalConfig[k] = v

    @staticmethod
    def _simplePathToPosix(targetPath: str) -> str:
        """return a path with more POSIX-like separators (path does not need to exist)"""
        return targetPath.replace("\\", "/")

    def _parseMyApiArgs(self) -> None:
        assert self.parser is not None

        sap = "Spectra Assure Portal"
        env = "can also be set using an environment variable"

        # Mandatory Portal access parameters
        self.parser.add_argument(
            "--server",
            dest="server",
            help=f"the mandatory 'server' name for the {sap}, {env}",
        )
        self.parser.add_argument(
            "--organization",
            dest="organization",
            help=f"the mandatory 'organization' name for the {sap}, {env}",
        )
        self.parser.add_argument(
            "--group",
            dest="group",
            help=f"the mandatory 'group' name for the {sap}, {env}",
        )
        self.parser.add_argument(
            "--token",
            dest="token",
            help=f"the mandatory 'access-token' for the {sap}, {env}",
        )

    def _parseMyOptionalArgs(self) -> None:
        assert self.parser is not None

        # autoAdaptToThrottle
        self.parser.add_argument(
            "--autoAdaptToThrottle",
            dest="autoAdaptToThrottle",
            default=None,  # use none as default so the override strategy works
            action="store_true",
            help="automatically adapt to throttle messages by waiting the required wait time",
        )

        # timeout
        self.parser.add_argument(
            "--request-timeout",
            dest="timeout",
            default=None,
            type=int,
            help="set the request timeout in seconds, default 3600, must be >= 30 and <= 3600",
        )

    def _parseMyProxyArgs(self) -> None:
        assert self.parser is not None

        env = "can also be set using an environment variable"

        # proxy arguments
        p = "set an optional proxy"
        self.parser.add_argument(
            "--proxy-server",
            dest="proxy_server",
            help=f"{p} server, {env}",
        )
        self.parser.add_argument(
            "--proxy-port",
            dest="proxy_port",
            type=int,
            default=None,  # no default as we may want to override from other sources (env or config file)
            help=f"{p} port (only used if proxy_host is set), {env}",
        )
        self.parser.add_argument(
            "--proxy-user",
            dest="proxy_user",
            help=f"{p} user for proxy authentication, {env}",
        )
        self.parser.add_argument(
            "--proxy-password",
            dest="proxy_password",
            help=f"{p} password (only used if proxy_user is set), {env}",
        )

    def _parseProcessCliArgs(self) -> Dict[str, Any]:
        assert self.parser is not None

        # https://stackoverflow.com/questions/42279063/python-typehints-for-argparse-namespace-objects
        # my_args = MyProgramArgs(**vars(self.parser.parse_args())
        cliDict = vars(self.parser.parse_args())

        logger.info(f"Cli: {cliDict}")
        return cliDict

    def _applyConfigFileNow(self) -> Dict[str, Any]:
        cfDict: Dict[str, Any] = {}
        if self.configFileHandle is None:
            return cfDict

        return self.configFileHandle.getConfigFileNow()

    def updateParamsDict(
        self,
        paramsDict: Dict[str, Any],
        inputDict: Dict[str, Any],
    ) -> None:
        for k, v in inputDict.items():
            if v is not None:
                paramsDict[k] = v

    def _processArgsStrategy(
        self,
        strategyLoadConfigParams: List[str],
    ) -> Dict[str, Any]:
        if strategyLoadConfigParams == []:
            strategyLoadConfigParams = ["CONFIGFILE", "CLI", "ENV"]

        paramsDict: Dict[str, Any] = {}

        for what in strategyLoadConfigParams:
            if what.upper() == "CONFIGFILE":
                self.updateParamsDict(paramsDict, self._applyConfigFileNow())
            elif what.upper() == "CLI":
                self.updateParamsDict(paramsDict, self._parseProcessCliArgs())
            elif what.upper() == "ENV":
                self.updateParamsDict(paramsDict, self.envVars.processEnvironmentVars())
            else:
                logger.warning(f"skip: the parameter-load-strategy requested is unknown: {what}")

        return paramsDict

    # PUBLIC

    def getCliParser(self) -> argparse.ArgumentParser:
        assert self.parser is not None
        return self.parser

    def getConfig(
        self,
        *,
        strategyLoadConfigParams: List[str] = ["CONFIGFILE", "CLI", "ENV"],
    ) -> Tuple[SpectraAssureApiConfig, Dict[str, Any]]:
        """getConfig processes all parameter sources and produces a merged result according to the chosen strategy

        Args:
         - strategyLoadConfigParams: List[str].
            A list of strings indicating the sequence of processing

            The default strategy is:    ["CONFIGFILE", "CLI", "ENV"]
             - first, the config file    "CONFIGFILE" if one was provided
             - second, the cli           "CLI"
             - third, the environment    "ENV"

         - mustBeValid: bool, default True
            If True (the default), we enforce the minimal required parameters,
            and raise an exception if they are not all provided.

            If False, no validation for the minimal required parameters will be done.
            This means you may be missing essential parameters to connect to SpectraAsureApi.

        Return:
            We return a tuple (apiConfig, additionalConfig)
            apiConfig: SpectraAssureApiConfig,
            additionslConfig: Dict[str, Any]

        Notes:

        """
        self._startupCliArgs()

        paramsDict: Dict[str, Any] = self._processArgsStrategy(
            strategyLoadConfigParams,
        )

        # now apply the combined args to the SpectraAssureApiConfig
        self.apiConfig = SpectraAssureApiConfig(
            **paramsDict,
        )

        return self.apiConfig, self.additionalConfig

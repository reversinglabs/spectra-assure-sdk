# python 3


from typing import (
    Dict,
    Any,
)

import logging

from spectra_assure_api_client import (
    SpectraAssureApiOperations,
)

from spectraAssureTools import (
    SpectraAssureProgramStarter,
    SpectraAssureConfigFileJson,
)


logger = logging.getLogger()


class MyProgramStarter(SpectraAssureProgramStarter):
    """MyProgramStarter customizes the default program starter by adding custom arguments
    we add additional optional arguments:

     - project:
        Specify a project to test with

     - package
        Specify a package to test with

     - version
        Specify a version to test with.
        Mostly we will not use this during tests
        so the download step will find the latest approved
        (or all approved if that download-strategy is chosen)

     - skipCreateIfExist:
        This skips the create-project and create-package if they already exist.
        (and skips the delete-project at the end during download test)
        as we need manual approve the versions they have to persist during test

     - downloadPath:
        Specify a existing path where we will test downloading approved version files.
    """

    def addMyArgs(self) -> None:
        assert self.parser is not None

        for j in ["project", "package", "version"]:
            # all are optional
            self.parser.add_argument(
                f"--{j}",
                dest=f"{j}",
                help=f"optional; the current {j} name",
            )

        self.parser.add_argument(
            "--skipCreateIfExist",
            dest="skipCreateIfExist",
            action="store_true",
            default=None,  # use none as default so the override strategy works
            help="skip create project and package during testing",
        )

        self.parser.add_argument(
            "--downloadPath",
            dest="downloadPath",
            help="optional; when downloading we will use this path. [must exist]",
        )


def basicStarter() -> SpectraAssureApiOperations:
    """The minimal start of a program
    with a config file
    but without any customzations.

    We return aOperationHandle on which we later can call direct all operations.
    e.g. list, edit create, scan, ...

    like:
        data = aOperationHandle.list(project=project, package=package, version = version)

    any additional arguments become available to our program via:

     - aDict = aOperationHandle.getAdditionalArgs()

    """
    # create a config file handle
    aConfigFileHandle = SpectraAssureConfigFileJson(
        configFileJson="myConfig.json",
    )

    # create a program starter with a config file
    aProgramStarter = SpectraAssureProgramStarter(
        configFileHandle=aConfigFileHandle,
    )

    # parse and merge all arguments and return a apiConfig and any additional configuration options
    apiConfig, additionalConfig = aProgramStarter.getConfig()

    # create a operations handle for all operations and pass all additiona args also
    aOperationsHandle = SpectraAssureApiOperations(
        **vars(apiConfig),
        **additionalConfig,
    )

    return aOperationsHandle


def makeMyEnvVarOPtions() -> Dict[str, Dict[str, Any]]:

    prefix = "RLPORTAL_"
    pprefix = "RLSECURE_PROXY_"

    externalEnvVarsInfo: Dict[str, Dict[str, Any]] = {
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

    return externalEnvVarsInfo


def prepConfigFile() -> SpectraAssureConfigFileJson:
    """prepConfigFile
    sets up a config file with additional arguments just as we did with MyProgramStarter.
    We add the same arguments also to the config file,
    so they will be processed in combination with the minimal required arguments.
    """

    # prepare a config file
    configFileHandle = SpectraAssureConfigFileJson(
        configFileJson="myConfig.json",
    )

    # and add additional arguments with type enforcement
    additions = {
        "downloadPath": "str",
        "skipCreateIfExist": "bool",
        "project": "str",
        "package": "str",
        "version": "str",
    }

    for k, t in additions.items():
        configFileHandle.addConfigOption(
            key=k,
            typeName=t,
        )

    return configFileHandle


def customizedStarter() -> SpectraAssureApiOperations:
    """A custom starter
    that modifies:

    - the Environment parser
    - the config file
    - cli args

    """

    strategyLoadConfigParams = ["CLI", "ENV", "CONFIGFILE"]  # change the load order, do config file last

    # override default env vars
    externalEnvVarsInfo = makeMyEnvVarOPtions()

    # use customized config file
    configFileHandle = prepConfigFile()

    aProgramStarter = MyProgramStarter(
        externalEnvVarsInfo=externalEnvVarsInfo,
        configFileHandle=configFileHandle,
    )

    # add additional cli args before processing
    aProgramStarter.addMyArgs()

    apiConfig, additionalConfig = aProgramStarter.getConfig(
        strategyLoadConfigParams=strategyLoadConfigParams,
    )

    vv = dict(**vars(apiConfig))
    logger.debug(f"actual arguments: {vv}")

    additionalConfig = vv["additionalArgs"]  # additionalArgs
    logger.debug(f"additional arguments: {additionalConfig}")

    token = vv.get("token")  # token is coming from the environment
    configFile = "./myConfig.json"  # the config file has no token so we get it from elsewhere

    aOperationsHandle = SpectraAssureApiOperations(
        token=token,
        config_file=configFile,
        **additionalConfig,
    )

    return aOperationsHandle


def startProg() -> SpectraAssureApiOperations:
    useAdditional = True

    if useAdditional is True:
        aOperationsHandle = customizedStarter()
    else:
        aOperationsHandle = basicStarter()

    return aOperationsHandle

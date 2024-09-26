# Spectra Assure SDK for Python

Spectra Assure SDK for Python is the official library maintained by ReversingLabs that makes it easier to integrate with the [Spectra Assure Portal](https://docs.secure.software/portal/) and interact with it in your own applications.

The SDK provides access to operations supported by the [Spectra Assure Portal API](https://docs.secure.software/api/).
The Portal API only supports Portal Projects features, and cannot be used to work with the File Stream.

You can use the SDK to:

- Create and delete projects and packages in the Portal
- Add and remove package versions in the Portal
- Update details for projects, packages, and versions
- Get a list of all projects in a group, all packages in a project, all versions in a package, and show details for any package version
- Show analysis status and performed checks for a package version
- Download analysis reports for a package version
- Download package versions previously approved in the Portal GUI


> **Note:**
> This documentation assumes that you already have a working knowledge of
> Python and previous experience with setting up your own Python projects.


**What is the Spectra Assure Portal?**

The Spectra Assure Portal is a SaaS solution that's part of the [Spectra Assure platform](https://www.reversinglabs.com/products/software-supply-chain-security) - a new ReversingLabs solution for software supply chain security.
More specifically, the Portal is a web-based application for improving and managing the security of your software releases and verifying third-party software used in your organization.

With the Spectra Assure Portal, you can:

- Scan your software packages to detect potential risks before release.
- Improve your SDLC by applying actionable advice from security scan reports to all phases of software development.
- Organize your software projects and automatically compare package versions to detect potentially dangerous behavior changes in the code.
- Manage software quality policies on the fly to ensure compliance and achieve maturity in your software releases.


## Table of contents

- [Versioning](#versioning)
- [Requirements and dependencies](#requirements-and-dependencies)
- [Installation](#installation)
- [Authentication](#authentication)
- [Quick start](#quick-start)
   - [Logging](#logging)
- [Usage](#usage)
   - [Rate limiting](#rate-limiting)
   - [Configuration](#configuration)
   - [Validation](#validation)
   - [Exceptions](#exceptions)
- [Reference](#reference)
   - [Operations](#operations)
- [Support](#support)
- [License](#license)



## Versioning

| SDK Version | Status | API version |
| -- | -- | -- |
| 1.0 | Latest | v1 |


## Requirements and dependencies

- Python (minimal version: 3.10)
- [requests](https://pypi.org/project/requests/) (version not critical)
- An active Spectra Assure Portal account. If you don't already have a Portal account, you may need to contact the administrator of your Portal organization to [invite you](https://docs.secure.software/portal/members#invite-a-new-member). Alternatively, if you're not a Spectra Assure customer yet, you can [contact ReversingLabs](https://docs.secure.software/portal/#get-access-to-securesoftware-portal) to sign up for a Portal account.
- A [Personal Access Token](https://docs.secure.software/api/generate-api-token) generated for your Spectra Assure Portal account.


## Installation

To get started with the Spectra Assure SDK, install the latest version from PyPI with pip:

`pip install spectra-assure-sdk`

By default, the SDK uses the Spectra Assure Portal API `v1` with `my.secure.software` as the host.
The default host and API version must not be modified by SDK users.


## Authentication

Before using the Spectra Assure SDK, you need to set up authentication credentials for your Portal account.

If you don't already have it, generate a [Personal Access Token](https://docs.secure.software/api/generate-api-token) for your account.

When you have the token, you can use it in any of the following ways:

- in a JSON configuration file
- with the `token` argument in your code

[Roles and permissions](https://docs.secure.software/portal/user-management#roles-and-permissions) set for your Portal account automatically apply to your token, and control which actions you can perform.

Keep in mind that Personal Access Tokens for Portal accounts have an expiration date.
After a token expires, any apps or integrations relying on it for authentication will stop functioning.
When this happens, you have to generate a new token and update it in all relevant places.


## Quick start

You must import the `SpectraAssureApiOperations` class.

To start working with the SDK, initialize an instance of `SpectraAssureApiOperations` and specify all [required parameters](#usage).

*Using named arguments is explicitly enforced - positional arguments are not supported in any of the SDK calls.*

The following code example shows how to combine different ways of specifying the required parameters (as named arguments, in a JSON configuration file, or both).

**Python code example**

```
import os
from spectra_assure_api_client import SpectraAssureApiOperations

prefix = "RLPORTAL_"

server = str(os.getenv(f"{prefix}SERVER"))
organization = str(os.getenv(f"{prefix}ORG"))
group = str(os.getenv(f"{prefix}GROUP"))
token = str(os.getenv(f"{prefix}ACCESS_TOKEN"))

configFile = "./myConfig.json"

for what in [1, 2, 3]:
    try:
        if what == 1:
            # Use only named arguments
            aHandle = SpectraAssureApiOperations(
                server=server,
                organization=organization,
                group=group,
                token=token,
            )
        elif what == 2:
            # Use only the configuration file
            # Note: with the current configFile example, this will fail because the token is not specified
            aHandle = SpectraAssureApiOperations(
                configFile=configFile,
            )
        elif what == 3:
            # Combine the configuration file with named arguments
            aHandle = SpectraAssureApiOperations(
                configFile=configFile,
                token=token,
            )
        print(aHandle)
    except Exception as e:
        print(e)
```

**Example configuration file - myConfig.json**

```
{
  "SpectraAssureApi" : {
    "server": "test",
    "organization": "Test",
    "group": "Default",
    "timeout": 60,
    "auto_adapt_to_throttle": true
  }
}
```


### Logging

The SDK uses logging internally. You can interface with the logging functions in the SDK by using the standard Python logging library.

**Logging example**

```
import os
import logging
import sys
from spectra_assure_api_client import SpectraAssureApiOperations

logger = logging.getLogger()

def make_logger(logger: logging.Logger) -> None:
     logger.setLevel(logging.DEBUG)

     progName = os.path.basename(sys.argv[0])
     if progName.endswith(".py"):
         progName = progName[:-3]
     fileName = f"{progName}.log"

     fh = logging.FileHandler(fileName)
     fh.setLevel(logging.INFO)

     ch = logging.StreamHandler()
     ch.setLevel(os.getenv("LOG_LEVEL", "WARNING"))

     formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
     ch.setFormatter(formatter)
     fh.setFormatter(formatter)

     # add the handlers to logger
     logger.addHandler(ch)
     logger.addHandler(fh)

if __name__ == "__main__":
    make_logger(logger)
    logger.info("start program")
```


## Usage

The following parameters are mandatory for all operations:

- **server** - Name of the Portal instance to use in requests.
The Portal instance name usually matches the subdirectory of my.secure.software in your Portal URL.
For example, if your portal URL is 'my.secure.software/demo', the instance name to use with this parameter is 'demo'.
- **organization** - Name of a Portal organization to use in requests.
The user account that is sending the request must be a member of the specified organization and have the appropriate
permissions to perform the requested operation. Organization names are case-sensitive.
- **group** - Name of a Portal group to use in requests. The group must exist in the specified Portal organization.
Group names are case-sensitive.
- **token** - Personal Access Token for authenticating to the Portal API.

The following parameters are optional:

- **timeout** - The request timeout to be used for HTTPS requests to the Portal API, specified in seconds.
The default is 10 seconds.

- **auto_adapt_to_throttle** - Some requests may be
[throttled](#rate-limiting)
and require a minimal wait time before the next request.
With this option, you can automatically wait for the data to become available and for the required time to pass.
By default, this option is disabled (set to `false`).
This parameter can also be specified on each individual operation.


Some operations support multiple targets (project, package, version) that have to be provided as named arguments.
Based on the provided arguments, the library can automatically decide the target of the operation.
The first value of 'None' decides the target of the operation:

```
 - project: str | None;
   If we don't have a project name,
   we are doing something with a group.
 - package: str | None;
   If we don't have a package name,
   we are doing something with a project.
 - version: str | None;
   If we don't have a version name,
   we are doing something with a package.
 - If all args are not None,
   we are doing something with a version.
```

Refer to the full list of [supported operations](#operations) for more details
on their usage and specific parameters they support.


### Rate limiting

Requests to the Spectra Assure Portal API are subject to rate limiting as defined in [the official API documentation](https://docs.secure.software/api-reference/#section/About-the-API/Rate-limiting).

This means that rate limits will also apply to requests sent by the SDK.

Optionally, you can enable the `auto_adapt_to_throttle` setting globally
(when creating the `SpectraAssureApiOperations` instance) or on each individual operation.

Because this setting may slow down responses, it is not recommended for interactive use.
It is most suitable for automatic batch processing.


### Configuration

The SDK supports specifying mandatory and optional parameters in any of the following ways:

- in a JSON configuration file
- directly as named arguments in the code

By default, the configuration is evaluated and merged in that order: configuration file -> named arguments.
If a parameter is specified more than once, the latest stage overrides all previous instances.
In other words, if a parameter is set in the configuration file and as a argument,
the SDK will use the value from the argument.

The configuration file must be in JSON format.
The file name is arbitrary.
The file structure requires that all configuration parameters are placed as keys in the top-level `SpectraAssureApi`
object like in the following example:

```
{
  "SpectraAssureApi" : {
    "server": "test",
    "organization": "Test",
    "group": "Default",
    "timeout": 60,
    "auto_adapt_to_throttle": true
  }
}
```

The configuration file supports the following parameters:

**Mandatory**

- server: `string`
- organization: `string`
- group: `string`
- token: `string`

**Optional**

- proxy_server: `string`
- proxy_port: `int`
- proxy_user: `string`
- proxy_password: `string`
- timeout: `int`
- auto_adapt_to_throttle: `bool`


All `proxy_*` parameters are optional.
However, if you're using `proxy_server`, then you must also use `proxy_port`.
Similarly, `proxy_user` and `proxy_password` must be used together.

### Validation

Some operations support additional query parameters with values that require validation
(for example, strings that have limited length or enumerated values).

The SDK does not explicitly check all values - the validation is performed on the Portal side.

Before using query parameters, it is recommended to check their limitations in the
[Portal API reference documentation](https://docs.secure.software/api-reference/) or in the [Portal OpenAPI specification](https://docs.secure.software/redocusaurus/secure-software-public-v1.yaml).


### Exceptions

All operations return a `requests.Response` and may raise exceptions in case of errors or misconfiguration.
It is up to the SDK user to handle any exceptions.

Depending on the operation and the type of issue, the following exceptions may be raised:

- `SpectraAssureInvalidAction` - This action is not allowed
- `SpectraAssureInvalidPath` - The specified path is incorrect
- `SpectraAssureUnexpectedNoDataFound` - Received no data where we expected some
- `SpectraAssureNoDownloadUrlInResult` - The query returns no download URL
- `SpectraAssureUnsupportedStrategy` - Attempted download strategy is not supported
- `UrlDownloaderUnknownHashKey` - No digest found; can't find the proper hash key or the hash type is not supported
- `UrlDownloaderTargetDirectoryIssue` - The target file path does not exist or is not a directory
- `UrlDownloaderTargetFileIssue` - The target file name can't be extracted from the URL
- `UrlDownloaderTempFileIssue` - There is an issue with the target directory
- `UrlDownloaderFileVerifyIssue` - Cannot calculate hash; verification failed


## Examples

An example program showing all supported operations is available in this repository:
[api_client_example.py](./examples/api_client_example.py)


## Reference

The `doc` folder in the SDK GitHub repository contains reference pages for individual operations.

You can also consult the official
[Spectra Assure Portal](https://docs.secure.software/portal/) and
[API reference documentation](https://docs.secure.software/api/)
for more detailed instructions on specific features and functionalities.


### Operations

Every class listed in this section maps directly to a Portal API operation,
except **SpectraAssureApiOperationsDownload** which is a synthetic operation not directly available on the Portal.

If an operation supports query parameters, they should be provided in the `qp` argument list.
Any invalid parameters will be automatically filtered out.

[`SpectraAssureApiOperationsChecks`](./doc/checks.md)

**Show performed checks for a version.**

|        | Group | Project | Package | Version |
| --     | --    |    --   |  --     |    --   |
| Targets |  |  |  | ✔️ |
| Query parameters |  |  |  |  |


[`SpectraAssureApiOperationsCreate`](./doc/create.md)

**Create a project or package in the Portal.**

|        | Group | Project | Package | Version |
| --     | --    |    --   |  --     |    --   |
| Targets |  | ✔️ | ✔️ |  |
| Query parameters |  | ✔️ | ✔️ |  |


[`SpectraAssureApiOperationsDelete`](./doc/delete.md)

**Remove a project, package, or version from the Portal.**

|        | Group | Project | Package | Version |
| --     | --    |    --   |  --     |    --   |
| Targets |  | ✔️ | ✔️ | ✔️ |
| Query parameters |  |  |  | ✔️ |


[`SpectraAssureApiOperationsDownload`](./doc/download.md)

**Download file(s) of approved version(s).**

This class uses `list` and `status` operations to gather information about what is downloadable,
and only requests the artifact download URL for versions that are selected for download.

Every time the download link is generated, your Portal download capacity is reduced by the artifact's file size,
even if the artifact is not downloaded from the link.
If your user account doesn't have permission to download files from the Portal,
the API responds with an error and the download capacity remains unaffected.


[`SpectraAssureApiOperationsEdit`](./doc/edit.md)

**Edit details for a project, package, or version.**

|        | Group | Project | Package | Version |
| --     | --    |    --   |  --     |    --   |
| Targets |  | ✔️ | ✔️ | ✔️ |
| Query parameters |  | ✔️ | ✔️ | ✔️ |


[`SpectraAssureApiOperationsList`](./doc/list.md)

**List all groups, projects, packages, and versions.**

|        | Group | Project | Package | Version |
| --     | --    |    --   |  --     |    --   |
| Targets | ✔️ | ✔️ | ✔️ | ✔️ |
| Query parameters |  |  |  |  |


[`SpectraAssureApiOperationsReport`](./doc/report.md)

**Download analysis report for a version.**

|        | Group | Project | Package | Version |
| --     | --    |    --   |  --     |    --   |
| Targets |  |  |  | ✔️ |
| Query parameters |  |  |  | ✔️ |


[`SpectraAssureApiOperationsScan`](./doc/scan.md)

**Upload and scan a new version.**

|        | Group | Project | Package | Version |
| --     | --    |    --   |  --     |    --   |
| Targets |  |  |  | ✔️ |
| Query parameters |  |  |  | ✔️ |


[`SpectraAssureApiOperationsStatus`](./doc/status.md)

**Show analysis status for a version.**

|        | Group | Project | Package | Version |
| --     | --    |    --   |  --     |    --   |
| Targets |  |  |  | ✔️ |
| Query parameters |  |  |  | ✔️ |


## Support

To get assistance with the Spectra Assure SDK,
you or your company need to have an existing support agreement with ReversingLabs.
Then you can submit a support request with "Spectra Assure SDK" in the message subject.

ReversingLabs does not provide support if the original code from the official Spectra Assure SDK repository
has been modified by you or any other open source community members.
In those cases, contact the author(s) of the modified SDK for help.


## License

The Spectra Assure SDK (Software Development Kit) for Python is released under [the MIT License](./LICENSE.MD).

<!-- 2024-09-26: Spectra Assure CLI 2.4.0 has been released; -->

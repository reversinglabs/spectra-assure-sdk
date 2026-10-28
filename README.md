# Spectra Assure SDK for Python &middot; [![RL Status Badge](https://secure.software/pypi/badge/spectra-assure-sdk)](https://secure.software/pypi/packages/spectra-assure-sdk)

> **Note: Python 3.11 will be the minimum in the next version.**
> This version still supports Python 3.10, which reaches its end of life on 2026-10-31.
> The next version of the SDK will require Python 3.11 or later.

Spectra Assure SDK for Python is the official library maintained by ReversingLabs that makes it easier to integrate with the [Spectra Assure Portal](https://docs.secure.software/portal/) and interact with it in your own applications.

The SDK provides access to the operations supported by the [Spectra Assure Portal API](https://docs.secure.software/api/), allowing you to work with Portal File Stream and Projects.

You can use the SDK to:

- Create, edit and delete projects and packages, and edit and delete versions
- Add versions by uploading a file, or by importing it from a URL or a package URL (PURL)
- List the projects in a group, the packages in a project and the versions of a package, and show the details of a version
- Show the analysis status and the performed checks of a version, download its analysis reports and its RL-SAFE archive, and rescan it
- Approve, reject and revoke versions, and download approved versions
- Upload or import, analyze, approve and download standalone files in the File Stream
- Query the Spectra Assure Community for open-source packages
- List the groups of an organization, show usage, export and import profile configurations, and export the audit log


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
- [Examples](#examples)
- [Reference](#reference)
- [Operations](#operations)
- [Community repositories](#community-repositories)
- [Sessions](#sessions)
- [Support](#support)
- [License](#license)
- [Changes](#changes)
- [Versioning](#versioning)

## Requirements and dependencies

- Python (minimal version: 3.10)
- [requests](https://pypi.org/project/requests/); version: >=2.32.2,<=2.34.2
- An active Spectra Assure Portal account. If you don't already have a Portal account, you may need to contact the administrator of your Portal organization to [invite you](https://docs.secure.software/portal/members#invite-a-new-member). Alternatively, if you're not a Spectra Assure customer yet, you can [contact ReversingLabs](https://docs.secure.software/portal/#get-access-to-securesoftware-portal) to sign up for a Portal account.
- A [Personal Access Token](https://docs.secure.software/api/generate-api-token) generated for your Spectra Assure Portal account.


## Installation

To get started with the Spectra Assure SDK, install the latest version from PyPI with pip:

`pip install spectra-assure-sdk`

The SDK uses version `v1` of the Spectra Assure Portal API.
Tell it where your Portal is with `host`, `server` or both; see [Usage](#usage).
The API settings `api_version`, `api_domain` and `api_proto` must not be changed.


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

The following example reads the settings from environment variables, lists the groups the specified token can access,
and closes the connection when the `with` block ends.

**Python code example**

```python
import os

from spectra_assure_api_client import SpectraAssureApiOperations

# os.environ[...] fails at once when a variable is missing; str(os.getenv(...))
# would instead pass the text "None" on as the organization name.
with SpectraAssureApiOperations(
    host=os.environ["RLPORTAL_HOST"],
    server=os.environ.get("RLPORTAL_SERVER"),  # optional
    organization=os.environ["RLPORTAL_ORG"],
    group=os.environ["RLPORTAL_GROUP"],
    token=os.environ["RLPORTAL_ACCESS_TOKEN"],
) as client:
    response = client.list_groups()
    print(response.status_code, response.json())
```

The settings can also come from a JSON configuration file, alone or together with named arguments,
which take precedence over the file (see [Configuration](#configuration)):

```python
import os

from spectra_assure_api_client import SpectraAssureApiOperations

with SpectraAssureApiOperations(
    config_file="./myConfig.json",
    token=os.environ["RLPORTAL_ACCESS_TOKEN"],  # keeps the token out of the file
) as client:
    print(client.list_groups().status_code)
```

**Example configuration file - myConfig.json**

```json
{
  "SpectraAssureApi" : {
    "host": "my.secure.software",
    "server": "test",
    "organization": "Test",
    "group": "Default",
    "timeout": 60,
    "auto_adapt_to_throttle": true
  }
}
```


## Logging

The SDK logs through the standard Python `logging` module, under the logger `spectra_assure_api_client`
(each module logs to a child of it, such as `spectra_assure_api_client.communication.core`).
It never logs the token, and it masks a proxy password.
Configure it like any library logger:

```python
import logging

logging.basicConfig(level=logging.WARNING)
logging.getLogger("spectra_assure_api_client").setLevel(logging.INFO)
```

For scripts, the SDK has a helper that sets up a console handler, at the level in the `LOG_LEVEL`
environment variable (default `WARNING`), and a `<program>.log` file in the current directory.
Calling it again replaces the handlers it added rather than adding more:

```python
import logging

from spectra_assure_api_client import SpectraAssureApiOperations

logger = logging.getLogger()
SpectraAssureApiOperations.make_logger(my_logger=logger)
logger.info("start program")
```


## Usage

The following parameters are mandatory for all operations:


- **organization** - Name of a Portal organization to use in requests.
The user account that is sending the request must be a member of the specified organization and have the appropriate
permissions to perform the requested operation. Organization names are case-sensitive.
- **group** - Name of a Portal group to use in requests. The group must exist in the specified Portal organization.
Group names are case-sensitive.
- **token** - Personal Access Token for authenticating to the Portal API.

The following parameters are optional:

- **host** - The host name of your Portal, usually `my.secure.software`.
<br> Any other host will be explicitly communicated to customers.
- **server** - Name of the Portal instance (tenant) to use in requests.
<br> The Portal instance name usually matches the subdirectory of my.secure.software in your Portal URL.
<br> For example, if your portal URL is 'my.secure.software/demo', the instance name to use with this parameter is 'demo'.

At least one of `host` and `server` must be given; with neither, the client cannot be created.
They combine like this:

| Setting | Requests go to |
| -- | -- |
| `server` only | `https://my.secure.software/<server>/api/public/v1` |
| `host` only | `https://<host>/api/public/v1` |
| `host` and `server` | `https://<host>/<server>/api/public/v1` |
| `server` is `trial` or `playground`, with or without `host` | `https://<server>.secure.software/api/public/v1` |

- **read_timeout** - The read timeout to be used for HTTPS requests, specified in seconds.
<br>The default is 3600 seconds.
- **timeout** - The older name for `read_timeout`; both set the same value.
<br>If both are given, `read_timeout` is used.
- **connect_timeout** - The connect timeout used by the https requests, specified in seconds.
<br>The default is 10 seconds.
<br>Downloads keep the read timeout within 10 to 3600 seconds and the connect timeout within 1 to 10 seconds;
a value outside that range is adjusted and a warning is logged.
- **auto_adapt_to_throttle** - Some requests may be [throttled](#rate-limiting)
and require a minimal wait time before the next request.
<br> With this option, you can automatically wait for the data to become available and for the required time to pass.
<br> By default, this option is disabled (set to `false`).
<br> This parameter can also be specified on each individual operation.
- **no_ssl_verify** - Set to `true` to turn off TLS certificate verification.
<br> By default, certificates are verified. Use this only for testing.
- **config_file** - Path to an optional JSON configuration file that supplies any of these settings; see [Configuration](#configuration).
- **proxy_server**, **proxy_port**, **proxy_user**, **proxy_password** - Optional proxy settings for all requests.
<br> `proxy_server` needs `proxy_port`, and `proxy_user` and `proxy_password` go together.
- **additional_args** - Data of your own, passed through untouched; `get_additional_args()` returns it.

Every setting can be given as a named argument or in the configuration file.


Operations on the Portal's projects, packages and versions take `project`, `package` and `version`
as named arguments, and what they are given decides what they act on:

| `project` | `package` | `version` | The call acts on |
| -- | -- | -- | -- |
| not given | not given | not given | the group |
| given | not given | not given | the project |
| given | given | not given | the package |
| given | given | given | the version |

Which of these a call supports is shown in its table in [Operations](./Operations.md).
File Stream calls take a `file_id` instead.

Refer to the full list of [supported operations](./Operations.md) for more details
on their usage and specific parameters they support.


### Rate limiting

Requests to the Spectra Assure Portal API are subject to rate limiting as defined in [the official API documentation](https://docs.secure.software/api-reference/#section/About-the-API/Rate-limiting).

This means that rate limits will also apply to requests sent by the SDK.

Optionally, you can enable the `auto_adapt_to_throttle` setting globally
(when creating the `SpectraAssureApiOperations` instance) or on each individual operation.
A call that is answered with 429 waits as long as specified in the API's `Retry-After` header and tries again,
up to 5 attempts in total. Without that header, the call waits 60 seconds.

Download link requests are the exception. The API allows 10 requests per minute, so `download()` and
`filestream_download()` wait out a 429 on a link request even when the setting is off.
To fail immediately instead, pass `auto_adapt_to_throttle=False` to the call.

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

- The configuration file must be in JSON format.
- The file name must end in `.json`, and the file must contain the `SpectraAssureApi` object;
  otherwise the SDK raises `SpectraAssureInvalidAction`.
- The file structure requires that all configuration parameters are placed as keys in the top-level `SpectraAssureApi` object like in the following example:

```json
{
  "SpectraAssureApi" : {
    "host": "my.secure.software",
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

- organization: `string`
- group: `string`
- token: `string`

**Optional**

- host: `string`
- server: `string`
- proxy_server: `string`
- proxy_port: `int`
- proxy_user: `string`
- proxy_password: `string`
- timeout: `int` (same as `read_timeout`)
- read_timeout: `int`
- connect_timeout: `int`
- auto_adapt_to_throttle: `bool`
- no_ssl_verify: `bool` | None = None.


A setting the SDK does not recognise is ignored, and a `UserWarning` is issued that names it and suggests
the closest valid name. This applies to unknown keyword arguments and to unknown keys inside the
`SpectraAssureApi` object of a configuration file.
Keys outside that object are not checked.

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

Operations return the `requests.Response` of the API call, except four that do more than one call:
`download` and `filestream_download` return a `dict` describing what was downloaded, or `None` when nothing qualified,
and `rl_safe_download` and `filestream_rl_safe_download` return a tuple `(downloaded, file_path)`.
The operations that return the response do not raise on an HTTP error status; check `response.status_code`.
The four download calls raise an exception when the API answers with an error.
All operations raise exceptions for errors in their arguments or configuration.
It is up to the SDK user to handle any exceptions.

Every exception the SDK raises derives from `SpectraAssureExceptions`, so one `except SpectraAssureExceptions` catches them all.
Depending on the operation and the type of issue, the following exceptions may be raised:

- `SpectraAssureExceptions` - The base of all of them.
  - `SpectraAssureInvalidAction` - This action is not allowed, or a setting is invalid.
    It is also raised for every problem with the configuration file: it is missing or cannot be read,
    it is not valid JSON or not UTF-8 text, or it does not contain a JSON object with a `SpectraAssureApi` object in it.
    The original error, such as `FileNotFoundError` or `json.JSONDecodeError`, is available as its `__cause__`.
  - `SpectraAssureWaitTimeoutExceeded` - A wait timeout has expired.
  - `SpectraAssureInvalidPath` - The specified path is incorrect.
  - `SpectraAssureUnexpectedNoDataFound` - Received no data where we expected some.
  - `SpectraAssureNoDownloadUrlInResult` - The query returns no download URL.
  - `SpectraAssureUnsupportedStrategy` - Attempted download strategy is not supported.
  - `SpectraAssureSpecError` - The compiled API specification shipped with the SDK is missing or damaged; a packaging fault.
  - `UrlDownloaderExceptions` - The base of the downloader's exceptions.
    - `UrlDownloaderUnknownHashKey` - No digest found; can't find the proper hash key or the hash type is not supported.
    - `UrlDownloaderTargetDirectoryIssue` - The target file path does not exist or is not a directory.
    - `UrlDownloaderTargetFileIssue` - The target file name can't be extracted from the URL.
    - `UrlDownloaderTempFileIssue` - No temporary file can be created in the target directory.
    - `UrlDownloaderFileVerifyIssue` - Cannot calculate hash; verification failed.


## Examples

An example program showing all supported operations is available in this repository:
[api_client_example.py](./examples/api_client_example.py)


## Reference

The `doc` folder in the SDK GitHub repository contains reference pages for individual operations.

You can also consult the official
[Spectra Assure Portal](https://docs.secure.software/portal/) and
[API reference documentation](https://docs.secure.software/api/)
for more detailed instructions on specific features and functionalities.


## Operations

Every call is described in [Operations](./Operations.md): one entry per operation, with the class that provides it,
a table of the levels it works at, and a link to its reference page in `doc/`.

- [General operations](./Operations.md#general-operations): the organization, its groups, and projects, packages and versions;
  also the Community calls
- [File Stream](./Operations.md#file-stream): standalone files, addressed by `file_id`
- [Catalog](./Operations.md#catalog): external catalogs, and the group's software catalog

## Community repositories

The repository names the API accepts (the `community` values in its specification) are:

- `gem`
- `npm`
- `nuget`
- `psgallery`
- `pypi`
- `vsx`
- `maven`
- `clawhub`

The SDK passes the name to the API as given, so a repository the API adds works without an SDK update.
Read more about [supported communities](https://docs.secure.software/community/#supported-communities).

## Sessions

Every request a client makes goes through one `requests.Session`, held for the life of the client,
so connections to the Portal are reused rather than opened for every call.

### Public surface

    client.close()                                   release the pooled connections
    with SpectraAssureApiOperations(...) as client:   closes the session on exit
    client.session                                   the session itself, if you need to tune it

`close()` is idempotent, and the client still works afterwards: `requests` opens a fresh connection on the next call.

### Thread safety -- please read

`requests.Session` is **not thread-safe**, so a client must not be shared between threads.
Give each thread its own client.

## Support

To get assistance with the Spectra Assure SDK,
you or your company need to have an existing support agreement with ReversingLabs.
Then you can submit a support request with "Spectra Assure SDK" in the message subject.

ReversingLabs does not provide support if the original code from the official Spectra Assure SDK repository
has been modified by you or any other open source community members.
In those cases, contact the author(s) of the modified SDK for help.


## License

The Spectra Assure SDK (Software Development Kit) for Python is released under [the MIT License](./LICENSE).

## Changes

For a detailed list of changes see [CHANGES](./CHANGES.md).

## Versioning

| Version | Description |
| --      | --          |
| v1.2.0  | added the Catalog API. |
| v1.1.0  | added the File Stream API and one HTTP session per client. |
| v1.0.14 | add `audit_log_export` and `audit_log_status`, and update requests to the latest version. |
| v1.0.13 | add `community-user-account`. |
| v1.0.12 | fix the return data for `community-report-version`. |
| v1.0.11 | add import/export, purl-import, reports now all supported by api. |
| v1.0.10 | add support for community queries. |
| v1.0.9  | update to the latest python `requests` version. |
| v1.0.8  | add support for url-import. |
| v1.0.7  | add support for listGroups. |
| v1.0.6  | add support for usage. |
| v1.0.5  | add support for different hosts than the default `my.secure.software`. |
| v1.0.4  | add `rl-summary-pdf` report. |
| v1.0.3  | add `rl-safe` support. |
| v1.0.2  | add version actions: `sync`, `approve`, `reject`, `revoke`. |
| v1.0.1  | add `rl-uri` report. |
| v1.0.0  | initial. |

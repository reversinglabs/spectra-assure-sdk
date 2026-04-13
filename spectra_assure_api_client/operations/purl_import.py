r"""# PURL-IMPORT

- https://{portalUrl}/api/public/v1/purl-import/{organization}/{group}/pkg:rl/{project}/{package}@{version}

## path Parameters

organization    required    string
    Example: example-organization
    Specify the name of a Portal organization to use in the request.
    The user account that is sending the request must be a member of the specified organization and have the
        appropriate permissions to perform the requested operation.
        Organization names are case-sensitive.

group   required    string
    Example: example-group
    Specify the name of a Portal group to use in the request.
    The group must exist in the specified Portal organization.
    Group names are case-sensitive.

project required    string
    Example: example-project
    Specify the name of a Portal project to use in the request.
    Project names are case-sensitive.
    Special characters \/:*?"<>| are not supported.

package required    string
    Example: example-package
    Specify the name of a Portal package to use in the request.
    Package names are case-sensitive.
    Special characters \/:*?"<>| are not supported.

version required    string
    Example: 1.2.0
    Specify the name of a Portal package version to use in the request.
    Version names are case-sensitive.
    Special characters \/:*?"<>| are not supported.


## query Parameters

replace	    boolean Default: false
    This optional parameter lets you replace (overwrite) an already existing package version
      in the project with the package version you're uploading.
    This functionality is equivalent to the --replace option in the rl-secure scan command.
    If this parameter is set to false and the package version you're trying to upload
      already exists in the specified project,
      the API returns the 409 error response.

force	    boolean Default: false
    In Spectra Assure Portal, a package can only have a limited amount of versions.
    If a package already has the maximum number of versions, you can use this optional parameter to specify
      if the oldest version of the package should be deleted to make space for the version you're uploading.
    If this parameter is set to false and the package already has the maximum allowed number of versions,
      the API returns the 400 error response.
      Will be ignored if build=repro.

diff_with	string  Example: diff_with=1.1.0
    This optional parameter lets you specify a previous package version
      against which you want to compare (diff) the version you're uploading.
    The specified version must exist in the package.
    This functionality is equivalent to the --diff-with option in the rl-secure report command.
    Will be ignored if build=repro.

product	    string (VersionMetadataProduct) <= 200 characters
    Example: product=Example application
    Software product name

publisher	string (VersionMetadataPublisher) <= 200 characters
    Example: publisher=Example software publisher
    Software publisher

category	string  Default: "Other" Enum
    Categorization scheme for software based on their typical use or general purpose.

license     string Default: "Unknown" Enum
    SPDX-compliant license name under which the software is distributed.

platform    string  Default: "Other" Enum
    Underlying technology or framework that the software has been developed to run on.

release_date string <date-time> (DateTime)
    Example: release_date=2022-07-15T13:57:39.843631Z

max_size integer
    The maximum file size to attempt to download, in bytes.
    Keep in mind that determining file size before download can be unreliable

## Request Body
schema: application/json

purl required string <purl> <= 4096 characters
    Example: "pkg:pypi/pyaudio@0.2.13?artifact=PyAudio-0.2.13-cp311-cp311-win_amd64.whl"
    The PURL from which you want to download and import a software package into the Portal.
    If the PURL is not valid, the import will fail.

auth-user	  string
    Example: "username"
    If authentication is required for downloading the software package from the specified PURL,
      use this parameter to provide the username.
      Cannot be used with bearer-token.

auth-pass	string
    If authentication is required for downloading the software package from the specified PURL,
      use this parameter to provide the password.
    Cannot be used with bearer-token.

bearer-token string
    Example: "Bearer <token>"
    If token-based authentication is required for downloading the software package from the specified PURL,
      use this parameter to provide a Bearer token.
    Cannot be used with auth-user and auth-pass.

"""

import logging
from typing import (
    Any,
)

from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsPurlImport(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    @staticmethod
    def qp_purl_import(
        *,
        what: str,
        **qp: Any,
    ) -> dict[str, Any]:
        r: dict[str, Any] = {}

        version_qp: list[str] = [
            "replace",
            "force",
            "diff_with",
            #
            "product",
            "publisher",
            "category",
            "license",
            #
            "platform",
            "release_date",
            "max_size",
        ]

        if what in ["version"]:  # only supported for version level commands
            for k in version_qp:
                if k in qp:
                    r[k] = qp[k]

        # force; Will be ignored if build=repro.
        # diff_with; Will be ignored if build=repro.
        # let the portal handle all other validations (max len, enum valid, ...)

        return r

    def purl_import(  # pylint: disable=too-many-arguments
        self,
        *,
        project: str,
        package: str,
        version: str,
        purl: str,
        auth_user: str | None = None,
        auth_pass: str | None = None,
        bearer_token: str | None = None,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Any:
        """Action:
            execute a url-import() API call
            to import a file from a url and scan it, creating a version
            in a Portal project and package.

        Args: (organization and group go via the initial url connect)
         - project: str, mandatory.
         - package: str, mandatory.
         - version: str, mandatory.
         - purl: str, mandatory.

         - auth_user: str, optional.
         - auth_pass: str, optional.
         - bearer_token: str, optional.

         - auto_adapt_to_throttle: bool, default False, optional.
         - qp: Dict[str,Any] , optional.

        Return:
            The 'requests.result' of the url-import API call.

        Raises:
            May raise exceptions on issues with the HTTP connection or wrong parameters.
            - SpectraAssureInvalidAction: our exception.
            - <any other exception> from requests.get().

        QueryParameters:
            scan supports the following query parameters:
             - replace      #  see note-1.
             - force,       #  see note-2.
             - diff_with,   #  Will be ignored if build=repro.

             - product
             - publisher
             - category
             - license

             - platform
             - release_date
             - max_size

        note-1:
            If re-scanning the same file/version, use 'replace'.

        note-2
            If you have reached the max amount of versions allowed on the Portal,
              use 'force' to delete the oldest version and make room for the new one.
              Will be ignored if build=repro.

        """
        action = "purl_import"
        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        supported = ["version"]
        if what not in supported:
            msg = f"'{action}' is only supported for {'and '.join(supported)}"
            raise SpectraAssureInvalidAction(message=msg)

        # string <purl> <= 4096 characters
        # Example: "pkg:pypi/pyaudio@0.2.13?artifact=PyAudio-0.2.13-cp311-cp311-win_amd64.whl"
        if not purl.lower().startswith("pkg:"):
            msg = f"'{action}' no 'pkg:' in '{purl}'; purl must start with 'pkg:'"
            raise SpectraAssureInvalidAction(message=msg)

        valid_qp: dict[str, Any] = self.qp_purl_import(
            what=what,
            **qp,
        )
        xurl = self._make_current_url(
            action=action,
            project=project,
            package=package,
            version=version,
        )

        """
        purl string; mandatory;
        auth-user string; optional;
        auth-pass string; optional;
        bearer-token string; optional;
        """
        data: dict[str, Any] = {
            "purl": purl,
        }

        if auth_user:
            data["auth-user"] = auth_user
        if auth_pass:
            data["auth-pass"] = auth_pass
        if bearer_token:
            data["bearer-token"] = bearer_token

        return self.do_it_post(
            action=action,
            url=xurl,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            post_data=data,
            **valid_qp,
        )

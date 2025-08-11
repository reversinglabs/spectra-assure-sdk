"""
# URL-IMPORT

- https://{portalUrl}/api/public/v1/url-import/{organization}/{group}/pkg:rl/{project}/{package}@{version}

## query Parameters

max_size integer;
The maximum file size that the Portal will attempt to download from the specified URL, in bytes.
Keep in mind that the file size estimate before the download starts can be unreliable.

replace boolean; Default: false
This optional parameter lets you replace (overwrite) an already existing package version
  in the project with the package version you're uploading.
This functionality is equivalent to the --replace option in the rl-secure scan command.
If this parameter is set to false and the package version you're trying to upload
  already exists in the specified project,
  the API returns the 409 error response.

force boolean; Default: false
In the Portal, a package can only have a limited amount of versions.
If a package already has the maximum number of versions,
  you can use this optional parameter to specify if the oldest version of the package should be deleted
  to make space for the version you're uploading.
If this parameter is set to false and the package already has the maximum allowed number of versions,
  the API returns the 400 error response.
Will be ignored if build=repro.

diff_with string; Example: diff_with=1.1.0
This optional parameter lets you specify a previous package version
  against which you want to compare (diff) the version you're uploading.
The specified version must exist in the package.
This functionality is equivalent to the --diff-with option in the rl-secure report command.
Will be ignored if build=repro.

product string (VersionMetadataProduct) ; max: 200; Example: product=Example application
Software product name

publisher string (VersionMetadataPublisher); max 200; Example: publisher=Example software publisher
Software publisher

category string; Default: "Other" (Don't validate let the portal do that)
Categorization scheme for software based on their typical use or general purpose.

license string; Default: "Unknown"
Enum: 454 more (Don't validate let the portal do that)
SPDX-compliant license name under which the software is distributed.

platform string; Default: "Other"
Enum: (Don't validate let the portal do that)
Underlying technology or framework that the software has been developed to run on.

release_date string <date-time> (DateTime); Example: release_date=2022-07-15T13:57:39.843631Z

## Request Body

schema: application/json

url [required] string; format: <uri>; max 4096; Example: "https://example.com/downloads/example-file.exe"
  currently only http(s) is supported.

The URL from which you want to download and import a software package into the Portal.
If the URL is not valid or if there is no downloadable file at the specified location,
  the import will fail.

auth-user string; Example: "username"
If authentication is required for downloading the software package from the specified URL,
  use this parameter to provide the username.
Cannot be used with bearer-token.

auth-pass string <password>
If authentication is required for downloading the software package from the specified URL,
  use this parameter to provide the password.
Cannot be used with bearer-token.

bearer-token string; Example: "Bearer <token>"
If token-based authentication is required for downloading the software package from the specified URL,
  use this parameter to provide a Bearer token.
Cannot be used with auth-user and auth-pass.
"""

from typing import (
    Any,
    Dict,
    List,
)

import logging

from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)


from .base import SpectraAssureApiOperationsBase


logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsUrlImport(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes

    @staticmethod
    def qp_url_import(
        *,
        what: str,
        **qp: Any,
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {}

        version_qp: List[str] = [
            "max_size",
            "replace",
            "force",
            "diff_with",
            "product",
            "publisher",
            "category",
            "license",
            "platform",
            "release_date",
        ]

        if what in ["version"]:  # only supported for version level commands
            for k in version_qp:
                if k in qp:
                    r[k] = qp[k]

        # force; Will be ignored if build=repro.
        # diff_with; Will be ignored if build=repro.
        # let the portal handle all other validations (max len, enum valid, ...)

        return r

    def url_import(  # pylint: disable=too-many-arguments
        self,
        *,
        project: str,
        package: str,
        version: str,
        url: str,  # max len 4k; format uri :// should be present
        auth_user: str | None = None,
        auth_pass: str | None = None,
        bearer_token: str | None = None,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Any:
        """
        Action:
            execute a url-import() API call
            to import a file from a url and scan it, creating a version
            in a Portal project and package.

        Args:
         - project: str, mandatory.
         - package: str, mandatory.
         - version: str, mandatory.
         - url: str, mandatory, max 4k, must_contain '://'.
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
             - max_size
             - replace      #  see note-1.
             - force,       #  see note-2.
             - diff_with,   #  Will be ignored if build=repro.
             - product
             - publisher
             - category
             - license
             - platform
             - release_date

        note-1:
            If re-scanning the same file/version, use 'replace'.

        note-2
            If you have reached the max amount of versions allowed on the Portal,
              use 'force' to delete the oldest version and make room for the new one.
              Will be ignored if build=repro.
        """

        action = "url_import"
        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        supported = ["version"]
        if what not in supported:
            msg = f"'{action}' is only supported for {'and '.join(supported)}"
            raise SpectraAssureInvalidAction(message=msg)

        if "://" not in url:
            msg = f"'{action}' no '://' in '{url}'; url must be in uri format '<proto>://<host>[:<port>]/<path>'"
            raise SpectraAssureInvalidAction(message=msg)

        valid_qp: Dict[str, Any] = self.qp_url_import(
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
        url string; mandatory;
        auth-user string; optional;
        auth-pass string; optional;
        bearer-token string; optional;
        """
        data: Dict[str, Any] = {
            "url": url,
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

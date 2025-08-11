from typing import (
    Any,
    Dict,
    List,
)

import os
import logging

from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)


from .base import SpectraAssureApiOperationsBase


logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsScan(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes

    @staticmethod
    def qp_scan(
        *,
        what: str,
        **qp: Any,
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {}

        version_qp: List[str] = [
            "build",
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

        if what in ["version"]:
            for k in version_qp:
                if k in qp:
                    r[k] = qp[k]

        # force    # This parameter is incompatible with build=repro.
        # diff_with    # This parameter is incompatible with build=repro.
        if "build" in r and r["build"].lower() == "repro":
            invalid_list = ["force", "diff_with"]
            for k in invalid_list:
                if k in r:
                    msg = f"'scan' query parameter {k} cannot be combined with 'build=repro'"
                    raise SpectraAssureInvalidAction(message=msg)

        return r

    def scan(  # pylint: disable=too-many-arguments
        self,
        *,
        project: str,
        package: str,
        version: str,
        file_path: str,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Any:
        """
        Action:
            execute a scan() API call
            to upload a file and scan it, creating a version
            in a Portal project and package.

        Args:
         - project: str, mandatory.
         - package: str, mandatory.
         - version: str, mandatory.
         - file_path: str, mandatory, must exist for files, but not for url or purl.
         - auto_adapt_to_throttle: bool, default False, optional.
         - qp: Dict[str,Any] , optional.

        Return:
            The 'requests.result' of the scan API call.

        Raises:
            May raise exceptions on issues with the HTTP connection or wrong parameters.
            - SpectraAssureInvalidAction: our exception.
            - <any other exception> from requests.get().

        QueryParameters:
            scan supports the following query parameters:
             - build
             - replace
             - force,       cannot be combined with 'build=repro'
             - diff_with,   cannot be combined with 'build=repro'
             - product
             - publisher
             - category
             - license
             - platform
             - release_date

            If re-scanning the same file/version, use 'replace'.
            If you have reached the max amount of versions allowed on the Portal,
              use 'force' to delete the oldest version and make room for the new one.
        """

        action = "scan"
        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        supported = ["version"]
        if what not in supported:
            msg = f"'{action}' is only supported for {'and '.join(supported)}"
            raise SpectraAssureInvalidAction(message=msg)

        if not (os.path.isfile(file_path) and os.access(file_path, os.R_OK)):
            msg = f"'{action}' needs the specified file '{file_path}' to exist and be readable"
            raise SpectraAssureInvalidAction(message=msg)

        valid_qp: Dict[str, Any] = self.qp_scan(
            what=what,
            **qp,
        )
        url = self._make_current_url(
            action=action,
            project=project,
            package=package,
            version=version,
        )

        return self.do_it_post(
            action=action,
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            file_path=file_path,
            **valid_qp,
        )

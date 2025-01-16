import logging
from pathlib import Path

from typing import Any, Dict, Tuple

from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)
from spectra_assure_api_client.communication.downloader import UrlDownloader
from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsRlSafe(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    @staticmethod
    def qp_report(
        what: str,
        **qp: Any,
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {}
        if what in ["version"]:
            for k in ["build"]:
                if k in qp:
                    r[k] = qp[k]
        return r

    def rl_safe(  # pylint: disable=too-many-arguments
        self,
        *,
        project: str,
        package: str,
        version: str,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Any:
        """
        https://docs.secure.software/api-reference/#tag/Version/operation/getRlSafeVersionArchive

        Action:
            Execute a pack/safe api call
            for the specified 'project/package@version'

        Args:
         - project: str, mandatory.
         - package: str, mandatory.
         - version: str, mandatory.

         - auto_adapt_to_throttle: bool, default False, optional.
         - qp: Dict[str,Any] , optional.
            build: Default: "version"; Enum: "repro" "version"

        Return:
            The 'requests.result' of the report API call.
            See Notes for the expected response format.

        Raises:
            May raise exceptions on issues with the HTTP connection or wrong parameters.
            - SpectraAssureInvalidAction: our exception.
            - <any other exception> from requests.get().

        QueryParameters:
            report supports one query parameter:
             -  build: Default: "version"; Enum: "repro" "version"

        Notes:
            This will return a download url for the rl-safe archive (with limited validity)
        """

        action = "rl_safe"
        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        supported = ["version"]
        if what not in supported:
            msg = f"'{action}' is only supported for {'and '.join(supported)}"
            raise SpectraAssureInvalidAction(message=msg)

        valid_qp: Dict[str, Any] = self.qp_report(
            what=what,
            **qp,
        )
        url = self._make_current_url(
            action=action,
            project=project,
            package=package,
            version=version,
        )
        return self.do_it_get(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **valid_qp,
        )

    def rl_safe_download(
        self,
        *,
        target_dir: str,
        project: str,
        package: str,
        version: str,
        auto_adapt_to_throttle: bool = False,
        rename_archive: bool = True,
        **qp: Any,
    ) -> Tuple[bool, str]:
        """
        Download a rl-safe archive

        - by default rename it to <project>/<package>@<version>.rl-safe in the target_dir
        - always overwrite

        Return: Tuple[downloaded: bool, file_path: str]
            If downloaded is False, we dod not download the file,

            If downloaded is True, we downloaded the file,
                we report the resulting file path

        return the path of the archive
        """

        data = self.rl_safe(
            project=project,
            package=package,
            version=version,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )
        logger.debug("rl-_safe return data: %s", data)
        download_url = data.json().get("download_link")

        ud = UrlDownloader(
            target_dir=target_dir,
            with_overwrite_existing_files=True,
            with_verify_after_download=False,
            with_verify_existing_files=False,
        )
        download_ok, file_path = ud.download_file_from_url(
            download_url=download_url,
            hashes={},  # a rl-safe archive has no digest so there is no need for verify
        )

        if download_ok is False:
            return download_ok, file_path

        if rename_archive is False:
            return download_ok, file_path

        # rename the archive to the purl.rl-safe
        purl = f"{project}/{package}@{version}"
        new_file_name = f"{target_dir}/{purl}.rl-safe"

        z = f"{target_dir}/{project}"
        p = Path(z)
        if p.exists() and not p.is_dir():
            return False, f"item {z} exists but is not a directory, cannot create {new_file_name}"

        if not p.exists():
            p.mkdir()

        f = Path(file_path)
        f.rename(new_file_name)
        return download_ok, new_file_name

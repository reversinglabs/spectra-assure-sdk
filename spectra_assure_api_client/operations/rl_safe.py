import logging
import os
from pathlib import Path
from typing import Any

import requests

from spectra_assure_api_client.communication.downloader import UrlDownloader
from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)

from .base import SpectraAssureApiOperationsBase
from .constants import _ARCHIVE_MAX_WAIT

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsRlSafe(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def rl_safe(  # pylint: disable=too-many-arguments
        self,
        *,
        project: str,
        package: str,
        version: str,
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,
    ) -> requests.Response:

        action = "rl_safe"
        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        supported = ["version"]
        if what not in supported:
            msg = f"'{action}' is only supported for {' and '.join(supported)}"
            raise SpectraAssureInvalidAction(message=msg)

        # rl_safe's own query parameters, from the specification; it used to
        # borrow the report action's list, which matched only by coincidence.
        valid_qp: dict[str, Any] = self._accepted_query("rl_safe", what, qp)
        url = self._make_current_url(
            action=action,
            project=project,
            package=package,
            version=version,
        )
        return self._do_it_get(
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
        auto_adapt_to_throttle: bool | None = None,
        rename_archive: bool = True,
        max_wait_time_for_archive: int = _ARCHIVE_MAX_WAIT,
        **qp: Any,
    ) -> tuple[bool, str]:
        """Download the RL-SAFE archive of a version to `target_dir`.

        While the analysis is still running the API answers 202 and no archive
        exists yet. That is a normal step, not a failure, so this waits up to
        `max_wait_time_for_archive` seconds for the archive to become available
        (pass 0 to fail on the first 202), as `filestream_rl_safe_download` does.
        `rl_safe` itself returns the response as it is, 202 included.
        """
        data = self._wait_for_rl_safe_archive(
            fetch=lambda: self.rl_safe(
                project=project,
                package=package,
                version=version,
                auto_adapt_to_throttle=auto_adapt_to_throttle,
                **qp,
            ),
            what=f"{project}/{package}@{version}",
            max_wait_time=max_wait_time_for_archive,
        )
        logger.debug("rl-safe return data: %s", data)

        download_url = data.json().get("download_link")
        if not download_url:
            msg = "missing download url in rl-safe download request"
            raise SpectraAssureInvalidAction(message=msg)

        ud = UrlDownloader(
            target_dir=target_dir,
            with_overwrite_existing_files=True,
            with_verify_after_download=False,
            with_verify_existing_files=False,
            no_ssl_verify=bool(self.no_ssl_verify),
            proxies=self.proxies,
            session=self.session,
            read_timeout=self.read_timeout,
            connect_timeout=self.connect_timeout,
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
            return (
                False,
                f"item {z} exists but is not a directory, cannot create {new_file_name}",
            )

        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)

        # os.replace overwrites an existing file on every platform. Path.rename
        # only does on Unix and raises FileExistsError on Windows, which made the
        # re-download of an archive fail there.
        os.replace(file_path, new_file_name)
        return download_ok, new_file_name

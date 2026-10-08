"""File Stream operations.

File Stream files are standalone:
they belong to no project, package or version,
and a server-generated `file_id` is the only handle.
Everything here is therefore kept apart from the purl-based calls
 -- different methods, different arguments, no shared ladder --
rather than being folded into them behind optional parameters.

Three differences from the purl endpoints are worth knowing:

* `reason` is mandatory on approve, reject and revoke, and on the purl
  equivalents too. Here it is a named argument rather than part of `**qp`,
  and an empty one is refused.
* `version` is metadata, not a path segment.
  It rides along as a query parameter on the three calls that create a file.
* Reports are one operation with the type in the path; the API lists eight
  types, and `rl-diff` is not among them: File Stream holds no versions to
  diff against.
"""

from __future__ import annotations

import logging
import os
import time
from typing import (
    Any,
)

import requests

from spectra_assure_api_client.communication.download_criteria import (
    SpectraAssureDownloadCriteria,
)
from spectra_assure_api_client.communication.downloader import UrlDownloader
from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
    SpectraAssureInvalidPath,
    SpectraAssureNoDownloadUrlInResult,
    SpectraAssureUnexpectedNoDataFound,
)
from spectra_assure_api_client.spec import (
    FILESTREAM_REPORT_OPERATIONS,
    SpectraAssureSpecError,
    resolve_filestream_report,
)

from .base import SpectraAssureApiOperationsBase
from .constants import (
    _ANALYSIS_FINISHED,
    _APPROVED_STATUSES,
    _ARCHIVE_MAX_WAIT,
    _LOOKUP_MAX_PAGES,
    _LOOKUP_PAGE_SIZE,
)

logger = logging.getLogger(__name__)

WHAT = "filestream"


class SpectraAssureApiOperationsFilestream(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):
    """The File Stream half of the public surface."""

    # ------------------------------------------------------------- helpers

    def _filestream_url(self, action: str, file_id: str | None = None) -> str:
        operation = self._resolve(action, WHAT)
        values = {"file_id": file_id} if file_id is not None else {}
        return self._url_for(operation, **values)

    def _filestream_params(self, action: str, qp: dict[str, Any]) -> dict[str, Any]:
        # Query parameters only. Every File Stream call builds its body from
        # named arguments, and `_accepted` would also keep body fields: a body
        # field passed in **qp, such as `auth-pass`, was sent in the URL.
        return self._accepted_query(action, WHAT, qp)

    # ------------------------------------------------------------ creating

    def filestream_scan(
        self,
        *,
        file_path: str,
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,
    ) -> requests.Response:
        """Upload a file to the File Stream and start its analysis.

        The response carries the server-generated id, under `id`, which every
        other File Stream call needs.
        """
        action = "filestream_scan"

        if not (os.path.isfile(file_path) and os.access(file_path, os.R_OK)):
            msg = f"'{action}' needs the specified file '{file_path}' to exist and be readable"
            raise SpectraAssureInvalidAction(message=msg)

        return self._post(
            action=action,
            url=self._filestream_url(action),
            body="file",
            file_path=file_path,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **self._filestream_params(action, qp),
        )

    def filestream_url_import(
        self,
        *,
        url: str,
        auth_user: str | None = None,
        auth_pass: str | None = None,
        bearer_token: str | None = None,
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,
    ) -> requests.Response:
        """Import a file into the File Stream from a URL."""
        action = "filestream_url_import"

        body = self._import_body(
            action=action,
            key="url",
            value=url,
            auth_user=auth_user,
            auth_pass=auth_pass,
            bearer_token=bearer_token,
        )

        return self._post(
            action=action,
            body="json",
            url=self._filestream_url(action),
            post_data=body,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **self._filestream_params(action, qp),
        )

    def filestream_purl_import(
        self,
        *,
        purl: str,
        auth_user: str | None = None,
        auth_pass: str | None = None,
        bearer_token: str | None = None,
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,
    ) -> requests.Response:
        """Import a file into the File Stream from a package URL."""
        action = "filestream_purl_import"

        body = self._import_body(
            action=action,
            key="purl",
            value=purl,
            auth_user=auth_user,
            auth_pass=auth_pass,
            bearer_token=bearer_token,
        )

        return self._post(
            action=action,
            body="json",
            url=self._filestream_url(action),
            post_data=body,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **self._filestream_params(action, qp),
        )

    # ------------------------------------------------------------ querying

    def filestream_list(
        self,
        *,
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,
    ) -> requests.Response:
        """List the files in the group's File Stream.

        Accepts the filters the specification declares: `approval_status`,
        `deleted_in_days`, `file_name`, `limit`, `offset`, `sort_by` and `user`.
        """
        action = "filestream_list"
        return self._do_it_get(
            url=self._filestream_url(action),
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **self._filestream_params(action, qp),
        )

    def filestream_status(
        self,
        *,
        file_id: str,
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,
    ) -> requests.Response:
        """Analysis status for one File Stream file."""
        action = "filestream_status"
        return self._do_it_get(
            url=self._filestream_url(action, file_id),
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **self._filestream_params(action, qp),
        )

    def filestream_checks(
        self,
        *,
        file_id: str,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        """Checks performed on one File Stream file."""
        return self._do_it_get(
            url=self._filestream_url("filestream_checks", file_id),
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

    def filestream_report(
        self,
        *,
        file_id: str,
        report_type: str,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        """Export one report for a File Stream file.

        `report_type` takes the same spellings as the purl `report` call,
        minus `rl-diff`, which File Stream does not offer.
        """
        try:
            operation = resolve_filestream_report(report_type)
        except SpectraAssureSpecError as exc:
            raise SpectraAssureInvalidAction(message=str(exc)) from exc

        return self._do_it_get(
            url=self._url_for(operation, file_id=file_id, report_type=report_type.lower()),
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

    @staticmethod
    def filestream_report_types() -> list[str]:
        """The report types File Stream supports."""
        return sorted(FILESTREAM_REPORT_OPERATIONS)

    # ----------------------------------------------------------- lifecycle

    def filestream_sync(
        self,
        *,
        file_id: str,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        """Re-analyse a File Stream file, for instance after an engine update."""
        return self._post(
            action="filestream_sync",
            url=self._filestream_url("filestream_sync", file_id),
            body="none",
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

    def filestream_delete(
        self,
        *,
        file_id: str,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        """Remove a file from the File Stream."""
        return self._do_it_delete(
            url=self._filestream_url("filestream_delete", file_id),
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

    def _approval(
        self,
        *,
        action: str,
        file_id: str,
        reason: str,
        auto_adapt_to_throttle: bool | None,
    ) -> requests.Response:
        if not reason:
            # Mandatory per the specification, unlike the purl equivalents.
            msg = f"'{action}' requires a non-empty 'reason'"
            raise SpectraAssureInvalidAction(message=msg)

        return self._do_it_put(
            url=self._filestream_url(action, file_id),
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            reason=reason,
        )

    def filestream_approve(
        self,
        *,
        file_id: str,
        reason: str,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        """Approve a File Stream file. `reason` is required."""
        return self._approval(
            action="filestream_approve",
            file_id=file_id,
            reason=reason,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

    def filestream_reject(
        self,
        *,
        file_id: str,
        reason: str,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        """Reject a File Stream file. `reason` is required."""
        return self._approval(
            action="filestream_reject",
            file_id=file_id,
            reason=reason,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

    def filestream_revoke(
        self,
        *,
        file_id: str,
        reason: str,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        """Revoke a previously approved File Stream file. `reason` is required."""
        return self._approval(
            action="filestream_revoke",
            file_id=file_id,
            reason=reason,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

    # ----------------------------------------------------------- downloads

    def filestream_rl_safe(
        self,
        *,
        file_id: str,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        """Request a download link for the file's rl-safe archive."""
        return self._do_it_get(
            url=self._filestream_url("filestream_rl_safe", file_id),
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

    def _filestream_wait_for_rl_safe(
        self,
        *,
        file_id: str,
        max_wait_time: int,
        auto_adapt_to_throttle: bool | None = None,
    ) -> requests.Response:
        """Request the rl-safe archive, waiting while the analysis is still running.

        The wait itself is shared with the project/package/version archives.
        """
        return self._wait_for_rl_safe_archive(
            fetch=lambda: self.filestream_rl_safe(
                file_id=file_id,
                auto_adapt_to_throttle=auto_adapt_to_throttle,
            ),
            what=file_id,
            max_wait_time=max_wait_time,
        )

    def filestream_rl_safe_download(
        self,
        *,
        target_dir: str,
        file_id: str,
        auto_adapt_to_throttle: bool | None = None,
        rename_archive: bool = True,
        max_wait_time_for_archive: int = _ARCHIVE_MAX_WAIT,
    ) -> tuple[bool, str]:
        """Fetch the rl-safe archive for a File Stream file to `target_dir`.

        While the analysis is still running the API answers 202 and no archive exists yet.
        Rather than failing, this waits up to `max_wait_time_for_archive` seconds for it to become available.
        Pass 0 to fail immediately instead.
        """
        data = self._filestream_wait_for_rl_safe(
            file_id=file_id,
            max_wait_time=max_wait_time_for_archive,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

        download_url = data.json().get("download_link")
        if not download_url:
            msg = "missing download url in rl-safe download request"
            raise SpectraAssureInvalidAction(message=msg)

        downloader = UrlDownloader(
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
        download_ok, file_path = downloader.download_file_from_url(
            download_url=download_url,
            hashes={},  # an rl-safe archive carries no digest to verify against
        )

        if download_ok is False or rename_archive is False:
            return download_ok, file_path

        # There is no purl to name the archive after, so the file id is used.
        new_file_name = os.path.join(target_dir, f"{file_id}.rl-safe")
        os.replace(file_path, new_file_name)
        return download_ok, new_file_name

    def _filestream_find_in_list(
        self,
        *,
        file_id: str,
        auto_adapt_to_throttle: bool | None = None,
    ) -> dict[str, Any] | None:
        """Find one file's list entry, for the fields status does not carry.

        `approval_status` appears in the list response but not in the status
        response, and there is no endpoint that fetches a single file's
        metadata, so the list is paged through until the id turns up.
        """
        for page in range(_LOOKUP_MAX_PAGES):
            response = self.filestream_list(
                auto_adapt_to_throttle=auto_adapt_to_throttle,
                limit=_LOOKUP_PAGE_SIZE,
                offset=page * _LOOKUP_PAGE_SIZE,
            )
            if response.status_code != 200:
                msg = f"NO DATA FOUND with filestream_list :: {response.status_code} {response.text}"
                raise SpectraAssureUnexpectedNoDataFound(msg)

            files = response.json().get("files") or []
            for item in files:
                if item.get("id") == file_id:
                    return dict(item)

            if len(files) < _LOOKUP_PAGE_SIZE:
                return None

        logger.warning(
            "gave up looking for %s after %d pages of filestream_list",
            file_id,
            _LOOKUP_MAX_PAGES,
        )
        return None

    def _filestream_wait_for_analysis(
        self,
        *,
        file_id: str,
        criteria: SpectraAssureDownloadCriteria,
        auto_adapt_to_throttle: bool | None = None,
    ) -> dict[str, Any]:
        """Poll status until the analysis is done, or the budget runs out."""
        max_time = criteria.max_wait_time_for_scan_done
        step_time = min(
            max(int(max_time / 5), 10),
            30,
        )
        current_time = 0

        while True:
            response = self.filestream_status(
                file_id=file_id,
                auto_adapt_to_throttle=auto_adapt_to_throttle,
            )
            if response.status_code != 200:
                msg = f"NO DATA FOUND with filestream_status({file_id}) :: {response.status_code} {response.text}"
                raise SpectraAssureUnexpectedNoDataFound(msg)

            data = response.json()
            info: dict[str, Any] = {
                "analysis": self._get_path(path="analysis/status", data=data),
                "hashes": self._get_path(path="analysis/report/info/file/hashes", data=data),
            }
            if isinstance(info["analysis"], str):
                info["analysis"] = info["analysis"].lower()

            if criteria.wait_for_scan_done is False:
                return info

            # Stop on a finished analysis, failed ones included (I-44).
            if info["analysis"] in _ANALYSIS_FINISHED:
                return info

            if current_time > max_time:
                return info

            logger.info(
                "waiting for analysis to finish on %s (max %ds, current %ds)",
                file_id,
                max_time,
                current_time,
            )

            time.sleep(step_time)
            current_time += step_time

    def filestream_download(
        self,
        *,
        target_dir: str,
        file_id: str,
        auto_adapt_to_throttle: bool | None = None,
        download_criteria: SpectraAssureDownloadCriteria | None = None,
    ) -> dict[str, dict[str, Any]] | None:
        """Download one File Stream file to `target_dir`.

        The File Stream counterpart of `download`. There is no version ladder to
        search, so the criteria that pick between candidate versions do not
        apply; `wait_for_scan_done`, `must_be_approved` and the verification and
        overwrite settings all do.

        Returns a single-entry mapping keyed by `file_id`, or None if the file
        was skipped. The shape matches `download` so callers can treat the two
        alike.
        """
        criteria = download_criteria or SpectraAssureDownloadCriteria()

        target_dir_posix = self._simple_path_to_posix(target_path=target_dir)
        exists, what = self._exists_posix_path(item_path=target_dir_posix)
        if exists is False:
            msg = f"the target directory you specified does not exist; {target_dir_posix}"
            logger.critical(msg)
            raise SpectraAssureInvalidPath(msg)
        if what != "D":
            msg = f"the target you specified is not directory; {target_dir_posix}"
            logger.critical(msg)
            raise SpectraAssureInvalidPath(msg)

        info = self._filestream_wait_for_analysis(
            file_id=file_id,
            criteria=criteria,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

        if info.get("analysis") != "done":
            if info.get("analysis") == "error":
                logger.warning("the analysis of %s ended in an error; it will be skipped", file_id)
            else:
                logger.info("%s has not finished processing; it will be skipped", file_id)
            return None

        if criteria.must_be_approved is True:
            entry = self._filestream_find_in_list(
                file_id=file_id,
                auto_adapt_to_throttle=auto_adapt_to_throttle,
            )
            approval = (entry or {}).get("approval_status")
            if not isinstance(approval, str) or approval.lower() not in _APPROVED_STATUSES:
                logger.info(
                    "%s has approval status %r; it will be skipped",
                    file_id,
                    approval,
                )
                return None
            info["approved"] = approval.lower()

        # The download link is only requested once the file is a real candidate:
        # every request for one draws on the group's download capacity.
        status = self.filestream_status(
            file_id=file_id,
            auto_adapt_to_throttle=self._link_request_throttle(auto_adapt_to_throttle),
            download=True,
        )
        if status.status_code >= 300 or status.status_code < 200:
            msg = self._link_request_failure(status.status_code, file_id)
            logger.error(msg)
            raise SpectraAssureUnexpectedNoDataFound(msg)

        payload = status.json()
        download_url = self._get_path(
            path="analysis/report/info/portal/download",
            data=payload,
        )
        if download_url is None:
            msg = f"no download URL from status for {file_id}"
            logger.error(msg)
            raise SpectraAssureNoDownloadUrlInResult(msg)

        hashes = self._get_path(path="analysis/report/info/file/hashes", data=payload) or []

        downloader = UrlDownloader(
            target_dir=target_dir_posix,
            with_verify_existing_files=criteria.with_verify_existing_files,
            with_verify_after_download=criteria.with_verify_after_download,
            with_overwrite_existing_files=criteria.with_overwrite_existing_files,
            no_ssl_verify=bool(self.no_ssl_verify),
            proxies=self.proxies,
            session=self.session,
            read_timeout=self.read_timeout,
            connect_timeout=self.connect_timeout,
        )
        download_status, target_file_path = downloader.download_file_from_url(
            download_url=download_url,
            hashes=self._extract_hashes(hashes),
        )

        info["hashes"] = self._extract_hashes(hashes)
        info["downloaded"] = download_status
        info["target_file_path"] = os.path.realpath(target_file_path)

        return {file_id: info}

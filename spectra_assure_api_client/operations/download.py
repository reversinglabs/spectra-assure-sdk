import logging
import os
import time
from typing import (
    Any,
    Dict,
    List,
    Tuple,
)

from spectra_assure_api_client.communication.download_criteria import SpectraAssureDownloadCriteria
from spectra_assure_api_client.communication.downloader import UrlDownloader
from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
    SpectraAssureInvalidPath,
    SpectraAssureUnexpectedNoDataFound,
    SpectraAssureNoDownloadUrlInResult,
    SpectraAssureUnsupportedStrategy,
)
from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsDownload(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):

    def _prep_criteria(
        self,
        download_criteria: SpectraAssureDownloadCriteria | None = None,
    ) -> None:
        # pylint: disable=attribute-defined-outside-init
        self.download_criteria = SpectraAssureDownloadCriteria()  # start with a default
        if download_criteria:
            self.download_criteria = download_criteria

        self.download_criteria.must_be_approved = True  # OVERRIDE must_be_approved = True
        logger.info("download_criteria: %s", download_criteria)

    def _validate_target_dir(self, target_dir: str) -> str:
        target_dir_posix = self.simple_path_to_posix(target_path=target_dir)
        exists, what = self.exists_posix_path(item_path=target_dir_posix)

        if exists is False:
            msg = f"the target directory you specified does not exist; {target_dir_posix}"
            logger.critical(msg)
            raise SpectraAssureInvalidPath(msg)

        if what != "D":
            msg = f"the target you specified is not directory; {target_dir_posix}"
            logger.critical(msg)
            raise SpectraAssureInvalidPath(msg)

        return target_dir_posix

    # pylint: disable=too-many-arguments
    def _do_one_download(
        self,
        *,
        project: str,
        package: str,
        version: str,
        ud: UrlDownloader,
        info: Dict[str, Dict[str, Any]],
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Tuple[bool, str]:

        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        # if we need to download, request the download link
        qp_status = self.qp_status(
            what=what,
            **qp,
        )
        qp_status["download"] = True

        data = self.status(
            project=project,
            package=package,
            version=version,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp_status,
        )

        if data.status_code >= 300 or data.status_code < 200:
            msg = f"we get {data.status_code} from status lookup for {project}/{package}@{version}"
            logger.error(msg)
            raise SpectraAssureUnexpectedNoDataFound(msg)

        download_url = self._get_path(
            path="analysis/report/info/portal/download",
            data=data.json(),
        )
        if download_url is None:
            msg = f"no download URL from status for {project}/{package}@{version}"
            logger.error(msg)
            raise SpectraAssureNoDownloadUrlInResult(msg)

        download_status, target_file_path = ud.download_file_from_url(
            download_url=download_url,
            hashes=info["hashes"],
        )

        if download_status is True:
            logger.info("targetFile: %s", target_file_path)

        return download_status, target_file_path

    def _process_candidates(  # pylint: disable=too-many-arguments
        self,
        *,
        project: str,
        package: str,
        chosen: Dict[str, Dict[str, Any]],
        target_dir: str,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Dict[str, Dict[str, Any]]:
        # create a UrlDownloader to do the actual download
        ud = UrlDownloader(
            target_dir=target_dir,
            with_verify_existing_files=self.download_criteria.with_verify_existing_files,
            with_verify_after_download=self.download_criteria.with_verify_after_download,
            with_overwrite_existing_files=self.download_criteria.with_overwrite_existing_files,
        )

        for version_, info in chosen.items():
            logger.info("try download: version %s, with info: %s", version_, info)

            download_status, target_file_path = self._do_one_download(
                project=project,
                package=package,
                version=version_,
                info=info,
                ud=ud,
                auto_adapt_to_throttle=auto_adapt_to_throttle,
                **qp,
            )

            chosen[version_]["target_file_path"] = os.path.realpath(target_file_path)
            chosen[version_]["downloaded"] = download_status

        return chosen

    def _list(
        self,
        *,
        project: str,
        package: str,
        version: str | None = None,
        with_sort: bool = True,
        auto_adapt_to_throttle: bool = False,
    ) -> List[str]:

        data = self.list(
            project=project,
            package=package,
            version=version,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

        if data.status_code != 200:
            msg = f"NO DATA FOUND with list({project},{package},{version}) :: {data.status_code} {data.text}"
            raise SpectraAssureUnexpectedNoDataFound(msg)

        return self._flatten_list(
            data.json(),
            multiple="versions",
            single="version",
            with_sort=with_sort,
        )

    def _find_versions_from_project_and_package(
        self,
        *,
        project: str,
        package: str,
        auto_adapt_to_throttle: bool = False,
    ) -> List[str]:
        version_list: List[str] = []

        for version in self._list(
            project=project,
            package=package,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        ):
            version_list.append(version)

        return version_list

    def _make_initial_info_dict_on_all_versions_in_this_package(
        self,
        *,
        project: str,
        package: str,
        version: str | None = None,
        auto_adapt_to_throttle: bool = False,
    ) -> Dict[str, Dict[str, Any]]:
        info_dict: Dict[str, Dict[str, Any]] = {}

        if version is not None:
            logger.debug("we have a version as argument, return that")
            info_dict[version] = {}
            return info_dict

        logger.debug("we have no version, find all versions for this project/package")
        version_list = self._find_versions_from_project_and_package(
            project=project,
            package=package,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

        for version_ in version_list:
            info_dict[version_] = {}

        return info_dict

    def _update_skip_list(  # pylint: disable=too-many-arguments
        self,
        *,
        project: str,
        package: str,
        version: str,
        skip: List[str],
        info_dict: Dict[str, Dict[str, Any]],
    ) -> None:
        if info_dict[version]["analysis"].lower() != "done":
            # waiting on 'done', was already completed while fetching the VersionStatus data
            msg = f"{project}/{package}@{version} has not yet finished processing; it will be skipped"
            if version not in skip:
                skip.append(version)
                logger.info(msg)
            return

        if self.download_criteria.must_be_approved is True:
            msg = f"{project}/{package}@{version} has not been approved; it will be skipped"
            if info_dict[version]["approved"].lower() != "approved":
                if version not in skip:
                    skip.append(version)
                    logger.info(msg)
                return

    @staticmethod
    def _update_time_for_repeat(
        current_time: int,
        step_time: int,
        msg: str,
    ) -> int:
        logger.info(msg)
        time.sleep(step_time)
        current_time += step_time
        return current_time

    def _get_start_times_for_repeat(self) -> Tuple[int, int, int]:
        # prep time settings
        max_time = self.download_criteria.max_wait_time_for_scan_done

        step_time = int(self.download_criteria.max_wait_time_for_scan_done / 5)
        step_time = max(step_time, 10)
        if step_time > 60:
            step_time = 30

        current_time = 0

        return current_time, step_time, max_time

    def _get_info_status(
        self,
        *,
        project: str,
        package: str,
        version: str,
        auto_adapt_to_throttle: bool = False,
    ) -> Dict[str, Any]:
        a_dict: Dict[str, Any] = {}

        current_time, step_time, max_time = self._get_start_times_for_repeat()

        while True:
            data = self.status(
                project=project,
                package=package,
                version=version,
                auto_adapt_to_throttle=auto_adapt_to_throttle,
            )
            if data.status_code != 200:
                msg = f"NO DATA FOUND with status({project},{package},{version}) :: {data.status_code} {data.text}"
                raise SpectraAssureUnexpectedNoDataFound(msg)

            path_info: Dict[str, str] = {
                "analysis": "analysis/status",  # we are looking for "done"
                "quality": "analysis/report/info/statistics/quality/status",
                "hashes": "analysis/report/info/file/hashes",
            }
            for k, path in path_info.items():
                a_dict[k] = self._get_path(path=path, data=data.json())
                if a_dict[k] is not None and k != "hashes":
                    a_dict[k] = a_dict[k].lower()

            if self.download_criteria.wait_for_scan_done is False:
                return a_dict

            if a_dict["analysis"].lower() == "done":
                return a_dict
            # pylint: disable-next=line-too-long
            msg = (
                f"waiting for analysis to finish on: {project}/{package}@{version}"
                + " (max {max_time}s, current {current_time}s"
            )
            current_time = self._update_time_for_repeat(
                current_time,
                step_time,
                msg,
            )
            if current_time > max_time:
                return a_dict

    def _do_status(
        self,
        *,
        project: str,
        package: str,
        version: str,
        skip: List[str],  # pylint: disable=unused-argument
        info_dict: Dict[str, Dict[str, Any]],
        auto_adapt_to_throttle: bool = False,
    ) -> None:
        a_dict = self._get_info_status(
            project=project,
            package=package,
            version=version,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

        for k, v in a_dict.items():
            info_dict[version][k] = v

    def _remove_skipped_versions_from_result(
        self,
        *,
        info_dict: Dict[str, Any],
        skip: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        result_dict: Dict[str, Dict[str, Any]] = {}

        for version, info in info_dict.items():
            if version in skip:
                continue

            result_dict[version] = {}
            for k, v in info.items():
                result_dict[version][k] = v

                if k in ["hashes"]:
                    result_dict[version][k] = self._extract_hashes(v)

        logger.info("candidate versions after skip removal: %s", result_dict.keys())

        return result_dict

    # pylint: disable=too-many-arguments
    def _do_list(
        self,
        *,
        project: str,
        package: str,
        version: str,
        skip: List[str],  # pylint: disable=unused-argument
        info_dict: Dict[str, Dict[str, Any]],
        auto_adapt_to_throttle: bool = False,
    ) -> None:
        # get the data
        data = self.list(
            project=project,
            package=package,
            version=version,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )
        if data.status_code != 200:
            msg = f"NO DATA FOUND with list({project},{package},{version}) :: {data.status_code} {data.text}"
            raise SpectraAssureUnexpectedNoDataFound(msg)

        # process the data
        path_info: Dict[str, str] = {
            "approved": "approval_status",  # we are looking for "approved"
            "approval-stamp": "approval_information/timestamp",
            "released": "is_released",
        }

        a_dict: Dict[str, Any] = {}
        for k, path in path_info.items():
            a_dict[k] = self._get_path(path=path, data=data.json())
            if a_dict[k] is not None and isinstance(a_dict[k], str):
                a_dict[k] = a_dict[k].lower()

        for k, v in a_dict.items():
            info_dict[version][k] = v

    def _filter_latest_approved_version(
        self,
        *,
        temp_result_dict: Dict[str, Dict[str, Any]],
    ) -> str:
        # sort by latest approval timestamp

        tt: Dict[str, str] = {}
        for version, info in temp_result_dict.items():
            for k, v in info.items():
                if k == "approval-stamp" and v is not None:
                    tt[v] = version
        sorted_by_time = list(sorted(tt.keys()))

        latest_most_recent = sorted_by_time[-1]  # let's assume this is actually unique
        latest_version_string = tt[latest_most_recent]

        msg = f"strategy {self.download_criteria.current_strategy} selected {latest_version_string}"
        logger.info(msg)

        return latest_version_string

    def _select_version_from_result(
        self,
        *,
        result_dict: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]] | None:
        assert self.download_criteria is not None

        if len(result_dict) == 0:
            msg = "no versions exist after filters have been applied"
            logger.info(msg)
            return None

        if len(result_dict) == 1:
            msg = f"the result for download has only one candidate {result_dict.keys()}"
            logger.info(msg)
            return result_dict

        if self.download_criteria.current_strategy.lower() == "AllApproved".lower():
            msg = f"used strategy {self.download_criteria.current_strategy} on {result_dict.keys()}"
            logger.info(msg)
            return result_dict

        if self.download_criteria.current_strategy.lower() == "LatestApproved_ByApprovalTimeStamp".lower():
            msg = f"used strategy {self.download_criteria.current_strategy} on {result_dict.keys()}"
            logger.info(msg)
            latest = self._filter_latest_approved_version(temp_result_dict=result_dict)
            return {latest: result_dict[latest]}

        msg = f"unsupported strategy {self.download_criteria.current_strategy}"
        logger.info(msg)
        raise SpectraAssureUnsupportedStrategy(msg)

    def _get_extended_info_versions(
        self,  # pylint: disable=unused-argument
        *,
        project: str,
        package: str,
        version: str | None = None,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Dict[str, Dict[str, Any]] | None:
        skip: List[str] = []

        info_dict = self._make_initial_info_dict_on_all_versions_in_this_package(
            project=project,
            package=package,
            version=version,  # may be None
            auto_adapt_to_throttle=auto_adapt_to_throttle,
        )

        # from now on version is no longer None
        for version_ in info_dict:
            logger.debug("%s/%s@%s", project, package, version_)
            self._do_status(
                project=project,
                package=package,
                version=version_,
                skip=skip,
                info_dict=info_dict,
                auto_adapt_to_throttle=auto_adapt_to_throttle,
            )
            self._do_list(
                project=project,
                package=package,
                version=version_,
                skip=skip,
                info_dict=info_dict,
                auto_adapt_to_throttle=auto_adapt_to_throttle,
            )

            self._update_skip_list(
                project=project,
                package=package,
                version=version_,
                skip=skip,
                info_dict=info_dict,
            )

        logger.info("candidate versions: %s", info_dict.keys())
        logger.info("skip list is: %s", skip)

        result_dict = self._remove_skipped_versions_from_result(
            info_dict=info_dict,
            skip=skip,
        )

        return self._select_version_from_result(
            result_dict=result_dict,
        )

    def _prep_candidates(
        self,
        *,
        target_dir: str,  # pylint: disable=unused-argument
        project: str,
        package: str,
        version: str | None = None,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Dict[str, Dict[str, Any]] | None:

        assert self.download_criteria is not None
        self.download_criteria.must_be_approved = True  # Force True, we only currently support approved versions

        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        supported = ["package", "version"]
        if what not in supported:
            msg = f"'download' is only supported for {'and '.join(supported)}"
            raise SpectraAssureInvalidAction(message=msg)

        valid_qp: Dict[str, Any] = self.qp_download(
            what=what,
            **qp,
        )

        return self._get_extended_info_versions(
            project=project,
            package=package,
            version=version,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **valid_qp,
        )

    # PUBLIC
    @staticmethod
    def qp_download(
        *,
        what: str,
        **qp: Any,
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {}
        if what in ["version"]:
            for k in ["build"]:
                if k in qp:
                    r[k] = qp[k]
        return r

    def download(  # pylint: disable=too-many-arguments
        self,
        *,
        target_dir: str,
        project: str,
        package: str,
        version: str | None = None,
        auto_adapt_to_throttle: bool = False,
        download_criteria: SpectraAssureDownloadCriteria | None = None,
        **qp: Any,
    ) -> Dict[str, Dict[str, Any]] | None:
        """
        Action: download

        Args:
         - target_dir: str, mandatory;
            The directory where the file will be downloaded; MUST exist.

         - project: str, mandatory;
            Project containing the version you want to download.

         - package: str, mandatory;
            Package containing the version you want to download.

         - version: str | None = None, optional;
            The version you want to download or
            None if you want to look at all available versions in the current project/package.
            (By default, only approved versions will be considered download candidates.)

         - auto_adapt_to_throttle: bool = False, optional;
            If a throttle response is received:
                you may want to use this option to automatically wait until the data becomes available.
                Otherwise, no download will take place and an exception will be raised.

         - download_criteria: SpectraAssureDownloadCriteria | None = None, optional;
            Specify exactly how the download should deal with e.g. verification,
            overwriting existing files in the target directory,
            and finding download candidates if the version is not specified.

         - qp: Dict[str,Any], optional;
            Additional query parameters to be used by status()
            while gathering information on download candidates.

        Returns:
         - Dict[str, Dict[str, Any]] | None
            If we cannot find any download candidates, we return None.
            Otherwise:
             - the key of the dict is the version string,
             - the value is a dict specifying all collected data during the selection and download.

        Raises:
            SpectraAssureInvalidAction: if the target for download is incorrect.
            SpectraAssureInvalidPath:   if there are issues with the target path.
            SpectraAssureUnexpectedNoDataFound: if a https.request did not return any data,
                but we expected data to arrive.
            SpectraAssureNoDownloadUrlInResult: if the status request does not have a download URL in the response.
            SpectraAssureUnsupportedStrategy: if the selection strategy specified in 'download_criteria' is invalid.

            From the urlDownloader we may get:
                UrlDownloaderUnknownHashKey:  we cannot find the proper hash key in the provided hash info dict.
                UrlDownloaderTargetDirectoryIssue:  there are issues with the target directory.
                UrlDownloaderTargetFileIssue: there are issues with the target file.
                UrlDownloaderTempFileIssue: there are issues with the temp file.
                UrlDownloaderFileVerifyIssue: the verification failed for the existing file or for the downloaded file.

        QueryParameters:
            Additional query parameters to be used by status()
            while gathering information on download candidates.

            status supports:
                'build' as a query parameter,
                'download' is not valid on this level
                (only used internally by the download call when actually needed).

        Notes:
            The result may be empty if there are no approved download candidates when looking for multiple versions,
            or when the specified version is not approved.

            Using status() with 'download' directly influences your Spectra Assure Portal download capacity.

        """
        self._prep_criteria(download_criteria)
        target_dir_posix = self._validate_target_dir(target_dir)

        # find the version(s) and see if they are candidates
        chosen = self._prep_candidates(
            target_dir=target_dir_posix,
            project=project,
            package=package,
            version=version,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

        if chosen is None:
            logger.info("the resulting candidate list is empty")
            return None

        return self._process_candidates(
            target_dir=target_dir_posix,
            project=project,
            package=package,
            chosen=chosen,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

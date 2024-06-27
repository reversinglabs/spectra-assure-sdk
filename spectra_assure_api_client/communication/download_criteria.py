import logging
from typing import (
    List,
)

from .exceptions import (
    SpectraAssureInvalidAction,
)

SUPPORTED_STRATEGIES: List[str] = [
    "LatestApproved_ByApprovalTimeStamp",  # default
    "AllApproved",
    # "AllApproved_SkipExistingFiles_VerifyAfterDownload",
    # "AllApproved_SkipExistingFilesButVerify_VerifyAfterDownload",
]


logger = logging.getLogger(__name__)


class SpectraAssureDownloadCriteria:

    def __init__(
        self,
        *,
        wait_for_scan_done: bool = False,  # manually approved items are Done already
        max_wait_time_for_scan_done: int = 60,  # seconds , <= 1 hour
        #
        # mustHaveQualityStatusPass: bool = False,
        must_be_approved: bool = True,
        #
        current_strategy: str = "LatestApproved_ByApprovalTimeStamp",
        #
        with_overwrite_existing_files: bool = False,
        with_verify_after_download: bool = True,
        with_verify_existing_files: bool = True,
    ) -> None:
        """
        Args:

        wait_for_scan_done: bool = False
            If a scan has not finished, wait for it to finish.

        max_wait_time_for_scan_done: int = 60 # in seconds
            If waiting for the scan to finish, by default wait max 60 seconds per scan item.
            Max time per item <= 1h (3600 seconds)
            Min time > 10 seconds
            Wait intervals are never greater than 30 seconds and never smaller than 10 seconds.

        mustHaveQualityStatusPass: bool = False; Optional.
            If True, the 'quality' status must be 'pass' before we consider this version a candidate for download.
            Otherwise, we ignore this candidate.

        must_be_approved: bool = True.
            By default, we ignore all unapproved versions.
            If set to False, any candidate for download does not have to be approved.

        current_strategy: str Enum:
            LatestApprovedByTimeStamp: only approved items are inspected and only one (or none) is selected:
                the most recent by approved_timestamp

            AllApproved_SkipExistingFiles_VerifyAfterDownload:
                only download and verify new files

            AllApproved_SkipExistingFilesButVerify_VerifyAfterDownload:
                verify existing files and download and verify new ones

            AllApproved:  -> AllApproved_SkipExistingFiles_VerifyAfterDownload

        with_verify_after_download: bool = True; Optional.
            On download (to a temp location) we verify the file after download,
            and compare it to the sha256 from the status response.
            On mismatch, we raise 'DownloadFileDigestFailure' and remove the temp file.

        with_overwrite_existing_files: bool: False; Optional.
            If False and the target file already exists, we do not overwrite the target file.
            If True we overwrite the target file.

        with_verify_existing_files: bool = True;
            If True and the target file already exists,
            we verify the currently existing target file against the sha256 from the status response.
            On mismatch, we raise 'ExistingTargetFileDigestFailure' and report the path to the file.

        """
        self.current_strategy = ""
        for strategy in SUPPORTED_STRATEGIES:
            if current_strategy.lower() == strategy.lower():
                self.current_strategy = strategy

        if len(self.current_strategy) == 0:
            # pylint: disable-next=line-too-long
            msg = (
                "The strategy you requested is not supported:"
                + f" {self.current_strategy}; must be one of {SUPPORTED_STRATEGIES}"
            )
            raise SpectraAssureInvalidAction(message=msg)

        self.wait_for_scan_done = wait_for_scan_done
        self.max_wait_time_for_scan_done = max_wait_time_for_scan_done
        self.max_wait_time_for_scan_done = max(10, self.max_wait_time_for_scan_done)
        self.max_wait_time_for_scan_done = min(3600, self.max_wait_time_for_scan_done)

        # self.mustHaveQualityStatusPass = mustHaveQualityStatusPass
        self.must_be_approved = must_be_approved

        self.with_overwrite_existing_files = with_overwrite_existing_files
        self.with_verify_after_download = with_verify_after_download
        self.with_verify_existing_files = with_verify_existing_files

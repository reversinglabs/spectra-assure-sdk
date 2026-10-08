import logging

from .exceptions import (
    SpectraAssureInvalidAction,
)

SUPPORTED_STRATEGIES: list[str] = [
    "LatestApproved_ByApprovalTimeStamp",  # default
    "AllApproved",
]


logger = logging.getLogger(__name__)


class SpectraAssureDownloadCriteria:
    def __init__(
        self,
        *,
        wait_for_scan_done: bool = False,  # manually approved items are Done already
        max_wait_time_for_scan_done: int = 300,  # seconds , <= 1 hour
        must_be_approved: bool = True,
        current_strategy: str = "LatestApproved_ByApprovalTimeStamp",
        with_overwrite_existing_files: bool = False,
        with_verify_after_download: bool = True,
        with_verify_existing_files: bool = True,
    ) -> None:

        self.current_strategy = ""
        for strategy in SUPPORTED_STRATEGIES:
            if current_strategy.lower() == strategy.lower():
                self.current_strategy = strategy

        if len(self.current_strategy) == 0:
            # pylint: disable-next=line-too-long
            msg = (
                "The strategy you requested is not supported:"
                + f" {current_strategy}; must be one of {SUPPORTED_STRATEGIES}"
            )
            raise SpectraAssureInvalidAction(message=msg)

        self.wait_for_scan_done = wait_for_scan_done
        self.max_wait_time_for_scan_done = max_wait_time_for_scan_done
        self.max_wait_time_for_scan_done = max(10, self.max_wait_time_for_scan_done)
        self.max_wait_time_for_scan_done = min(3600, self.max_wait_time_for_scan_done)

        self.must_be_approved = must_be_approved

        self.with_overwrite_existing_files = with_overwrite_existing_files
        self.with_verify_after_download = with_verify_after_download
        self.with_verify_existing_files = with_verify_existing_files

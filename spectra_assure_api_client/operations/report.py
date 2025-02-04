import logging
from typing import (
    Any,
    Dict,
    List,
)

from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)
from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsReport(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    @staticmethod
    def current_report_names() -> List[str]:
        return [  # (8)
            "cyclonedx",
            "rl-checks",
            "rl-cve",  # not json
            "rl-json",
            "rl-uri",  # not json
            "sarif",
            "spdx",
            "rl-summary-pdf",  # not json
        ]

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

    def report(  # pylint: disable=too-many-arguments
        self,
        *,
        project: str,
        package: str,
        version: str,
        report_type: str,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Any:
        """
        Action:
            Execute a report() API call
            for the specified 'project/package@version'

        Args:
         - project: str, mandatory.
         - package: str, mandatory.
         - version: str, mandatory.
         - report_type: str, mandatory
           must be one of: (8)
            - cyclonedx
            - rl-checks
            - rl-cve
            - rl-uri
            - rl-json
            - sarif
            - spdx
            - rl-summary-pdf

         - auto_adapt_to_throttle: bool, default False, optional.
         - qp: Dict[str,Any] , optional.

        Return:
            The 'requests.result' of the report API call.
            See Notes for the expected response format.

        Raises:
            May raise exceptions on issues with the HTTP connection or wrong parameters.
            - SpectraAssureInvalidAction: our exception.
            - <any other exception> from requests.get().

        QueryParameters:
            report supports one query parameter:
             -  build

        Notes:
            The result data is not always in the JSON format.
            Specifically, the 'rl-cve' and `rl-uri` report are in CSV format.

            When a new report format is introduced on the Portal,
            and the new report does not exist yet for this 'version'
            expect 404 as a result when requesting the new report format.
            You will need to rescan the uploaded file to produce a new set of reports.
            After the rescan, you can request the report in the new format.
        """

        action = "report"
        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        supported = ["version"]
        if what not in supported:
            msg = f"'{action}' is only supported for {'and '.join(supported)}"
            raise SpectraAssureInvalidAction(message=msg)

        # note not al reports are in json format some are csv
        r_type_list = sorted(self.current_report_names())

        if report_type not in r_type_list:
            msg = f"'report_type' is not valid, must be one of: {', '.join(r_type_list)}"
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
            report_type=report_type,
        )
        return self.do_it_get(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **valid_qp,
        )

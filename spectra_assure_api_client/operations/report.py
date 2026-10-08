import logging
from typing import (
    Any,
)

import requests

from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsReport(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def report(  # pylint: disable=too-many-arguments
        self,
        *,
        project: str,
        package: str,
        version: str,
        report_type: str,
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,
    ) -> requests.Response:
        action = "report"
        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        supported = ["version"]
        if what not in supported:
            msg = f"'{action}' is only supported for {' and '.join(supported)}"
            raise SpectraAssureInvalidAction(message=msg)

        # The report type is passed through, not checked, on purpose: the Portal
        # checks it, and the list has changed over time, so a new type must not
        # need a new SDK version. An unknown type comes back as a 400 or 404 in
        # the response. (filestream_report does check its types, against the
        # eight the API lists for the File Stream.)
        # Not all reports are JSON; rl-cve and rl-uri are CSV.
        report_type = report_type.lower()

        valid_qp: dict[str, Any] = self._qp_report(
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
        return self._do_it_get(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **valid_qp,
        )

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


class SpectraAssureApiOperationsPurlImport(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    @staticmethod
    def _qp_purl_import(
        *,
        what: str,
        **qp: Any,
    ) -> dict[str, Any]:
        # The query parameters come from the specification, not from a list kept
        # here. The body (the source and the credentials) is built from named
        # arguments, so only query parameters are taken from **qp.
        return SpectraAssureApiOperationsBase._accepted_query("purl_import", what, qp)

    def purl_import(  # pylint: disable=too-many-arguments
        self,
        *,
        project: str,
        package: str,
        version: str,
        purl: str,
        auth_user: str | None = None,
        auth_pass: str | None = None,
        bearer_token: str | None = None,
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,
    ) -> requests.Response:

        action = "purl_import"
        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        supported = ["version"]
        if what not in supported:
            msg = f"'{action}' is only supported for {' and '.join(supported)}"
            raise SpectraAssureInvalidAction(message=msg)

        valid_qp: dict[str, Any] = self._qp_purl_import(
            what=what,
            **qp,
        )
        xurl = self._make_current_url(
            action=action,
            project=project,
            package=package,
            version=version,
        )

        data = self._import_body(
            action=action,
            key="purl",
            value=purl,
            auth_user=auth_user,
            auth_pass=auth_pass,
            bearer_token=bearer_token,
        )

        return self._post(
            action=action,
            url=xurl,
            body="json",
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            post_data=data,
            **valid_qp,
        )

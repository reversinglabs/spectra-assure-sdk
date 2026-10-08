import logging
import os
from typing import (
    Any,
)

import requests

from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsImportProfile(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def import_profile(  # pylint: disable=too-many-arguments
        self,
        *,
        organization: str,
        file_path: str,
        replace: bool = True,
        group: str | None = None,
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,  # ignored
    ) -> requests.Response:
        action = "import_org_profile"
        if group is None:
            operation = self._resolve("import_profile", "organization")
            url = self._url_for(operation, organization=organization)
        else:
            action = "import_group_profile"
            operation = self._resolve("import_profile", "group")
            url = self._url_for(operation, organization=organization, group=group)

        if not (os.path.isfile(file_path) and os.access(file_path, os.R_OK)):
            msg = f"'{action}' needs the specified file '{file_path}' to exist and be readable"
            raise SpectraAssureInvalidAction(message=msg)

        post_data = {
            "replace": replace,
        }

        valid_qp: Any = {}
        return self._post(
            action=action,
            url=url,
            body="form",
            file_path=file_path,
            post_data=post_data,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **valid_qp,
        )

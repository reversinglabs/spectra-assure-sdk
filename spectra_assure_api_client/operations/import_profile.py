"""
https://{portalUrl}/api/public/v1/profile/{organization}/import
https://{portalUrl}/api/public/v1/profile/{organization_name}/{group_name}/import

## path Parameters

    organization    required    string
        Example: example-organization
        Specify the name of a Portal organization to use in the request.
        The user account that is sending the request must be a member of the specified organization
          and have the appropriate permissions to perform the requested operation.
        Organization names are case-sensitive.

    group required string
        Example: example-group
        Specify the name of a Portal group to use in the request.
        The group must exist in the specified Portal organization.
        Group names are case-sensitive.

## Request Body schema: multipart/form-data

    configuration_file required string <binary>

    replace boolean Default: true
        This optional flag lets you decide how the imported configuration is applied.
        If true, the existing configuration is fully replaced by the imported configuration.
        If false, the imported configuration is merged into the existing configuration
          (only provided overrides are updated; others remain unchanged).
"""

import logging
import os
from typing import (
    Any,
)

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
        auto_adapt_to_throttle: bool = False,
        **qp: Any,  # ignored
    ) -> Any:
        action = "import_org_profile"
        if group is not None:
            action = "import_group_profile"

        url = self._make_current_url(
            action=action,
        )

        # url will now be 'https://<server....>/api/public/v1/profile'
        if action == "import_group_profile":
            url = f"{url}/{organization}/{group}/import"
        else:
            url = f"{url}/{organization}/import"

        if not (os.path.isfile(file_path) and os.access(file_path, os.R_OK)):
            msg = f"'{action}' needs the specified file '{file_path}' to exist and be readable"
            raise SpectraAssureInvalidAction(message=msg)

        post_data = {
            "replace": replace,
        }
        use_multipart = True

        # msg = f"action: {action} url: {url} useMulti: {use_multipart} file_path: {file_path} post_data: {post_data}"
        # logger.debug(msg)

        valid_qp: Any = {}
        return self.do_it_post(
            action=action,
            url=url,
            use_multipart=use_multipart,
            file_path=file_path,
            post_data=post_data,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **valid_qp,
        )

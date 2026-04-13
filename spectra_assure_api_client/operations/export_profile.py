"""
A) GET https://{portalUrl}/api/public/v1/profile/{organization_name}/export
B) GET https://{portalUrl}/api/public/v1/profile/{organization_name}/{group_name}/export

## path Parameters
A and B)

    organization    required    string
        Example: example-organization
        Specify the name of a Portal organization to use in the request.
        The user account that is sending the request must be a member of the specified organization
          and have the appropriate permissions to perform the requested operation.
        Organization names are case-sensitive.

B only)
    group   required    string
        Example: example-group
        Specify the name of a Portal group to use in the request.
        The group must exist in the specified Portal organization.
        Group names are case-sensitive.
"""

import logging
from typing import (
    Any,
)

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsExportProfile(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def export_profile(
        self,
        *,
        organization: str,
        group: str | None = None,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,  # ignored
    ) -> Any:
        action = "export_org_profile"
        if group is not None:
            action = "export_group_profile"

        url = self._make_current_url(
            action=action,
        )

        # url will now be 'https://<server....>/api/public/v1/profile'
        if action == "export_group_profile":
            url = f"{url}/{organization}/{group}/export"
        else:
            url = f"{url}/{organization}/export"

        qp = {}
        return self.do_it_get(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **qp,
        )

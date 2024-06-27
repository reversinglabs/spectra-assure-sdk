import logging
from typing import (
    Any,
    Dict,
)

from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)
from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsCreate(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes

    @staticmethod
    def qp_create(
        *,
        what: str,
        **qp: Any,
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {}
        if what in ["project", "package"]:
            k = "description"
            if k in qp:
                r[k] = qp[k]
        return r

    def create(
        self,
        *,
        project: str,
        package: str | None = None,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Any:
        """
        Action:
            Execute a create() API call
            to create a new 'project' or a new 'package'.
            ( For creating a 'version', see scan() )

        Args:
         - project: str, mandatory.
         - package: str | None, optional.
         - auto_adapt_to_throttle: bool, default False, optional.
         - qp: Dict[str,Any] , optional.

        Return:
            The 'requests.result' of the create() API call.

        Raises:
            May raise exceptions on issues with the HTTP connection or wrong parameters.
            - SpectraAssureInvalidAction: our exception.
            - <any other exception> from requests.post().

        QueryParameters:
            'description' is supported as a query parameter for
             both create 'project' and create 'package'.

        Notes:
            If we only specify 'project', we create a new 'project' in the specified 'group'.
            If we specify 'project' and 'package', we create a new 'package' in that 'project'.
        """

        action = "create"
        what = self._what(project=project, package=package)

        supported = [
            "project",
            "package",
        ]
        if what not in supported:
            msg = f"'create' is only supported for {'and '.join(supported)}"
            raise SpectraAssureInvalidAction(message=msg)

        valid_qp: Dict[str, Any] = self.qp_create(what=what, **qp)
        url = self._make_current_url(action=action, project=project, package=package)

        return self.do_it_post(
            action=action,
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **valid_qp,
        )

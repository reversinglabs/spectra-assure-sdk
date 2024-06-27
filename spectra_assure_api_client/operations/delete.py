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


class SpectraAssureApiOperationsDelete(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes

    @staticmethod
    def qp_delete(
        *,
        what: str,
        **qp: Any,
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {}

        # only version supports qp
        if what in ["version"]:
            for k in ["build"]:
                if k in qp:
                    r[k] = qp[k]

        return r

    def delete(
        self,
        *,
        project: str,
        package: str | None = None,
        version: str | None = None,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Any:
        """
        Action:
            Execute delete() API call

        Args:
         - project: str, mandatory.
         - package: str | None, optional.
         - version: str | None, optional.
         - auto_adapt_to_throttle: bool, default False, optional.
         - qp: Dict[str,Any] , optional.

        Return:
            The 'requests.result' of the delete API call.

        Raises:
            May raise exceptions on issues with the HTTP connection or wrong parameters.
            - SpectraAssureInvalidAction: our exception.
            - <any other exception> from requests.get().

        QueryParameters:
            the optional 'build' query parameter is supported only for 'version' delete.

        Notes:
            If we only specify 'project', we delete that 'project' and all its 'packages' and 'versions'.
            If we specify 'project' and 'package', we delete that 'package' and all its 'versions'.
            If we specify 'project', 'package' and 'version', we delete only that 'version'.
        """

        action = "delete"
        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        supported = [
            "project",
            "package",
            "version",
        ]
        if what not in supported:
            msg = f"'delete' is only supported for {'and '.join(supported)}"
            raise SpectraAssureInvalidAction(message=msg)

        valid_qp: Dict[str, Any] = self.qp_delete(what=what, **qp)
        url = self._make_current_url(action=action, project=project, package=package, version=version)

        return self.do_it_delete(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **valid_qp,
        )

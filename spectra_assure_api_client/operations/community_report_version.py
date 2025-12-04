"""
def:: community-api: 'api/public/v1/community'
def:: COMMUNITIES: [ "gem" "npm" "nuget" "psgallery" "pypi" "vsx" ]

[ ] https://{portalUrl}/{community-api}/report/version/pkg:{repository}/[{namespace}/]{package}[@{version}]
        [ ] GET :: may return one version; note namespace is optional

    path Parameters:
        repository [required] string  validate: in COMMUNITIES
            Open source community identifier of the software repository that hosts the requested software package.
            Must match one of the software repositories supported by Spectra Assure Community.
        namespace [optional] string
            Namespace of the requested software package
            (according to the purl schema pkg:repository/[namespace/]package@version).
        package [required] string
            Name of the requested software package
            (according to the purl schema pkg:repository/[namespace/]package@version).
        version [optional] string
            Version of the requested software package
            (according to the purl schema pkg:repository/[namespace/]package[@version]).

    query Parameters
        artifact string ::
            Qualifier that specifies the artifact file of the requested software package
            (according to the purl schema pkg:repository/[namespace/]package@version?artifact=filename.ext).
            Note that some software repositories (communities) do not support searching for artifacts.
        artifact_tag string ::
            Qualifier that specifies the artifact file of the requested software package by a repository-specific tag
            (according to the purl schema pkg:repository/[namespace/]package@version?artifact_tag=example_tag).
            Note that some software repositories (communities) do not support searching for artifacts.
"""

import logging
from typing import (
    Any,
    Dict,
    List,
)

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)

COMMUNITIES: List[str] = [
    "gem",
    "npm",
    "nuget",
    "psgallery",
    "pypi",
    "vsx",
]


class SpectraAssureApiOperationsCommunityReportVersion(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes

    @staticmethod
    def _qp_create(
        **qp: Any,
    ) -> Dict[str, Any]:
        """
        query Parameters
            artifact string ::
                Qualifier that specifies the artifact file of the requested software package
                (according to the purl schema pkg:repository/[namespace/]package@version?artifact=filename.ext).
                Note that some software repositories (communities) do not support searching for artifacts.
            artifact_tag string ::
                Qualifier that specifies the artifact file of the requested software package
                    by a repository-specific tag
                (according to the purl schema pkg:repository/[namespace/]package@version?artifact_tag=example_tag).
                Note that some software repositories (communities) do not support searching for artifacts.

                NOTE: no type or data validation currently.
        """
        r: Dict[str, Any] = {}
        params = [
            "artifact",
            "artifact_tag",
        ]
        for k in params:
            if k in qp:
                r[k] = qp[k]
        return r

    def community_report_version(
        self,
        *,  # force name based params
        repository: str,
        package: str,
        namespace: str | None = None,
        version: str | None = None,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Any:
        """
        path Parameters:
            repository [required] string  validate: in COMMUNITIES
                Open source community identifier of the software repository that hosts the requested software package.
                Must match one of the software repositories supported by Spectra Assure Community.
            namespace [optional] string
                Namespace of the requested software package
                (according to the purl schema pkg:repository/[namespace/]package@version).
            package [required] string
                Name of the requested software package
                (according to the purl schema pkg:repository/[namespace/]package@version).
            version [optional] string
                Version of the requested software package
                (according to the purl schema pkg:repository/[namespace/]package[@version]).

        Note: we will add the namespace to the package as the rest of the lib does not understand namespace
        """

        action = "community_report_package"
        # we will the namespace to the package as the rest of the lib does not understand namespace
        if namespace is not None and len(namespace) > 0:
            package = f"{namespace}/{package}"

        valid_qp: Dict[str, Any] = self._qp_create(**qp)
        url = self._make_current_url_community(
            action=action,
            repository=repository,
            package=package,
            version=version,
        )
        logger.debug("url is now: %s", url)

        # https://{portalUrl}/{community-api}/report/version/pkg:{repository}/[{namespace}/]{package}[@{version}]

        return self.do_it_get(
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            **valid_qp,
        )

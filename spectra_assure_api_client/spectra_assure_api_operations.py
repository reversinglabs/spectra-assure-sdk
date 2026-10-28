import functools
import inspect
import logging
import warnings
from typing import TYPE_CHECKING, Any

from spectra_assure_api_client.operations.approve import (
    SpectraAssureApiOperationsApprove,
)

# audit
from spectra_assure_api_client.operations.audit_log_export import (
    SpectraAssureApiOperationsAuditLogExport,
)
from spectra_assure_api_client.operations.audit_log_status import (
    SpectraAssureApiOperationsAuditLogStatus,
)

# catalog
from spectra_assure_api_client.operations.catalog import (
    SpectraAssureApiOperationsCatalog,
)

# real operations
from spectra_assure_api_client.operations.checks import SpectraAssureApiOperationsChecks

# community
from spectra_assure_api_client.operations.community_find_packages import (
    SpectraAssureApiOperationsCommunityFindPackages,
)
from spectra_assure_api_client.operations.community_report_package import (
    SpectraAssureApiOperationsCommunityReportPackage,
)
from spectra_assure_api_client.operations.community_report_version import (
    SpectraAssureApiOperationsCommunityReportVersion,
)
from spectra_assure_api_client.operations.community_user_account import (
    SpectraAssureApiOperationsCommunityUserAccount,
)

#
from spectra_assure_api_client.operations.create import SpectraAssureApiOperationsCreate
from spectra_assure_api_client.operations.delete import SpectraAssureApiOperationsDelete

# pseudo operation
from spectra_assure_api_client.operations.download import (
    SpectraAssureApiOperationsDownload,
)
from spectra_assure_api_client.operations.edit import SpectraAssureApiOperationsEdit
from spectra_assure_api_client.operations.export_profile import SpectraAssureApiOperationsExportProfile

# file stream
from spectra_assure_api_client.operations.filestream import (
    SpectraAssureApiOperationsFilestream,
)
from spectra_assure_api_client.operations.import_profile import SpectraAssureApiOperationsImportProfile
from spectra_assure_api_client.operations.list import SpectraAssureApiOperationsList
from spectra_assure_api_client.operations.list_groups import (
    SpectraAssureApiOperationsListGroups,
)
from spectra_assure_api_client.operations.purl_import import (
    SpectraAssureApiOperationsPurlImport,
)
from spectra_assure_api_client.operations.reject import SpectraAssureApiOperationsReject
from spectra_assure_api_client.operations.report import SpectraAssureApiOperationsReport
from spectra_assure_api_client.operations.revoke import SpectraAssureApiOperationsRevoke
from spectra_assure_api_client.operations.rl_safe import (
    SpectraAssureApiOperationsRlSafe,
)
from spectra_assure_api_client.operations.scan import SpectraAssureApiOperationsScan
from spectra_assure_api_client.operations.status import SpectraAssureApiOperationsStatus
from spectra_assure_api_client.operations.sync import SpectraAssureApiOperationsSync
from spectra_assure_api_client.operations.url_import import (
    SpectraAssureApiOperationsUrlImport,
)
from spectra_assure_api_client.operations.usage import SpectraAssureApiOperationsUsage

if TYPE_CHECKING:
    from spectra_assure_api_client.communication.api import SpectraAssureApi, StaticToolBox
    from spectra_assure_api_client.communication.core import SpectraAssureApiCore
    from spectra_assure_api_client.communication.delete import SpectraAssureApiDelete
    from spectra_assure_api_client.communication.get import SpectraAssureApiGet
    from spectra_assure_api_client.communication.patch import SpectraAssureApiPatch
    from spectra_assure_api_client.communication.post import SpectraAssureApiPost
    from spectra_assure_api_client.communication.put import SpectraAssureApiPut
    from spectra_assure_api_client.operations.base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)


class SpectraAssureApiOperations(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsCreate,  # Create a project or package in the Portal
    SpectraAssureApiOperationsScan,  # Upload and scan a new version
    SpectraAssureApiOperationsList,  # List all groups, projects, packages, and versions
    SpectraAssureApiOperationsEdit,  # Edit details for a project, package, or version
    SpectraAssureApiOperationsDelete,  # Remove a project, package, or version from the Portal
    SpectraAssureApiOperationsReport,  # Download analysis report for a version
    SpectraAssureApiOperationsStatus,  # Show analysis status for a version
    SpectraAssureApiOperationsChecks,  # Show performed checks for a version
    SpectraAssureApiOperationsDownload,  # Get artifact download link for a version (uses List and Status)
    SpectraAssureApiOperationsSync,  # start a new scan if needed (e.g. new engine, see docs)
    SpectraAssureApiOperationsApprove,  # approve a version
    SpectraAssureApiOperationsReject,  # reject a version
    SpectraAssureApiOperationsRevoke,  # revoke a previously accepted version
    SpectraAssureApiOperationsRlSafe,  # create a rl-safe download link
    SpectraAssureApiOperationsUsage,  # list usage information
    SpectraAssureApiOperationsListGroups,  # list the groups in this organization that we have access to
    SpectraAssureApiOperationsUrlImport,  # scan a file (create a version) via a url
    SpectraAssureApiOperationsPurlImport,  # scan a file (create a version) via a purl
    # community
    SpectraAssureApiOperationsCommunityFindPackages,  # community find packages
    SpectraAssureApiOperationsCommunityReportPackage,  # Community report on a [Namespace/]Package[@version]
    SpectraAssureApiOperationsCommunityReportVersion,  # Community report on a [Namespace/]Package[@version]
    SpectraAssureApiOperationsCommunityUserAccount,
    # profile
    SpectraAssureApiOperationsExportProfile,  # export org or group profile
    SpectraAssureApiOperationsImportProfile,  # import org or group profile
    # audit
    SpectraAssureApiOperationsAuditLogExport,
    SpectraAssureApiOperationsAuditLogStatus,
    # file stream: standalone files keyed by file_id, no project/package/version
    SpectraAssureApiOperationsFilestream,
    # catalog: import packages from external catalogs, publish them to the group's catalog
    SpectraAssureApiOperationsCatalog,
):
    """A class that combines all operations"""

    # Deprecated public names of SDK internals (I-19). At run time they are
    # attached below as warning aliases; these declarations only tell a type
    # checker that the names still exist and what they accept.
    if TYPE_CHECKING:
        do_it_delete = SpectraAssureApiDelete._do_it_delete
        do_it_get = SpectraAssureApiGet._do_it_get
        do_it_patch = SpectraAssureApiPatch._do_it_patch
        do_it_post = SpectraAssureApiPost._do_it_post
        do_it_put = SpectraAssureApiPut._do_it_put
        execute_with_retry = SpectraAssureApiCore._execute_with_retry
        get_customer_context = SpectraAssureApi._get_customer_context
        show_debug = SpectraAssureApi._show_debug
        exists_posix_path = staticmethod(StaticToolBox._exists_posix_path)
        extract_hashes = staticmethod(StaticToolBox._extract_hashes)
        extract_purl_components = staticmethod(StaticToolBox._extract_purl_components)
        extract_target_file_name = staticmethod(StaticToolBox._extract_target_file_name)
        flatten_list = staticmethod(StaticToolBox._flatten_list)
        get_path = staticmethod(StaticToolBox._get_path)
        qp_status = staticmethod(SpectraAssureApiOperationsBase._qp_status)
        remove_temp_file_if_exists = staticmethod(StaticToolBox._remove_temp_file_if_exists)
        simple_path_to_posix = staticmethod(StaticToolBox._simple_path_to_posix)
        qp_edit = staticmethod(SpectraAssureApiOperationsBase._qp_edit)
        qp_reject = staticmethod(SpectraAssureApiOperationsBase._qp_reject)
        qp_revoke = staticmethod(SpectraAssureApiOperationsBase._qp_revoke)
        qp_scan = staticmethod(SpectraAssureApiOperationsBase._qp_scan)
        qp_download = staticmethod(SpectraAssureApiOperationsDownload._qp_download)
        qp_purl_import = staticmethod(SpectraAssureApiOperationsPurlImport._qp_purl_import)
        qp_url_import = staticmethod(SpectraAssureApiOperationsUrlImport._qp_url_import)
        listGroups = SpectraAssureApiOperationsListGroups.list_groups  # noqa: N815  the old name


# Old public names of methods that are internal to the SDK (I-19). The methods
# now carry a leading underscore. The old names stay for now as aliases that
# warn and forward, so that nobody who called one breaks in a minor release;
# they are meant to go in the next major release.
DEPRECATED_INTERNAL_NAMES: tuple[str, ...] = (
    "do_it_delete",
    "do_it_get",
    "do_it_patch",
    "do_it_post",
    "do_it_put",
    "execute_with_retry",
    "exists_posix_path",
    "extract_hashes",
    "extract_purl_components",
    "extract_target_file_name",
    "flatten_list",
    "get_customer_context",
    "get_path",
    "qp_download",
    "qp_edit",
    "qp_purl_import",
    "qp_reject",
    "qp_revoke",
    "qp_scan",
    "qp_status",
    "qp_url_import",
    "remove_temp_file_if_exists",
    "show_debug",
    "simple_path_to_posix",
)


# Public methods whose name changed: old name -> new name (I-25). Like the
# internals above they stay as warning aliases until the next major release.
DEPRECATED_RENAMED: dict[str, str] = {
    "listGroups": "list_groups",
}


def _deprecated_alias(old: str, new: str, message: str) -> Any:
    """An alias for `old` that warns with `message` and forwards to `new`.

    It keeps the target's signature (for `inspect` and the contract test) and
    its kind: a static method stays callable on the class.
    """
    target = inspect.getattr_static(SpectraAssureApiOperations, new)

    if isinstance(target, staticmethod):
        function = target.__func__

        @functools.wraps(function)
        def static_alias(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return function(*args, **kwargs)

        static_alias.__name__ = static_alias.__qualname__ = old
        return staticmethod(static_alias)

    @functools.wraps(target)
    def method_alias(self: Any, *args: Any, **kwargs: Any) -> Any:
        warnings.warn(message, DeprecationWarning, stacklevel=2)
        return getattr(self, new)(*args, **kwargs)

    method_alias.__name__ = method_alias.__qualname__ = old
    return method_alias


for _old in DEPRECATED_INTERNAL_NAMES:
    _message = (
        f"SpectraAssureApiOperations.{_old} is internal to the SDK and will be removed "
        f"in a future major release; do not call it"
    )
    setattr(SpectraAssureApiOperations, _old, _deprecated_alias(_old, f"_{_old}", _message))

for _old, _new in DEPRECATED_RENAMED.items():
    _message = (
        f"SpectraAssureApiOperations.{_old} is deprecated and will be removed "
        f"in a future major release; use {_new} instead"
    )
    setattr(SpectraAssureApiOperations, _old, _deprecated_alias(_old, _new, _message))

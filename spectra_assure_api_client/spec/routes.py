"""Which specification operation backs each public SDK call.

The SDK's public methods are coarser than the API: one `list` call covers four
specification operations, chosen by how far down the group/project/package/version
ladder the caller supplied arguments. This module holds that mapping and nothing
else, so the relationship between the customer-facing surface and the API is
stated in one readable place instead of being spread across per-operation
modules and a URL-building `if` chain.

Keys are `(action, what)` where `what` is the ladder position computed by
`SpectraAssureApiOperationsBase._what`.
"""

from __future__ import annotations

from .index import Operation, SpectraAssureSpecError, get_operation

# (action, what) -> operationId
ROUTES: dict[tuple[str, str], str] = {
    # project / package / version lifecycle
    ("create", "project"): "postProject",
    ("create", "package"): "postPackage",
    ("delete", "project"): "deleteProject",
    ("delete", "package"): "deletePackage",
    ("delete", "version"): "deleteVersion",
    ("edit", "project"): "patchProject",
    ("edit", "package"): "patchPackage",
    ("edit", "version"): "patchVersion",
    # listing: the same public `list` call, four operations
    ("list", "group"): "listGroupProjects",
    ("list", "project"): "listPackages",
    ("list", "package"): "listVersions",
    ("list", "version"): "versionInfo",
    ("list_groups", "group"): "listGroups",
    # version analysis
    ("scan", "version"): "scanVersion",
    ("status", "version"): "getVersionStatus",
    ("checks", "version"): "getVersionChecks",
    ("report", "version"): "getVersionReport",
    ("sync", "version"): "syncVersion",
    ("rl_safe", "version"): "getRlSafeVersionArchive",
    # approval workflow
    ("approve", "version"): "approveVersion",
    ("reject", "version"): "rejectVersion",
    ("revoke", "version"): "revokeVersion",
    # imports
    ("url_import", "version"): "importVersion",
    ("purl_import", "version"): "importVersionPURL",
    # organization-level and group-level pairs
    ("usage", "organization"): "listOrganizationUsage",
    ("usage", "group"): "listGroupUsage",
    ("export_profile", "organization"): "exportOrganizationRlProfile",
    ("export_profile", "group"): "exportGroupRlProfile",
    ("import_profile", "organization"): "importOrganizationRlProfile",
    ("import_profile", "group"): "importGroupRlProfile",
    # audit
    ("audit_log_export", "organization"): "createAuditExportAPI",
    ("audit_log_status", "organization"): "getAuditExportStatus",
    # community: no organization or group in the path
    ("community_user_account", "community"): "getUserAccountDetails",
    ("community_find_packages", "community"): "postFindPackageMetadata",
    ("community_report_package", "community"): "getCommunityPackageMetadata",
    ("community_report_version", "community"): "getCommunityVersionAssessment",
}

# File Stream. These files are standalone: no project, package or version, and
# `file_id` as the only handle. The ladder position is the constant
# "filestream", which `_what` never returns, so these routes cannot be reached
# from the purl-based calls and vice versa.
ROUTES.update(
    {
        ("filestream_scan", "filestream"): "scanFilestreamFile",
        ("filestream_list", "filestream"): "listFilestreamFiles",
        ("filestream_status", "filestream"): "getFilestreamFileStatus",
        ("filestream_checks", "filestream"): "getFilestreamFileChecks",
        ("filestream_delete", "filestream"): "deleteFilestreamFile",
        ("filestream_sync", "filestream"): "syncFilestreamFile",
        ("filestream_approve", "filestream"): "approveFilestreamFile",
        ("filestream_reject", "filestream"): "rejectFilestreamFile",
        ("filestream_revoke", "filestream"): "revokeFilestreamFile",
        ("filestream_rl_safe", "filestream"): "getRlSafeFilestreamArchive",
        ("filestream_url_import", "filestream"): "importFilestreamURL",
        ("filestream_purl_import", "filestream"): "importFilestreamPURL",
    }
)

# File Stream reports are one operation, getFilestreamReport, with the type in
# its `report_type` path parameter. The specification lists the types that
# parameter accepts; `filestream_report` checks against this table, which holds
# exactly those (a unit test compares the two). `rl-diff` is not among them:
# File Stream holds no versions to diff.
FILESTREAM_REPORT_OPERATIONS: dict[str, str] = dict.fromkeys(
    ("cyclonedx", "rl-checks", "rl-cve", "rl-json", "rl-summary-pdf", "rl-uri", "sarif", "spdx"),
    "getFilestreamReport",
)

ROUTES.update(
    {
        (f"filestream_report:{report_type}", "filestream"): operation_id
        for report_type, operation_id in FILESTREAM_REPORT_OPERATIONS.items()
    }
)


# Actions whose public method exists only in the SDK: these orchestrate several
# real operations and have no single operation of their own.
PSEUDO_ACTIONS = frozenset(
    {
        "download",
        "rl_safe_download",
        "filestream_download",
        "filestream_rl_safe_download",
    }
)


def resolve(action: str, what: str) -> Operation:
    """Return the operation backing `action` at ladder position `what`."""
    try:
        operation_id = ROUTES[(action, what)]
    except KeyError as exc:
        supported = sorted({w for (a, w) in ROUTES if a == action})
        if not supported:
            raise SpectraAssureSpecError(f"no route is defined for action {action!r}") from exc
        raise SpectraAssureSpecError(f"'{action}' is only supported for {' and '.join(supported)}") from exc

    return get_operation(operation_id)


def resolve_filestream_report(report_type: str) -> Operation:
    """Return the operation for one File Stream report type."""
    key = report_type.lower()
    if key not in FILESTREAM_REPORT_OPERATIONS:
        supported = ", ".join(sorted(FILESTREAM_REPORT_OPERATIONS))
        raise SpectraAssureSpecError(
            f"unsupported File Stream report type {report_type!r}; supported types are: {supported}"
        )
    return resolve(f"filestream_report:{key}", "filestream")


def routed_operation_ids() -> frozenset[str]:
    """Every operation id the public surface can reach."""
    return frozenset(ROUTES.values())

# Operations

Every call of `SpectraAssureApiOperations`, one entry per operation.
How to install the SDK, create a client, configure it and handle errors is described in the [README](./README.md).

- [General operations](#general-operations): the organization, its groups, and projects, packages and versions;
  also the Community calls
- [File Stream](#file-stream): standalone files, addressed by `file_id`
- [Catalog](#catalog): external catalogs, and the group's software catalog

## General operations

Each entry names the method to call and the class that provides it.
Every method maps directly to a Portal API operation,
except `download`, `filestream_download` and the two `*_rl_safe_download` calls, which combine several.

The table under each entry shows where the call works and what it sends:

- **Targets**: the levels it addresses: the organization, a group, a project, a package or a version.
- **Query parameters**: the levels at which the API specification declares query parameters.
  Pass them as keyword arguments; names the specification does not declare are dropped.
- **Body fields**: the levels at which the call sends named fields in the request body, such as `description` or `reason`.

[`checks`](./doc/checks.md) · class `SpectraAssureApiOperationsChecks`

**Show performed checks for a version.**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          |  |  |  |  | &#10003; |
| Query parameters |  |  |  |  |  |
| Body fields      |  |  |  |  |  |

[`create`](./doc/create.md) · class `SpectraAssureApiOperationsCreate`

**Create a project or package in the Portal.**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          |  |  | &#10003; | &#10003; |  |
| Query parameters |  |  |  |  |  |
| Body fields      |  |  | &#10003; | &#10003; |  |

[`delete`](./doc/delete.md) · class `SpectraAssureApiOperationsDelete`

**Remove a project, package, or version from the Portal.**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          |  |  | &#10003; | &#10003; | &#10003; |
| Query parameters |  |  |  |  | &#10003; |
| Body fields      |  |  |  |  |  |

[`download`](./doc/download.md) · class `SpectraAssureApiOperationsDownload`

**Download file(s) of approved version(s).**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          |  |  |  | &#10003; | &#10003; |
| Query parameters |  |  |  | &#10003; | &#10003; |
| Body fields      |  |  |  |  |  |

This class uses `list` and `status` operations to gather information about what is downloadable,
and only requests the artifact download URL for versions that are selected for download.

Every time the download link is generated, your Portal download capacity is reduced by the artifact's file size,
even if the artifact is not downloaded from the link.
If your user account doesn't have permission to download files from the Portal,
the API responds with an error and the download capacity remains unaffected.

[`edit`](./doc/edit.md) · class `SpectraAssureApiOperationsEdit`

**Edit details for a project, package, or version.**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          |  |  | &#10003; | &#10003; | &#10003; |
| Query parameters |  |  |  |  |  |
| Body fields      |  |  | &#10003; | &#10003; | &#10003; |

[`list`](./doc/list.md) · class `SpectraAssureApiOperationsList`

**List the projects in a group, the packages in a project or the versions of a package, or show the details of a version.**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          |  | &#10003; | &#10003; | &#10003; | &#10003; |
| Query parameters |  |  |  |  |  |
| Body fields      |  |  |  |  |  |

[`report`](./doc/report.md) · class `SpectraAssureApiOperationsReport`

**Download analysis report for a version.**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          |  |  |  |  | &#10003; |
| Query parameters |  |  |  |  | &#10003; |
| Body fields      |  |  |  |  |  |

The report type is passed to the Portal as given, in lowercase, and checked there,
so a report type the Portal adds works without an SDK update; see the reference page for the current list.

[`scan`](./doc/scan.md) · class `SpectraAssureApiOperationsScan`

**Upload and scan a new version.**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          |  |  |  |  | &#10003; |
| Query parameters |  |  |  |  | &#10003; |
| Body fields      |  |  |  |  |  |

[`status`](./doc/status.md) · class `SpectraAssureApiOperationsStatus`

**Show analysis status for a version.**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          |  |  |  |  | &#10003; |
| Query parameters |  |  |  |  | &#10003; |
| Body fields      |  |  |  |  |  |

[`sync`](./doc/sync.md) · class `SpectraAssureApiOperationsSync`

**Rescan a version**, to bring it up to date with a changed configuration or the latest engine; it does not count towards the monthly analysis capacity.

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          |  |  |  |  | &#10003; |
| Query parameters |  |  |  |  |  |
| Body fields      |  |  |  |  |  |

[`approve`](./doc/approve.md) · class `SpectraAssureApiOperationsApprove`

**Approve a version.** `reason` is mandatory.

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          |  |  |  |  | &#10003; |
| Query parameters |  |  |  |  |  |
| Body fields      |  |  |  |  | &#10003; |

[`reject`](./doc/reject.md) · class `SpectraAssureApiOperationsReject`

**Reject a version.** `reason` is mandatory.

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          |  |  |  |  | &#10003; |
| Query parameters |  |  |  |  |  |
| Body fields      |  |  |  |  | &#10003; |

[`revoke`](./doc/revoke.md) · class `SpectraAssureApiOperationsRevoke`

**Revoke a previously approved version.** `reason` is mandatory.

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          |  |  |  |  | &#10003; |
| Query parameters |  |  |  |  |  |
| Body fields      |  |  |  |  | &#10003; |

[`rl_safe`, `rl_safe_download`](./doc/rl_safe.md) · class `SpectraAssureApiOperationsRlSafe`

**Create a download link for the [RL-SAFE archive](https://docs.secure.software/concepts/analysis-reports#rl-safe-archive).**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          |  |  |  |  | &#10003; |
| Query parameters |  |  |  |  | &#10003; |
| Body fields      |  |  |  |  |  |

[`usage`](./doc/usage.md) · class `SpectraAssureApiOperationsUsage`

**List the current analysis capacity usage for the organization or group .**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          | &#10003; | &#10003; |  |  |  |
| Query parameters |  |  |  |  |  |
| Body fields      |  |  |  |  |  |

[`list_groups`](./doc/listGroups.md) · class `SpectraAssureApiOperationsListGroups` (`listGroups` is its deprecated old name)

**List the groups you have access to in the current organization .**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          | &#10003; |  |  |  |  |
| Query parameters |  |  |  |  |  |
| Body fields      |  |  |  |  |  |

[`url_import`](./doc/urlImport.md) · class `SpectraAssureApiOperationsUrlImport`

**Import and scan a new version from a URL.**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          |  |  |  |  | &#10003; |
| Query parameters |  |  |  |  | &#10003; |
| Body fields      |  |  |  |  | &#10003; |

[`purl_import`](./doc/purlImport.md) · class `SpectraAssureApiOperationsPurlImport`

**Import and scan a new version from a package URL (PURL).**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          |  |  |  |  | &#10003; |
| Query parameters |  |  |  |  | &#10003; |
| Body fields      |  |  |  |  | &#10003; |

[`community_find_packages`](./doc/community-find-packages.md) · class `SpectraAssureApiOperationsCommunityFindPackages`

**Search the Spectra Assure Community for packages.**

|                  | Community |
| --               | -- |
| Targets          | &#10003; |
| Query parameters | &#10003; |
| Body fields      |  |

[`community_report_package`](./doc/community-report-package.md) · class `SpectraAssureApiOperationsCommunityReportPackage`

**Show details about a package in the Spectra Assure Community.**

|                  | Community |
| --               | -- |
| Targets          | &#10003; |
| Query parameters | &#10003; |
| Body fields      |  |

[`community_report_version`](./doc/community-report-version.md) · class `SpectraAssureApiOperationsCommunityReportVersion`

**Show the Spectra Assure Community report for a package version.**

|                  | Community |
| --               | -- |
| Targets          | &#10003; |
| Query parameters | &#10003; |
| Body fields      |  |

[`community_user_account`](./doc/community-user-account.md) · class `SpectraAssureApiOperationsCommunityUserAccount`

**View details about the Spectra Assure Community account of the current user.**

|                  | Community |
| --               | -- |
| Targets          | &#10003; |
| Query parameters |  |
| Body fields      |  |

[`export_profile`](./doc/export-profile.md) · class `SpectraAssureApiOperationsExportProfile`

**Export the profile configuration for a Portal organization or group as a JSON file .**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          | &#10003; | &#10003; |  |  |  |
| Query parameters |  |  |  |  |  |
| Body fields      |  |  |  |  |  |

[`import_profile`](./doc/import-profile.md) · class `SpectraAssureApiOperationsImportProfile`

**Import profile configuration settings for a Portal organization or group from a JSON file.**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          | &#10003; | &#10003; |  |  |  |
| Query parameters |  |  |  |  |  |
| Body fields      | &#10003; | &#10003; |  |  |  |

[`audit_log_export`](./doc/audit-log-export.md) · class `SpectraAssureApiOperationsAuditLogExport`

**Start the export of an audit log.**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          | &#10003; |  |  |  |  |
| Query parameters |  |  |  |  |  |
| Body fields      | &#10003; |  |  |  |  |

[`audit_log_status`](./doc/audit-log-status.md) · class `SpectraAssureApiOperationsAuditLogStatus`

**Check the status of an audit log export.**

|                  | Organization | Group | Project | Package | Version |
| --               | -- | -- | -- | -- | -- |
| Targets          | &#10003; |  |  |  |  |
| Query parameters |  |  |  |  |  |
| Body fields      |  |  |  |  |  |

## File Stream

File Stream files are standalone: they do not belong to a project or a package,
and they have no versions. A server-generated `file_id`, returned when the file
is created, is the only reference to a File Stream file.

The File Stream calls are kept separate from the project/package/version calls:
they take `file_id` rather than `project`, `package` and `version`.

[`filestream_scan`](./doc/filestream-scan.md)

**Upload a file to the File Stream and scan it.** Returns the `requests.Response`; on success (201) the new `file_id` is the `id` field of its JSON: `response.json()["id"]`.

|                  | File Stream file |
| --               | -- |
| Targets          | &#10003; |
| Query parameters | &#10003; |
| Body fields      |  |

[`filestream_url_import`](./doc/filestream-url-import.md)

**Import and scan a new File Stream file from a URL.**

|                  | File Stream file |
| --               | -- |
| Targets          | &#10003; |
| Query parameters | &#10003; |
| Body fields      | &#10003; |

[`filestream_purl_import`](./doc/filestream-purl-import.md)

**Import and scan a new File Stream file from a package URL (PURL).**

|                  | File Stream file |
| --               | -- |
| Targets          | &#10003; |
| Query parameters | &#10003; |
| Body fields      | &#10003; |

[`filestream_list`](./doc/filestream-list.md)

**List the files in the File Stream of the current group.**

|                  | File Stream file |
| --               | -- |
| Targets          | &#10003; |
| Query parameters | &#10003; |
| Body fields      |  |

[`filestream_status`](./doc/filestream-status.md)

**Show analysis status for a File Stream file.**

|                  | File Stream file |
| --               | -- |
| Targets          | &#10003; |
| Query parameters | &#10003; |
| Body fields      |  |

[`filestream_checks`](./doc/filestream-checks.md)

**Show performed checks for a File Stream file.**

|                  | File Stream file |
| --               | -- |
| Targets          | &#10003; |
| Query parameters |  |
| Body fields      |  |

[`filestream_report`](./doc/filestream-report.md)

**Download an analysis report for a File Stream file.**

|                  | File Stream file |
| --               | -- |
| Targets          | &#10003; |
| Query parameters |  |
| Body fields      |  |

Supported types: `cyclonedx`, `rl-checks`, `rl-cve`, `rl-json`,
`rl-summary-pdf`, `rl-uri`, `sarif`, `spdx`. (`rl-diff` is not available.)
Unlike `report`, this call checks the type, against the eight types the API lists for the File Stream;
a type the API adds there needs an SDK update.

[`filestream_sync`](./doc/filestream-sync.md)

**Rescan a File Stream file**, to bring it up to date with a changed configuration or the latest engine; it does not count towards the monthly analysis capacity.

|                  | File Stream file |
| --               | -- |
| Targets          | &#10003; |
| Query parameters |  |
| Body fields      |  |

[`filestream_approve`](./doc/filestream-approve.md)

**Approve a File Stream file.** `reason` is mandatory.

|                  | File Stream file |
| --               | -- |
| Targets          | &#10003; |
| Query parameters |  |
| Body fields      | &#10003; |

[`filestream_reject`](./doc/filestream-reject.md)

**Reject a File Stream file.** `reason` is mandatory.

|                  | File Stream file |
| --               | -- |
| Targets          | &#10003; |
| Query parameters |  |
| Body fields      | &#10003; |

[`filestream_revoke`](./doc/filestream-revoke.md)

**Revoke a previously approved File Stream file.** `reason` is mandatory.

|                  | File Stream file |
| --               | -- |
| Targets          | &#10003; |
| Query parameters |  |
| Body fields      | &#10003; |

[`filestream_rl_safe`, `filestream_rl_safe_download`](./doc/filestream-rl-safe.md)

**Create a download link for the [RL-SAFE archive](https://docs.secure.software/concepts/analysis-reports#rl-safe-archive) of a File Stream file.**

|                  | File Stream file |
| --               | -- |
| Targets          | &#10003; |
| Query parameters |  |
| Body fields      |  |

`filestream_rl_safe_download` also fetches the archive.

[`filestream_download`](./doc/filestream-download.md)

**Download an approved File Stream file.**

|                  | File Stream file |
| --               | -- |
| Targets          | &#10003; |
| Query parameters |  |
| Body fields      |  |

[`filestream_delete`](./doc/filestream-delete.md)

**Remove a file from the File Stream.**

|                  | File Stream file |
| --               | -- |
| Targets          | &#10003; |
| Query parameters |  |
| Body fields      |  |

## Catalog

There are two kinds of catalog.
1. An *external catalog* lists software, with its streams and versions, that the Portal can import:
`import_from_catalog` creates a package from one of its entries,
and the package stays linked to the external catalog so newer versions can be imported later.
2. The group's *software catalog* is where packages are published on the Portal
so that their latest approved version is available to users in the Portal organization.

The method names are the operation IDs of the Portal API in snake case.
The calls that address a package take `project` and `package`, as the other calls do;
none of them take `version`.

[`get_external_catalog`](./doc/catalog-get-external-catalog.md)

**Read the document of an external catalog: its software, their streams and versions.**

|                  | Catalog |
| --               | -- |
| Targets          | &#10003; |
| Query parameters |  |
| Body fields      |  |

[`list_catalog_packages`](./doc/catalog-list-catalog-packages.md)

**List the packages published in the group's software catalog.**

|                  | Catalog |
| --               | -- |
| Targets          | &#10003; |
| Query parameters |  |
| Body fields      |  |

[`import_from_catalog`](./doc/catalog-import-from-catalog.md)

**Create a package from software in an external catalog and import versions into it.**

|                  | Catalog |
| --               | -- |
| Targets          | &#10003; |
| Query parameters |  |
| Body fields      | &#10003; |

[`update_from_catalog`](./doc/catalog-update-from-catalog.md)

**Import newer versions from the external catalog a package is linked to.**

|                  | Catalog |
| --               | -- |
| Targets          | &#10003; |
| Query parameters |  |
| Body fields      | &#10003; |

[`publish_package_to_catalog`](./doc/catalog-publish-package-to-catalog.md)

**Publish a package to the group's software catalog.**

|                  | Catalog |
| --               | -- |
| Targets          | &#10003; |
| Query parameters |  |
| Body fields      |  |

[`unpublish_package_from_catalog`](./doc/catalog-unpublish-package-from-catalog.md)

**Remove a package from the group's software catalog.**

|                  | Catalog |
| --               | -- |
| Targets          | &#10003; |
| Query parameters |  |
| Body fields      |  |

[`detach_from_catalog`](./doc/catalog-detach-from-catalog.md)

**Unlink a package from the external catalog it was imported from.**

|                  | Catalog |
| --               | -- |
| Targets          | &#10003; |
| Query parameters |  |
| Body fields      |  |

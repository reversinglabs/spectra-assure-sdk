import datetime
import json
import logging
import os
import time
import uuid
from collections.abc import Callable
from typing import (
    Any,
)

import requests

from spectra_assure_api_client import (
    SpectraAssureApiOperations,
    SpectraAssureDownloadCriteria,
)

logger = logging.getLogger()


# Status codes the program accepts besides success: 409 means the version
# already exists (a rerun over earlier test data), which x_main() handles; 429
# is the rate limit, which the SDK waits out itself (auto_adapt_to_throttle).
ACCEPTED_ERRORS = {409, 429}

# Run the Catalog section of x_main(): import a package from an external catalog,
# update it, publish, unpublish and detach it. Turn it off for an endpoint that
# does not offer the Catalog API yet; there every catalog call answers an error.
USE_CATALOG_API = True

# Run the Catalog section of x_main() and nothing else: for an endpoint where the
# Catalog API is new and there is little other data to test against (staging).
# tests/Makefile sets RLPORTAL_ONLY_CATALOG=1 when it is run with ONLY_CATALOG=1.
ONLY_CATALOG = os.environ.get("RLPORTAL_ONLY_CATALOG") == "1"


def fail_on_error(response: requests.Response, *args: Any, **kwargs: Any) -> None:
    """Stop the program on any error answer, so a run that is incomplete fails.

    Every request the client makes goes through its session, so this one check
    covers every call, also the downloads the SDK makes for us. Without it, a 404
    (for example from an endpoint without the File Stream) was printed and the
    program went on to "Done" and exit status 0.
    """
    if response.status_code >= 400 and response.status_code not in ACCEPTED_ERRORS:
        request = response.request
        raise RuntimeError(
            f"{request.method if request else '?'} {response.url} answered "
            f"{response.status_code}: {response.text[:300]}"
        )


def until_ready(call: Callable[[], requests.Response], what: str, limit: int = 600) -> requests.Response:
    """Repeat a call while the Portal answers 202 (not ready yet), then require 200.

    A report or an archive is answered with 202 until it is ready. Returning
    nothing for it would leave the run incomplete without saying so.
    """
    waited = 0
    while True:
        response = call()
        if response.status_code == 200:
            return response
        if response.status_code != 202:
            raise RuntimeError(f"{what}: expected 200, got {response.status_code}: {response.text[:300]}")
        if waited >= limit:
            raise RuntimeError(f"{what}: still not ready (202) after {limit} s")
        time.sleep(10)
        waited += 10


def make_api_client(
    *,
    organization: str,
    group: str,
    token: str,
    host: str | None = None,
    server: str | None = None,
) -> SpectraAssureApiOperations:

    api_client = SpectraAssureApiOperations(
        host=host,
        server=server,
        organization=organization,
        group=group,
        token=token,
        auto_adapt_to_throttle=True,
        timeout=60,
        # Verify TLS certificates. Only an endpoint with a self-signed certificate
        # turns this off; the tests set RLPORTAL_NO_SSL_VERIFY=1 for those.
        no_ssl_verify=os.environ.get("RLPORTAL_NO_SSL_VERIFY") == "1",
    )
    api_client.make_logger(my_logger=logger)  # use a build in default logger to file and stderr
    api_client.session.hooks["response"].append(fail_on_error)  # any error answer stops the program
    print(f"host: {host}, server: {server}, organization: {organization}, group: {group}")
    return api_client


# CREATE
def create_project(
    api_client: SpectraAssureApiOperations,
    project: str,
) -> None:
    qp: dict[str, Any] = {
        "description": "SDK created project",
    }
    rr = api_client.create(
        project=project,
        **qp,
    )
    print("Create project", project, rr.status_code, rr.text)


def create_package(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> None:
    qp: dict[str, Any] = {
        "description": "SDK created project",
    }

    rr = api_client.create(
        project=project,
        package=package,
        **qp,
    )
    print("Create package", project, package, rr.status_code, rr.text)


def scan_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    file_path: str,
) -> int:
    qp: dict[str, Any] = {
        "publisher": "ReversingLabs Testing",
        "product": "a reversingLabs test",
        "category": "Development",
        "license": "MIT License Modern Variant",
        "platform": "Containers",
        "release_date": f"{datetime.datetime.now()}",
        "build": "version",
    }

    # create a version with upload (scan)
    rr = api_client.scan(
        project=project,
        package=package,
        version=version,
        file_path=file_path,
        **qp,
    )
    print("Create/Scan Version", rr.status_code, rr.text)
    return int(rr.status_code)


def url_import_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    url: str,
    auth_user: str | None = None,
    auth_pass: str | None = None,
    bearer_token: str | None = None,
) -> int:
    # url: https://www.7-zip.org/a/7z2500-x64.exe
    qp: dict[str, Any] = {
        "replace": False,
        "force": True,
        "publisher": "ReversingLabs Testing",
        "product": "a reversingLabs test",
        "category": "Development",
        "license": "MIT License Modern Variant",
        "platform": "Containers",
        "release_date": f"{datetime.datetime.now()}",
        "build": "version",
    }

    # create a version with upload via url (url_import)
    rr = api_client.url_import(
        project=project,
        package=package,
        version=version,
        url=url,
        auth_user=auth_user,
        auth_pass=auth_pass,
        bearer_token=bearer_token,
        **qp,
    )

    print("url_import Version", rr.status_code, rr.text)
    return int(rr.status_code)


def purl_import_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    purl: str,
    auth_user: str | None = None,
    auth_pass: str | None = None,
    bearer_token: str | None = None,
) -> int:
    # purl: "pkg:pypi/pyaudio@0.2.13?artifact=PyAudio-0.2.13-cp311-cp311-win_amd64.whl"
    qp: dict[str, Any] = {
        "replace": False,
        "force": True,
        "publisher": "ReversingLabs Testing",
        "product": "a reversingLabs test",
        "category": "Development",
        "license": "MIT License Modern Variant",
        "platform": "Containers",
        "release_date": f"{datetime.datetime.now()}",
        "build": "version",
    }

    # create a version with upload via url (url_import)
    rr = api_client.purl_import(
        project=project,
        package=package,
        version=version,
        purl=purl,
        auth_user=auth_user,
        auth_pass=auth_pass,
        bearer_token=bearer_token,
        **qp,
    )

    print("purl_import Version", rr.status_code, rr.text)
    return int(rr.status_code)


# DELETE
def delete_project(
    api_client: SpectraAssureApiOperations,
    project: str,
) -> None:
    rr = api_client.delete(
        project=project,
    )
    print(f"Delete Project {project}", rr.status_code, rr.text)


def delete_package(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> None:
    rr = api_client.delete(
        project=project,
        package=package,
    )
    print(f"Delete Package {package}", rr.status_code, rr.text)


def delete_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
) -> None:
    rr = api_client.delete(
        project=project,
        package=package,
        version=version,
    )
    print(f"Delete Version {version}", rr.status_code, rr.text)


# LIST
def list_groups(
    api_client: SpectraAssureApiOperations,
) -> Any:
    response = api_client.list_groups()
    print("list_groups:", response)

    data = response.json()
    # print("list_groups: ", json.dumps(data, indent=2))
    return data


def list_projects(
    api_client: SpectraAssureApiOperations,
) -> Any:
    response = api_client.list()
    print("list_projects:", response)
    data = response.json()
    # print("Projects: ", json.dumps(data, indent=2))
    return data


def list_project(
    api_client: SpectraAssureApiOperations,
    project: str,
) -> Any:
    project_info = api_client.list(
        project=project,
    )
    print("list_project:", project_info)
    project_data = project_info.json()
    # print("Project detail: ", json.dumps(project_data, indent=2))
    return project_data


def list_package(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> Any:
    package_info = api_client.list(
        project=project,
        package=package,
    )
    print("list_package:", package_info)
    package_data = package_info.json()
    # print("Package details: ", json.dumps(package_data, indent=2))
    return package_data


def list_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
) -> Any:
    version_info = api_client.list(
        project=project,
        package=package,
        version=version,
    )
    print("list_version:", version_info)
    # print("Version details: ", version_info.status_code)
    version_data = version_info.json()
    # print("Version details: ", json.dumps(version_data, indent=2))
    return version_data


# EDIT/UPDATE
def edit_project(
    api_client: SpectraAssureApiOperations,
    project: str,
) -> None:
    qp: dict[str, Any] = {
        "description": "API edited",
        "name": project,
    }
    rr = api_client.edit(
        project=project,
        **qp,
    )
    print("Update project", rr.status_code, rr.text)


def edit_package(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> None:
    qp: dict[str, Any] = {
        "description": "API edited",
        "name": package,
    }
    rr = api_client.edit(
        project=project,
        package=package,
        **qp,
    )
    print("Update package", rr.status_code, rr.text)


def edit_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
) -> None:
    qp: dict[str, Any] = {
        "publisher": "ReversingLabs Testing 2",
        "product": "a reversingLabs test 2",
        "license": "iMatix Standard Function Library Agreement",
    }

    rr = api_client.edit(
        project=project,
        package=package,
        version=version,
        **qp,
    )
    print("Update version", rr.status_code, rr.text)


# REPORT
def report_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    report_type: str,
) -> Any:
    report_data = until_ready(
        lambda: api_client.report(
            project=project,
            package=package,
            version=version,
            report_type=report_type,
        ),
        f"report {report_type}",
    )

    logger.debug("%s", report_data)

    # rl-cve and rl-uri are CSV, rl-summary-pdf is a PDF; the others are JSON
    if report_type in ["rl-cve", "rl-uri"]:
        return report_data.text

    if report_type.endswith("pdf"):
        return report_data.content

    return report_data.json()


# CHECK
def check_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
) -> None:
    rr = api_client.checks(
        project=project,
        package=package,
        version=version,
    )
    print("Version check:", rr.status_code)
    # print("Version check:", json.dumps(rr.json(), indent=2))


# STATUS
def status_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    with_download_url: bool = False,
) -> Any:
    qp: dict[str, Any] = {}

    if with_download_url is True:
        qp["download"] = True  # this will subtract from your quota

    version_check_response = api_client.status(
        project=project,
        package=package,
        version=version,
        **qp,
    )
    print(f"Version status check: {version_check_response.status_code}")
    # print(json.dumps(version_check_response.json(), indent=2))
    return version_check_response.json()


# SYNC
def sync_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
) -> Any:
    rr = api_client.sync(
        project=project,
        package=package,
        version=version,
    )
    print("Version sync", rr.status_code, rr.text)
    return rr


# APPROVE
def approve_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    reason: str,
) -> Any:
    rr = api_client.approve(
        project=project,
        package=package,
        version=version,
        reason=reason,
    )
    print("Version approve", rr.status_code, rr.text)
    return rr


# REJECT
def reject_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    reason: str,
) -> Any:
    rr = api_client.reject(
        project=project,
        package=package,
        version=version,
        reason=reason,
    )
    print("Version reject", rr.status_code, rr.text)
    return rr


# REVOKE
def revoke_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    reason: str,
) -> Any:
    rr = api_client.revoke(
        project=project,
        package=package,
        version=version,
        reason=reason,
    )
    print("Version revoke", rr.status_code, rr.text)
    return rr


# DOWNLOAD a approved version file
def download_versions(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> None:
    # download only works on approved versions,
    # so nothing will be produced here during automated testing
    # as approval is a manual action on the portal

    for available_strategy in [
        "AllApproved",  # select all
        "LatestApproved_ByApprovalTimeStamp",  # select only one
    ]:
        download_criteria = SpectraAssureDownloadCriteria(
            with_overwrite_existing_files=False,
            with_verify_existing_files=True,
            with_verify_after_download=True,
            current_strategy=available_strategy,
        )

        target_dir = "./downloads"
        if not os.path.isdir(target_dir):
            os.mkdir(target_dir)

        download_data = api_client.download(
            project=project,
            package=package,
            target_dir=target_dir,
            download_criteria=download_criteria,
        )
        print("Download details: ", json.dumps(download_data, indent=2))


# USAGE
def usage_organization(
    api_client: SpectraAssureApiOperations,
) -> Any:
    response = api_client.usage()
    data = response.json()
    print("ORG USAGE: ", json.dumps(data, indent=2))
    return data


def usage_group(
    api_client: SpectraAssureApiOperations,
    group: str,
) -> Any:
    response = api_client.usage(
        group=group,
    )
    data = response.json()
    print("GROUP USAGE: ", json.dumps(data, indent=2))
    return data


# RL_SAFE
def version_rl_safe(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    **qp: Any,
) -> Any:
    action = "Rl-Safe"

    rr = api_client.rl_safe(
        project=project,
        package=package,
        version=version,
        auto_adapt_to_throttle=True,
        **qp,
    )
    print("Version ", action, rr.status_code, rr.text)
    return rr


def version_rl_safe_with_download_and_rename(
    *,
    api_client: SpectraAssureApiOperations,
    target_dir: str,
    project: str,
    package: str,
    version: str,
    **qp: Any,
) -> tuple[bool, str]:
    action = "Rl-Safe with download and rename"

    download_ok, file_path = api_client.rl_safe_download(
        target_dir=target_dir,
        project=project,
        package=package,
        version=version,
        auto_adapt_to_throttle=True,
        **qp,
    )

    if download_ok is True:
        print("Version ", action, file_path)

    return download_ok, file_path


def makeFindQueries() -> dict[str, Any]:
    queries: dict[str, Any] = {}

    # ==================================
    myUuid = str(uuid.uuid4())
    myPurl = "pkg:pypi/numpy@2.3.5"
    query: dict[str, str] = {
        "uuid": myUuid,
        "purl": myPurl,
    }
    queries["FindByPurlOne"] = {
        "query": query,
        "qp": {},
    }

    # ==================================
    myUuid = str(uuid.uuid4())
    myPurl = "pkg:pypi/numpy"
    query = {
        "uuid": myUuid,
        "purl": myPurl,
    }
    queries["FindByPurlMany"] = {
        "query": query,
        "qp": {
            "offset": 1,
            "limit": 1,
            "compact": False,
        },
    }

    # ==================================
    myUuid = str(uuid.uuid4())
    sha256Hash = "fffe29a1ef00883599d1dc2c51aa2e5d80afe49523c261a74933df395c15c520"
    query = {
        "uuid": "1.2.3",
        "sha256": sha256Hash,
    }
    queries["FindBySha256"] = {
        "query": query,
        "qp": {},
    }

    return queries


def community_find_packages(
    api_client: SpectraAssureApiOperations,
) -> None:
    print("community_find_packages")

    for qName, query in makeFindQueries().items():
        post_data: list[Any] = [query["query"]]
        qp = query["qp"]

        print(f"qp: {qp}; post_data: {post_data}")

        result = api_client.community_find_packages(
            auto_adapt_to_throttle=True,
            post_data=post_data,
            **qp,
        )

        s = f"query: {qName} {query} gives:"
        print(f"{s} {result.status_code}")
        continue

        if result.status_code == 200:
            print(json.dumps(json.loads(result.text), indent=2))

    return None


def community_report_package(
    api_client: SpectraAssureApiOperations,
) -> None:
    qp: Any = None
    repository = "pypi"
    package = "numpy"
    namespace = ""
    # version = "2.3.5"
    print(f"query: pkg:{repository}/{namespace}/{package}")

    result = api_client.community_report_package(
        repository=repository,
        package=package,
        namespace=namespace,
        # version=version,
        qp=qp,
        auto_adapt_to_throttle=True,
    )
    print(f"community_report_package {result.status_code}")

    # if result.status_code == 200:
    #    print(json.dumps(json.loads(result.text), indent=2))

    return None


def community_report_version(
    api_client: SpectraAssureApiOperations,
) -> None:
    qp: Any = None
    repository = "pypi"
    package = "numpy"
    namespace = ""
    version = "2.3.5"

    print(f"query: pkg:{repository}/{namespace}/{package}@{version}")

    result = api_client.community_report_version(
        repository=repository,
        package=package,
        namespace=namespace,
        version=version,
        qp=qp,
        auto_adapt_to_throttle=True,
    )

    print(f"community_report_version {result.status_code}")
    if result.status_code == 200:
        print(json.dumps(json.loads(result.text), indent=2))

    return None


def community_user_account(
    api_client: SpectraAssureApiOperations,
) -> None:
    result = api_client.community_user_account(
        auto_adapt_to_throttle=True,
    )

    print(f"community_user_account: {result.status_code}")
    if result.status_code == 200:
        print(json.dumps(json.loads(result.text), indent=2))

    return None


def export_profile(
    api_client: SpectraAssureApiOperations,
    organization: str,
    group: str | None = None,
) -> str:

    result = api_client.export_profile(
        organization=organization,
        group=group,
        auto_adapt_to_throttle=True,
    )

    if result.status_code != 200:
        raise RuntimeError(f"export_profile {organization} {group}: expected 200, got {result.status_code}")

    f_name = f"export_profile.{organization}.{group}.json"
    data = json.dumps(json.loads(result.text))
    print(f"export_profile {organization} {group}\n {data}")
    with open(f_name, "wb") as f:
        f.write(bytes(data, "utf-8"))
    return f_name


def import_profile(
    api_client: SpectraAssureApiOperations,
    *,
    file_path: str,
    organization: str,
    group: str | None = None,
    replace: bool = True,  # default is to replace the full profile
) -> None:

    result = api_client.import_profile(
        file_path=file_path,
        organization=organization,
        group=group,
        replace=replace,
        auto_adapt_to_throttle=True,
    )

    print(f"import_profile, {file_path} {organization} {group} {replace} {result.status_code}")

    return None


def audit_log_export(
    api_client: SpectraAssureApiOperations,
    *,
    name: str,
    should_create_cef: bool,
    should_create_ndjson: bool,
    datetime_start: str,
    datetime_end: str,
    filters: list[Any] | None = None,
) -> str:
    print("==================== Audit Log Export =========================")
    name = str(uuid.uuid1())
    should_create_cef = True
    should_create_ndjson = True

    r1 = api_client.audit_log_export(
        name=name,
        should_create_cef=should_create_cef,
        should_create_ndjson=should_create_ndjson,
        datetime_end=datetime_end,
        datetime_start=datetime_start,
        filters=filters,
    )
    print("audit-log-export response", r1, r1.json())

    my_id = r1.json().get("id") or ""
    print("audit-log-export", my_id)

    return my_id


def audit_log_status(
    api_client: SpectraAssureApiOperations,
    *,
    job_id: str,
) -> Any:
    print("==================== Audit Log Export =========================")
    r2 = api_client.audit_log_status(
        job_id=job_id,
    )
    data = r2.json()
    print("response_status:", r2, "resonse_data:", data)
    return data


def walk_all_project_package_version(
    api_client: SpectraAssureApiOperations,
    limit_projects: int = 2,
    limit_packages: int = 2,
    limit_versions: int = 2,
) -> None:
    # read only
    data = list_projects(
        api_client=api_client,
    )

    project_n = 0
    for project in data["projects"]:
        if project_n > limit_projects:
            break

        project_n += 1

        project_data = list_project(
            api_client=api_client,
            project=project["name"],
        )

        package_n = 0
        for package in project_data["packages"]:
            if package_n > limit_packages:
                break

            package_n += 1

            package_data = list_package(
                api_client=api_client,
                project=project["name"],
                package=package["name"],
            )

            # package level
            download_versions(
                api_client=api_client,
                project=project["name"],
                package=package["name"],
            )

            version_n = 0
            for version in package_data["versions"]:
                if version_n > limit_versions:
                    break
                version_n += 1

                # version level
                list_version(
                    api_client=api_client,
                    project=project["name"],
                    package=package["name"],
                    version=version["version"],
                )

                r = report_version(
                    api_client=api_client,
                    project=project["name"],
                    package=package["name"],
                    version=version["version"],
                    report_type="rl-uri",
                )
                logger.debug("%s", r)

                r = report_version(
                    api_client=api_client,
                    project=project["name"],
                    package=package["name"],
                    version=version["version"],
                    report_type="rl-json",
                )
                logger.debug("%s", r)

                check_version(
                    api_client=api_client,
                    project=project["name"],
                    package=package["name"],
                    version=version["version"],
                )

                status_version(
                    api_client=api_client,
                    project=project["name"],
                    package=package["name"],
                    version=version["version"],
                    with_download_url=False,
                )

                version_rl_safe_with_download_and_rename(
                    api_client=api_client,
                    target_dir="./downloads",
                    project=project["name"],
                    package=package["name"],
                    version=version["version"],
                )


# ======================================================================
# FILE STREAM
#
# File Stream files are standalone: they do not belong to a project or a
# package, and they have no versions. A server-generated `file_id` is the only
# handle, so every call below takes one, except the three that create a file and
# return the id.
# ======================================================================


# FILE STREAM: SCAN (upload)
def filestream_scan_file(
    api_client: SpectraAssureApiOperations,
    file_path: str,
) -> str:
    qp: dict[str, Any] = {
        "publisher": "ReversingLabs Testing",
        "product": "a reversingLabs test",
        "category": "Development",
        "license": "MIT License Modern Variant",
        "platform": "Containers",
        "release_date": f"{datetime.datetime.now()}",
        "version": "2026.04.09",  # metadata only: File Stream files have no versions
    }

    rr = api_client.filestream_scan(
        file_path=file_path,
        **qp,
    )
    print("Filestream scan", rr.status_code, rr.text)

    if rr.status_code not in [200, 201]:
        raise RuntimeError(f"expected 200 or 201, got {rr.status_code}: {rr.text[:300]}")

    file_id = str(rr.json().get("id"))
    print("Filestream scan, new file_id:", file_id)
    return file_id


# FILE STREAM: URL IMPORT
def filestream_url_import_file(
    api_client: SpectraAssureApiOperations,
    url: str,
    auth_user: str | None = None,
    auth_pass: str | None = None,
    bearer_token: str | None = None,
) -> str:
    # url: https://www.7-zip.org/a/7z2500-x64.exe
    qp: dict[str, Any] = {
        "publisher": "ReversingLabs Testing",
        "product": "a reversingLabs test",
        "category": "Development",
        "license": "MIT License Modern Variant",
        "platform": "Containers",
        "release_date": f"{datetime.datetime.now()}",
    }

    rr = api_client.filestream_url_import(
        url=url,
        auth_user=auth_user,
        auth_pass=auth_pass,
        bearer_token=bearer_token,
        **qp,
    )
    print("Filestream url_import", rr.status_code, rr.text)

    if rr.status_code not in [200, 201]:
        raise RuntimeError(f"expected 200 or 201, got {rr.status_code}: {rr.text[:300]}")

    return str(rr.json().get("id"))


# FILE STREAM: PURL IMPORT
def filestream_purl_import_file(
    api_client: SpectraAssureApiOperations,
    purl: str,
    auth_user: str | None = None,
    auth_pass: str | None = None,
    bearer_token: str | None = None,
) -> str:
    # purl: pkg:pypi/pyaudio@0.2.13?artifact=PyAudio-0.2.13-cp311-cp311-win_amd64.whl
    qp: dict[str, Any] = {
        "publisher": "ReversingLabs Testing",
        "product": "a reversingLabs test",
        "category": "Development",
        "license": "MIT License Modern Variant",
        "platform": "Containers",
        "release_date": f"{datetime.datetime.now()}",
    }

    rr = api_client.filestream_purl_import(
        purl=purl,
        auth_user=auth_user,
        auth_pass=auth_pass,
        bearer_token=bearer_token,
        **qp,
    )
    print("Filestream purl_import", rr.status_code, rr.text)

    if rr.status_code not in [200, 201]:
        raise RuntimeError(f"expected 200 or 201, got {rr.status_code}: {rr.text[:300]}")

    return str(rr.json().get("id"))


# FILE STREAM: LIST
def filestream_list_files(
    api_client: SpectraAssureApiOperations,
    limit: int = 10,
    offset: int = 0,
) -> Any:
    qp: dict[str, Any] = {
        "limit": limit,
        "offset": offset,
        "sort_by": "-upload_date",  # most recently uploaded first
    }

    response = api_client.filestream_list(
        **qp,
    )
    print("Filestream list:", response.status_code)
    # print(json.dumps(response.json(), indent=2))
    return response.json()


# FILE STREAM: STATUS
def filestream_status_file(
    api_client: SpectraAssureApiOperations,
    file_id: str,
    with_download_url: bool = False,
) -> Any:
    qp: dict[str, Any] = {}

    if with_download_url is True:
        qp["download"] = True  # this will subtract from your quota

    response = api_client.filestream_status(
        file_id=file_id,
        **qp,
    )
    print(f"Filestream status check: {response.status_code}")
    # print(json.dumps(response.json(), indent=2))
    return response.json()


def filestream_wait_for_analysis(
    api_client: SpectraAssureApiOperations,
    file_id: str,
    max_wait: int = 600,
) -> None:
    n = 0
    step = 10

    while True:
        status = filestream_status_file(
            api_client=api_client,
            file_id=file_id,
        )
        state = status.get("analysis", {}).get("status", "").lower()
        if state == "done":
            return
        if state == "error":
            raise RuntimeError(f"the analysis of File Stream file {file_id} ended in ERROR")
        if n >= max_wait:
            raise RuntimeError(f"the analysis of File Stream file {file_id} took more than {max_wait} s")

        time.sleep(step)  # give the analyzer time to finish
        n = n + step
        print(f"wait for filestream scan status to complete: {n}")


# FILE STREAM: CHECK
def filestream_check_file(
    api_client: SpectraAssureApiOperations,
    file_id: str,
) -> None:
    rr = api_client.filestream_checks(
        file_id=file_id,
    )
    print("Filestream check:", rr.status_code)
    # print("Filestream check:", json.dumps(rr.json(), indent=2))


# FILE STREAM: REPORT
def filestream_report_file(
    api_client: SpectraAssureApiOperations,
    file_id: str,
    report_type: str,
) -> Any:
    # The supported report types are: cyclonedx, rl-checks, rl-cve, rl-json,
    # rl-summary-pdf, rl-uri, sarif, spdx.
    # 'rl-diff' is not supported: File Stream files have no versions to diff.
    print("Supported report types:", api_client.filestream_report_types())

    # 202 means the analysis has not finished yet; until_ready asks again
    report_data = until_ready(
        lambda: api_client.filestream_report(
            file_id=file_id,
            report_type=report_type,
        ),
        f"Filestream report {report_type}",
    )
    print(f"Filestream report {report_type}: {report_data.status_code}")

    # not all reports are json: rl-summary-pdf returns a pdf document
    if report_type in ["rl-summary-pdf"]:
        return report_data.content

    return report_data.json()


# FILE STREAM: SYNC
def filestream_sync_file(
    api_client: SpectraAssureApiOperations,
    file_id: str,
) -> Any:
    # 202: a re-scan was started. 200: the analysis is already up to date.
    rr = api_client.filestream_sync(
        file_id=file_id,
    )
    print("Filestream sync", rr.status_code, rr.text)
    return rr


# FILE STREAM: APPROVE
def filestream_approve_file(
    api_client: SpectraAssureApiOperations,
    file_id: str,
    reason: str,
) -> Any:
    # unlike the project/package/version approve(), 'reason' is mandatory here
    rr = api_client.filestream_approve(
        file_id=file_id,
        reason=reason,
    )
    print("Filestream approve", rr.status_code, rr.text)
    return rr


# FILE STREAM: REJECT
def filestream_reject_file(
    api_client: SpectraAssureApiOperations,
    file_id: str,
    reason: str,
) -> Any:
    # unlike the project/package/version reject(), 'reason' is mandatory here
    rr = api_client.filestream_reject(
        file_id=file_id,
        reason=reason,
    )
    print("Filestream reject", rr.status_code, rr.text)
    return rr


# FILE STREAM: REVOKE
def filestream_revoke_file(
    api_client: SpectraAssureApiOperations,
    file_id: str,
    reason: str,
) -> Any:
    # unlike the project/package/version revoke(), 'reason' is mandatory here
    rr = api_client.filestream_revoke(
        file_id=file_id,
        reason=reason,
    )
    print("Filestream revoke", rr.status_code, rr.text)
    return rr


# FILE STREAM: RL_SAFE
def filestream_rl_safe_file(
    api_client: SpectraAssureApiOperations,
    file_id: str,
) -> Any:
    # 202 means the analysis has not finished yet; the archive is not ready
    rr = api_client.filestream_rl_safe(
        file_id=file_id,
    )
    print("Filestream rl_safe", rr.status_code, rr.text)
    return rr


def filestream_rl_safe_with_download_and_rename(
    api_client: SpectraAssureApiOperations,
    target_dir: str,
    file_id: str,
    max_wait_time_for_archive: int = 300,
) -> Any:
    # the archive is renamed to '<file_id>.rl-safe':
    # File Stream files have no purl to name the archive after.
    #
    # While the analysis is still running the API answers 202 and no archive
    # exists yet; the SDK waits up to 'max_wait_time_for_archive' seconds for it.
    # Pass 0 to fail immediately instead of waiting.
    download_ok, file_path = api_client.filestream_rl_safe_download(
        target_dir=target_dir,
        file_id=file_id,
        rename_archive=True,
        max_wait_time_for_archive=max_wait_time_for_archive,
    )
    print("Filestream rl_safe download", download_ok, file_path)
    return download_ok, file_path


# FILE STREAM: DOWNLOAD an approved file
def filestream_download_file(
    api_client: SpectraAssureApiOperations,
    target_dir: str,
    file_id: str,
) -> Any:
    download_criteria = SpectraAssureDownloadCriteria(
        wait_for_scan_done=True,
        max_wait_time_for_scan_done=60,
        with_overwrite_existing_files=False,
        with_verify_after_download=True,
        with_verify_existing_files=True,
        # 'current_strategy' has no effect here:
        # there are no versions to choose between
    )

    download_data = api_client.filestream_download(
        target_dir=target_dir,
        file_id=file_id,
        download_criteria=download_criteria,
    )
    print("Filestream download:", json.dumps(download_data, indent=2, default=str))
    return download_data


# FILE STREAM: DELETE
def filestream_delete_file(
    api_client: SpectraAssureApiOperations,
    file_id: str,
) -> Any:
    rr = api_client.filestream_delete(
        file_id=file_id,
    )
    print("Filestream delete", rr.status_code, rr.text)
    return rr


def walk_all_filestream_files(
    api_client: SpectraAssureApiOperations,
    limit_files: int = 2,
) -> None:
    # read only
    data = filestream_list_files(
        api_client=api_client,
        limit=limit_files,
    )

    for item in data.get("files", []):
        file_id = item.get("id")
        print(
            "Filestream file:",
            file_id,
            item.get("file_name"),
            item.get("status"),
            item.get("approval_status"),
        )

        filestream_status_file(
            api_client=api_client,
            file_id=file_id,
        )

        # checks, reports and the rl-safe archive all answer 202 until the
        # analysis is done. This is a survey of whatever happens to be in the
        # group, so skip anything still being processed rather than waiting.
        if str(item.get("status", "")).upper() != "DONE":
            print("  still processing; skipping checks, report and archive")
            continue

        filestream_check_file(
            api_client=api_client,
            file_id=file_id,
        )

        r = filestream_report_file(
            api_client=api_client,
            file_id=file_id,
            report_type="rl-uri",
        )
        logger.debug("%s", r)

        filestream_rl_safe_with_download_and_rename(
            api_client=api_client,
            target_dir="./downloads",
            file_id=file_id,
        )


def filestream_main(
    api_client: SpectraAssureApiOperations,
    file_path: str,
    with_reject: bool = False,
    with_delete: bool = True,
) -> None:
    print("==================== File Stream =========================")

    file_id = filestream_scan_file(
        api_client=api_client,
        file_path=file_path,
    )
    filestream_wait_for_analysis(api_client=api_client, file_id=file_id)

    filestream_list_files(
        api_client=api_client,
    )

    filestream_check_file(
        api_client=api_client,
        file_id=file_id,
    )

    filestream_report_file(
        api_client=api_client,
        file_id=file_id,
        report_type="rl-json",
    )

    if with_reject:
        filestream_reject_file(
            api_client=api_client,
            file_id=file_id,
            reason="Just a Reject test",
        )
    else:
        filestream_approve_file(
            api_client=api_client,
            file_id=file_id,
            reason="Just a Approve test",
        )

        filestream_download_file(
            api_client=api_client,
            target_dir="./downloads",
            file_id=file_id,
        )

        filestream_rl_safe_file(
            api_client=api_client,
            file_id=file_id,
        )

        filestream_rl_safe_with_download_and_rename(
            api_client=api_client,
            target_dir="./downloads",
            file_id=file_id,
        )

        filestream_revoke_file(
            api_client=api_client,
            file_id=file_id,
            reason="Just a Revoke test",
        )

    # sync last: it may start a re-scan, and approve/reject/revoke all require
    # a fully processed file. Returns 202 when a re-scan starts, 200 when the
    # analysis is already up to date.
    filestream_sync_file(
        api_client=api_client,
        file_id=file_id,
    )

    # import a file into the File Stream from a url and from a purl
    url_file_id = filestream_url_import_file(
        api_client=api_client,
        url="https://www.7-zip.org/a/7z2500-x64.exe",
    )

    purl_file_id = filestream_purl_import_file(
        api_client=api_client,
        purl="pkg:pypi/pyaudio@0.2.13?artifact=PyAudio-0.2.13-cp311-cp311-win_amd64.whl",
    )

    walk_all_filestream_files(
        api_client=api_client,
    )

    if with_delete:
        for what in [file_id, url_file_id, purl_file_id]:
            filestream_delete_file(
                api_client=api_client,
                file_id=what,
            )


# CATALOG: READ AN EXTERNAL CATALOG
def catalog_get_external_catalog(
    api_client: SpectraAssureApiOperations,
    catalog: str = "reversinglabs",
) -> Any:
    rr = api_client.get_external_catalog(
        catalog=catalog,
    )
    print("Catalog get_external_catalog", rr.status_code)

    if rr.status_code != 200:
        raise RuntimeError(f"expected 200, got {rr.status_code}: {rr.text[:300]}")

    # every entry's `id` is a software_id; each of its `streams` has an `id` to import
    return rr.json()


# CATALOG: LIST THE PACKAGES PUBLISHED IN THE GROUP'S CATALOG
def catalog_list_catalog_packages(
    api_client: SpectraAssureApiOperations,
) -> Any:
    rr = api_client.list_catalog_packages()
    print("Catalog list_catalog_packages", rr.status_code, rr.text)
    return rr.json()


# CATALOG: IMPORT SOFTWARE FROM AN EXTERNAL CATALOG
def catalog_import_from_catalog(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    software_id: str,
    stream: str,
    catalog: str = "reversinglabs",
    versions: list[str] | None = None,
) -> Any:
    # the project is created if it does not exist; the package must not exist yet
    rr = api_client.import_from_catalog(
        catalog=catalog,
        project=project,
        package=package,
        software_id=software_id,
        stream=stream,
        versions=versions,  # None: the stream's newest versions
        auto_sync=False,
        package_description="imported from the catalog",
    )
    print("Catalog import_from_catalog", rr.status_code, rr.text)

    if rr.status_code != 201:
        raise RuntimeError(f"expected 201, got {rr.status_code}: {rr.text[:300]}")

    return rr.json().get("imported_versions")


# CATALOG: IMPORT NEWER VERSIONS FROM THE LINKED CATALOG
def catalog_update_from_catalog(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    versions: list[str] | None = None,
) -> Any:
    rr = api_client.update_from_catalog(
        project=project,
        package=package,
        versions=versions,  # None: every version newer than the package's newest one
    )
    print("Catalog update_from_catalog", rr.status_code, rr.text)

    # 201: versions were imported; 200: there was nothing newer
    if rr.status_code not in [200, 201]:
        raise RuntimeError(f"expected 200 or 201, got {rr.status_code}: {rr.text[:300]}")

    return rr.json().get("imported_versions")


# CATALOG: PUBLISH A PACKAGE TO THE GROUP'S CATALOG
def catalog_publish_package_to_catalog(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> Any:
    # the package needs at least one approved version
    rr = api_client.publish_package_to_catalog(
        project=project,
        package=package,
    )
    print("Catalog publish_package_to_catalog", rr.status_code, rr.text)
    return rr


# CATALOG: REMOVE A PACKAGE FROM THE GROUP'S CATALOG
def catalog_unpublish_package_from_catalog(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> Any:
    rr = api_client.unpublish_package_from_catalog(
        project=project,
        package=package,
    )
    print("Catalog unpublish_package_from_catalog", rr.status_code, rr.text)
    return rr


# CATALOG: UNLINK A PACKAGE FROM ITS EXTERNAL CATALOG
def catalog_detach_from_catalog(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> Any:
    # the package and its versions are kept, but no longer updated from the catalog
    rr = api_client.detach_from_catalog(
        project=project,
        package=package,
    )
    print("Catalog detach_from_catalog", rr.status_code, rr.text)
    return rr


# CATALOG: THE SCENARIO x_main() RUNS WHEN USE_CATALOG_API IS ON
def catalog_candidates(
    document: Any,
    skip_streams: set[str],
) -> list[tuple[str, str, str, str]]:
    """Streams worth importing for a test, smallest first: (software_id, stream, older, newer).

    A stream qualifies when it has at least two versions, so one can be imported
    and the other added later with update_from_catalog(). Streams already
    imported into the group are skipped: the API refuses a second import (400).
    """
    found: list[tuple[int, str, str, str, str]] = []
    for software in document.get("software", []):
        for stream in software.get("streams") or []:
            stream_id = stream.get("id")
            if not stream_id or stream_id in skip_streams:
                continue
            # versions are listed newest first; keep those with an artifact in this stream
            versions = [
                v
                for v in software.get("versions", [])
                if any(a.get("stream") == stream_id for a in v.get("artifacts", []))
            ]
            if len(versions) < 2:
                continue
            size = max(
                a.get("size") or 10**12  # unknown sizes last
                for v in versions[:2]
                for a in v["artifacts"]
                if a.get("stream") == stream_id
            )
            found.append((size, software["id"], stream_id, versions[1]["version"], versions[0]["version"]))
    return [entry[1:] for entry in sorted(found)]


def catalog_is_published(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> bool:
    data = catalog_list_catalog_packages(api_client=api_client)
    return any(p.get("project_name") == project and p.get("package_name") == package for p in data.get("packages", []))


def catalog_wait_for_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    max_wait: int = 1800,
) -> None:
    """Imported versions are analyzed in the background; approval needs a finished analysis."""
    n = 0
    step = 15

    while True:
        status = status_version(
            api_client=api_client,
            project=project,
            package=package,
            version=version,
        )
        state = str(status.get("analysis", {}).get("status", "")).lower()
        if state == "done":
            return
        if state == "error":
            raise RuntimeError(f"the analysis of {project}/{package}@{version} ended in ERROR")
        if n >= max_wait:
            raise RuntimeError(f"the analysis of {project}/{package}@{version} took more than {max_wait} s")

        time.sleep(step)
        n = n + step
        print(f"wait for the imported version to be analyzed: {n}")


def catalog_main(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    catalog: str = "reversinglabs",
    with_delete: bool = True,
) -> None:
    print("==================== Catalog =========================")

    # a manual run uses fixed names: remove what an earlier run left
    if any(p["name"] == project for p in list_projects(api_client=api_client)["projects"]):
        delete_project(api_client=api_client, project=project)

    # 1. read the external catalog and pick something small to import
    document = catalog_get_external_catalog(api_client=api_client, catalog=catalog)
    published = catalog_list_catalog_packages(api_client=api_client)
    imported_streams = {
        p["external_catalog"]["stream"] for p in published.get("packages", []) if p.get("external_catalog")
    }
    candidates = catalog_candidates(document, imported_streams)
    print(f"Catalog {catalog}: {len(document.get('software', []))} entries, {len(candidates)} candidate streams")
    if not candidates:
        raise RuntimeError(f"catalog {catalog} offers no stream with two versions to import")

    # 2. import the older of two versions; a stream that is already imported
    #    (but not published, so not seen above) is refused with 400: try the next
    for candidate in candidates[:5]:
        software_id, stream, older, newer = candidate
        try:
            imported = catalog_import_from_catalog(
                api_client=api_client,
                project=project,
                package=package,
                software_id=software_id,
                stream=stream,
                catalog=catalog,
                versions=[older],
            )
            break
        except RuntimeError as exc:
            if "already been imported" not in str(exc):
                raise
            print(f"stream {stream} is already imported into the group; trying the next one")
    else:
        raise RuntimeError("the first five candidate streams are all imported into the group already")

    print(f"imported {software_id} stream {stream}: {imported}")

    # 3. the package is linked to the catalog
    package_data = list_package(api_client=api_client, project=project, package=package)
    link = package_data.get("external_catalog") or {}
    if (link.get("software_id"), link.get("stream")) != (software_id, stream):
        raise RuntimeError(f"expected the package to be linked to {software_id}/{stream}, got {link}")
    first_version = package_data["versions"][0]["version"]

    # 4. import the newer version; asking for it again answers 409 (it exists)
    updated = catalog_update_from_catalog(
        api_client=api_client,
        project=project,
        package=package,
        versions=[newer],
    )
    print(f"update imported: {updated}")
    rr = api_client.update_from_catalog(project=project, package=package, versions=[newer])
    if rr.status_code != 409:
        raise RuntimeError(f"importing {newer} a second time: expected 409, got {rr.status_code}: {rr.text[:300]}")

    # 5. approving the first version publishes an imported package automatically
    catalog_wait_for_version(api_client=api_client, project=project, package=package, version=first_version)
    approve_version(
        api_client=api_client,
        project=project,
        package=package,
        version=first_version,
        reason="Catalog API test: approve to publish",
    )
    if not catalog_is_published(api_client=api_client, project=project, package=package):
        raise RuntimeError("the imported package was not published when its first version was approved")

    # 6. publishing again has no effect; unpublish removes it; publish brings it back
    catalog_publish_package_to_catalog(api_client=api_client, project=project, package=package)
    catalog_unpublish_package_from_catalog(api_client=api_client, project=project, package=package)
    if catalog_is_published(api_client=api_client, project=project, package=package):
        raise RuntimeError("the package is still listed after unpublishing it")
    catalog_publish_package_to_catalog(api_client=api_client, project=project, package=package)
    if not catalog_is_published(api_client=api_client, project=project, package=package):
        raise RuntimeError("the package is not listed after publishing it")

    # 7. detach: the package stays, the link goes
    catalog_detach_from_catalog(api_client=api_client, project=project, package=package)
    package_data = list_package(api_client=api_client, project=project, package=package)
    if package_data.get("external_catalog") is not None:
        raise RuntimeError(f"the package is still linked after detaching it: {package_data['external_catalog']}")

    if with_delete:
        catalog_unpublish_package_from_catalog(api_client=api_client, project=project, package=package)
        delete_project(api_client=api_client, project=project)


def x_main() -> None:
    prefix = "RLPORTAL_"

    # os.environ[...] fails at once when a required setting is missing;
    # str(os.getenv(...)) would pass the text "None" on as a name.
    host = os.environ.get(f"{prefix}HOST")  # host, server or both
    server = os.environ.get(f"{prefix}SERVER")
    organization = os.environ[f"{prefix}ORG"]
    group = os.environ[f"{prefix}GROUP"]
    token = os.environ[f"{prefix}ACCESS_TOKEN"]

    api_client = make_api_client(
        host=host,
        server=server,
        organization=organization,
        group=group,
        token=token,
    )
    with_reject = False
    with_delete = True

    if ONLY_CATALOG:
        if not USE_CATALOG_API:
            raise RuntimeError("RLPORTAL_ONLY_CATALOG=1 asks for the Catalog section, but USE_CATALOG_API is off")
        run_id = os.environ.get(f"{prefix}RUN_ID")
        catalog_main(
            api_client=api_client,
            project=f"{run_id}-catalog" if run_id else "SDKTestCatalog202604",
            package="SDKTestCatalogPackage",
            with_delete=with_delete,
        )
        print("Done (Catalog only)")
        return

    list_groups(
        api_client=api_client,
    )

    usage_organization(
        api_client=api_client,
    )
    usage_group(
        api_client=api_client,
        group=group,
    )

    community_find_packages(
        api_client=api_client,
    )
    community_report_package(
        api_client=api_client,
    )
    community_report_version(
        api_client=api_client,
    )
    community_user_account(
        api_client=api_client,
    )

    # The integration tests set RLPORTAL_RUN_ID, so every run uses its own
    # project and `make sweep` recognises it if a run is interrupted. A manual
    # run uses fixed names; a rerun over them is handled below (status 409).
    run_id = os.environ.get(f"{prefix}RUN_ID")
    new_project = f"{run_id}-example" if run_id else "SDKTestProject202604"
    new_package = "SDKTestPackage202604"
    new_version = "2026.04.09"
    file_path = "api_client_example.py"  # use my self as scan file

    create_project(
        api_client=api_client,
        project=new_project,
    )

    create_package(
        api_client=api_client,
        project=new_project,
        package=new_package,
    )

    status_code = scan_version(
        api_client=api_client,
        project=new_project,
        package=new_package,
        version=new_version,
        file_path=file_path,
    )

    status_code = url_import_version(
        api_client=api_client,
        project=new_project,
        package="7-zip",
        version="25.00-x64",
        url="https://www.7-zip.org/a/7z2500-x64.exe",
    )

    status_code = purl_import_version(
        api_client=api_client,
        project=new_project,
        package="pyaudio",
        version="0.2.13",
        purl="pkg:pypi/pyaudio@0.2.13?artifact=PyAudio-0.2.13-cp311-cp311-win_amd64.whl",
    )

    n = 0
    limit = 1800  # seconds
    while True:
        m = 10
        status = status_version(
            api_client=api_client,
            project=new_project,
            package=new_package,
            version=new_version,
        )
        state = status.get("analysis", {}).get("status", "").lower()
        if state == "done":
            break
        if state == "error":
            raise RuntimeError(f"the analysis of {new_project}/{new_package}@{new_version} ended in ERROR")
        if n > limit:
            raise RuntimeError(f"the analysis of {new_project}/{new_package}@{new_version} took more than {limit} s")
        time.sleep(m)  # give the analizer time to finish
        n = n + m
        print(f"wait for scan status to complete: {n}")

    delete_test_data = True  # by default we delete what we create
    exists_test_data = status_code == 409  # version already exists this results to True

    if exists_test_data is True:
        delete_test_data = False  # but we will not delete previously existing data
    delete_test_data = True  # by default we delete what we create

    if exists_test_data is False:
        edit_project(
            api_client=api_client,
            project=new_project,
        )

        edit_package(
            api_client=api_client,
            project=new_project,
            package=new_package,
        )

        edit_version(
            api_client=api_client,
            project=new_project,
            package=new_package,
            version=new_version,
        )

        # sync
        sync_version(
            api_client=api_client,
            project=new_project,
            package=new_package,
            version=new_version,
        )

        list_version(
            api_client=api_client,
            project=new_project,
            package=new_package,
            version=new_version,
        )

        if with_reject:
            # reject
            reject_version(
                api_client=api_client,
                project=new_project,
                package=new_package,
                version=new_version,
                reason="Just a Reject test",
            )

            list_version(
                api_client=api_client,
                project=new_project,
                package=new_package,
                version=new_version,
            )
        else:
            # approve
            approve_version(
                api_client=api_client,
                project=new_project,
                package=new_package,
                version=new_version,
                reason="Just a Approve test",
            )

            list_version(
                api_client=api_client,
                project=new_project,
                package=new_package,
                version=new_version,
            )

            # revoke
            revoke_version(
                api_client=api_client,
                project=new_project,
                package=new_package,
                version=new_version,
                reason="Just a Revoke test",
            )

            list_version(
                api_client=api_client,
                project=new_project,
                package=new_package,
                version=new_version,
            )

    f_name_org: str = export_profile(
        api_client=api_client,
        organization=organization,
    )  # export org profile
    print(f"export_profile: f_name: {f_name_org}")

    f_name_group: str = export_profile(
        api_client=api_client,
        organization=organization,
        group=group,
    )  # export group profile
    print(f"export_profile: f_name: {f_name_group}")

    if f_name_org:
        import_profile(
            api_client=api_client,
            file_path=f_name_org,
            organization=organization,
            replace=True,
        )

    if f_name_group:
        import_profile(
            api_client=api_client,
            file_path=f_name_group,
            organization=organization,
            group=group,
            replace=True,
        )

    walk_all_project_package_version(
        api_client=api_client,
    )

    if with_delete and delete_test_data:
        delete_version(
            api_client=api_client,
            project=new_project,
            package=new_package,
            version=new_version,
        )

        delete_package(
            api_client=api_client,
            project=new_project,
            package=new_package,
        )

        delete_project(
            api_client=api_client,
            project=new_project,
        )

    filestream_main(
        api_client=api_client,
        file_path=file_path,  # use my self as scan file
        with_reject=with_reject,
        with_delete=with_delete,
    )

    if USE_CATALOG_API:
        catalog_main(
            api_client=api_client,
            project=f"{run_id}-catalog" if run_id else "SDKTestCatalog202604",
            package="SDKTestCatalogPackage",
            with_delete=with_delete,
        )

    name = str(uuid.uuid1())
    should_create_cef = True
    should_create_ndjson = True
    # the last 30 days: fixed dates drift out of the audit log's retention period
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    datetime_start = (now - datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    datetime_end = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    job_id = audit_log_export(
        api_client=api_client,
        name=name,
        should_create_cef=should_create_cef,
        should_create_ndjson=should_create_ndjson,
        datetime_end=datetime_end,
        datetime_start=datetime_start,
    )
    result = audit_log_status(
        api_client=api_client,
        job_id=job_id,
    )
    print("Audit Log Export Status", result)
    print("Done")


if __name__ == "__main__":
    os.environ["LOG_LEVEL"] = "DEBUG"  # set the default log level to INFO
    os.environ["ENVIRONMENT"] = "testing"  # in testing mode the log file uses DEBUG level

    logger.setLevel(logging.DEBUG)
    x_main()

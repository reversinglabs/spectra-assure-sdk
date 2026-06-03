import datetime
import json
import logging
import os
import sys
import time
import uuid
from typing import (
    Any,
)

from spectra_assure_api_client import (
    SpectraAssureApiOperations,
    SpectraAssureDownloadCriteria,
)

logger = logging.getLogger()


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
        no_ssl_verify=True,
    )
    api_client.make_logger(my_logger=logger)  # use a build in default logger to file and stderr
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
    response = api_client.listGroups()
    print("list_groups:", response)

    data = response.json()
    # print("listGroups: ", json.dumps(data, indent=2))
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
    report_data = api_client.report(
        project=project,
        package=package,
        version=version,
        report_type=report_type,
    )

    logger.debug("%s", report_data)

    try:
        # print("Report details:", report_type, report_data.text)

        if report_type in ["rl-cve", "rl-uri"]:
            # print("Report details:", report_data.text)
            return report_data.text

        if report_type.endswith("pdf"):
            return ""

        if len(report_data.text) == 0:
            return ""

        report_details = report_data.json()
        # print("Report details:", json.dumps(report_details, indent=2))
        return report_details

    except Exception as e:
        print(e, report_type, file=sys.stderr)
        return None


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
    reason: str | None = None,
) -> Any:
    qp: dict[str, Any] = {}
    if reason:
        qp["reason"] = reason

    rr = api_client.approve(
        project=project,
        package=package,
        version=version,
        **qp,
    )
    print("Version approve", rr.status_code, rr.text)
    return rr


# REJECT
def reject_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    reason: str | None = None,
) -> Any:
    qp: dict[str, Any] = {}
    if reason:
        qp["reason"] = reason

    rr = api_client.reject(
        project=project,
        package=package,
        version=version,
        **qp,
    )
    print("Version reject", rr.status_code, rr.text)
    return rr


# REVOKE
def revoke_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    reason: str | None = None,
) -> Any:
    qp: dict[str, Any] = {}
    if reason:
        qp["reason"] = reason

    rr = api_client.revoke(
        project=project,
        package=package,
        version=version,
        **qp,
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


def makeFindQueries() -> dict:
    queries: dict = {}

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
    query: dict[str, str] = {
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
    query: dict[str, str] = {
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
):
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
):
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
):
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
):
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
) -> str | None:

    result = api_client.export_profile(
        organization=organization,
        group=group,
        auto_adapt_to_throttle=True,
    )

    if result.status_code == 200:
        f_name = f"export_profile.{organization}.{group}.json"
        data = json.dumps(json.loads(result.text))
        print(f"export_profile {organization} {group}\n {data}")
        with open(f_name, "wb") as f:
            f.write(bytes(data, "utf-8"))
        return f_name

    return None


def import_profile(
    api_client: SpectraAssureApiOperations,
    *,
    file_path: str,
    organization: str,
    group: str | None = None,
    replace: bool = True,  # default is to replace the full profile
) -> Any:

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
    datetime_start = "2026-01-01T00:00:00Z"
    datetime_end = "2026-06-01T00:00:00Z"

    r1 = api_client.audit_log_export(
        name=name,
        should_create_cef=should_create_cef,
        should_create_ndjson=should_create_ndjson,
        datetime_end=datetime_end,
        datetime_start=datetime_start,
        filters=filters,
    )
    print("audit-log-export response", r1, r1.json())

    my_id = r1.json().get("id")
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
    print("response_status:", r2, "resonse_data:", r2.json())
    return r2.json


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


def x_main() -> None:
    prefix = "RLPORTAL_"

    host = os.getenv(f"{prefix}HOST")
    server = os.getenv(f"{prefix}SERVER")
    organization = str(os.getenv(f"{prefix}ORG"))
    group = str(os.getenv(f"{prefix}GROUP"))
    token = str(os.getenv(f"{prefix}ACCESS_TOKEN"))

    api_client = make_api_client(
        host=host,
        server=server,
        organization=organization,
        group=group,
        token=token,
    )
    with_reject = False
    with_delete = True

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

    new_project = "SDKTestProject202604"
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
    while True:
        m = 10
        status = status_version(
            api_client=api_client,
            project=new_project,
            package=new_package,
            version=new_version,
        )
        if status.get("analysis", {}).get("status", "").lower() == "done":
            break
        time.sleep(m)  # give the analizer time to finish
        n = n + m
        print(f"wait for scan status to complete: {n}")

    # if the version already exists we will not delete it later or modify it,
    # if we created it in this test we can delete it safely
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

    f_name_org: str | None = export_profile(
        api_client=api_client,
        organization=organization,
    )  # export org profile
    print(f"export_profile: f_name: {f_name_org}")

    f_name_group: str | None = export_profile(
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

    name = str(uuid.uuid1())
    should_create_cef = True
    should_create_ndjson = True
    datetime_start = "2026-05-01T00:00:00Z"
    datetime_end = "2026-06-30T00:00:00Z"

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

    x_main()

from typing import (
    Any,
    Dict,
)

import datetime
import time
import logging
import os
import json

from spectra_assure_api_client import (
    SpectraAssureApiOperations,
    SpectraAssureDownloadCriteria,
)

log = logging.getLogger()


def make_api_client() -> SpectraAssureApiOperations:
    os.environ["LOG_LEVEL"] = "INFO"  # set the default log level to INFO
    os.environ["ENVIRONMENT"] = "testing"  # in testing mode the log file uses DEBUG level

    prefix = "RLPORTAL_"
    api_client = SpectraAssureApiOperations(
        server=os.getenv(f"{prefix}SERVER"),
        organization=os.getenv(f"{prefix}ORG"),
        group=os.getenv(f"{prefix}GROUP"),
        token=os.getenv(f"{prefix}ACCESS_TOKEN"),
        auto_adapt_to_throttle=True,
        timeout=60,
    )
    api_client.make_logger(my_logger=log)  # use a build in default logger to file and stderr

    return api_client


# CREATE


def create_project(
    api_client: SpectraAssureApiOperations,
    project: str,
) -> None:
    qp: Dict[str, Any] = {
        "description": "SDK created project",
    }
    rr = api_client.create(
        project=project,
        **qp,
    )
    print("Create project", rr.status_code, rr.text)


def create_package(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> None:
    qp: Dict[str, Any] = {
        "description": "SDK created project",
    }

    rr = api_client.create(
        project=project,
        package=package,
        **qp,
    )
    print("Create package", rr.status_code, rr.text)


def scan_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    file_path: str,
) -> int:
    qp: Dict[str, Any] = {
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


def list_projects(
    api_client: SpectraAssureApiOperations,
) -> Any:
    response = api_client.list()
    data = response.json()
    print("Projects: ", json.dumps(data, indent=2))
    return data


def list_project(
    api_client: SpectraAssureApiOperations,
    project: str,
) -> Any:
    project_info = api_client.list(
        project=project,
    )
    project_data = project_info.json()
    print("Project detail: ", json.dumps(project_data, indent=2))
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
    package_data = package_info.json()
    print("Package details: ", json.dumps(package_data, indent=2))
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
    version_data = version_info.json()
    print("Version details: ", json.dumps(version_data, indent=2))
    return version_data


# EDIT/UPDATE


def edit_project(
    api_client: SpectraAssureApiOperations,
    project: str,
) -> None:
    qp: Dict[str, Any] = {
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
    qp: Dict[str, Any] = {
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
    qp: Dict[str, Any] = {
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
    if "cve" in report_type:
        print("Report details:", report_data.text)
        return report_data.text
    else:
        report_details = report_data.json()
        print("Report details:", json.dumps(report_details, indent=2))
        return report_details


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
    print("Version check:", json.dumps(rr.json(), indent=2))


# STATUS
def status_version(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
    version: str,
    with_download_url: bool = False,
) -> Any:
    qp: Dict[str, Any] = {}

    if with_download_url is True:
        qp["download"] = True  # this will subtract from your quota

    version_check_response = api_client.status(
        project=project,
        package=package,
        version=version,
        **qp,
    )
    print("Version status check:")
    print(json.dumps(version_check_response.json(), indent=2))
    return version_check_response.json()


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


def walk_all_project_package_version(
    api_client: SpectraAssureApiOperations,
) -> None:
    # read only
    data = list_projects(
        api_client=api_client,
    )

    for project in data["projects"]:
        project_data = list_project(
            api_client=api_client,
            project=project["name"],
        )

        for package in project_data["packages"]:
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

            for version in package_data["versions"]:
                # version level
                list_version(
                    api_client=api_client,
                    project=project["name"],
                    package=package["name"],
                    version=version["version"],
                )

                report_version(
                    api_client=api_client,
                    project=project["name"],
                    package=package["name"],
                    version=version["version"],
                    report_type="rl-uri",
                    # report_type="rl-json",
                )

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


def x_main() -> None:
    api_client = make_api_client()

    new_project = "SDK test project"
    new_package = "SDK test package"
    new_version = "2024.1"
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

    walk_all_project_package_version(
        api_client=api_client,
    )

    if delete_test_data:
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

    print("Done")


if __name__ == "__main__":
    x_main()

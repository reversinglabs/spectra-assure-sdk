"""Delete what earlier integration-test runs left on one endpoint.

Run by `make sweep ENDPOINT=<name>`, with the endpoint's settings in the
environment. Every project the pytest suite creates is named
sdktest-<endpoint>-<yyyymmdd>-<hhmmss>-<random>, and a run deletes it at its
end; a run that was interrupted cannot. This removes such projects:

- only projects named sdktest-<this endpoint>-..., so other endpoints' test data
  and anything the tests did not create are never touched;
- only those older than SWEEP_AGE_HOURS (default 24), so a run that is still
  going on is never touched;
- packages first, then the project.

SWEEP_DRY_RUN=1 lists what would be deleted and deletes nothing. Exits 1 if a
deletion fails.
"""

from __future__ import annotations

import datetime
import os
import re
import sys
from typing import Any

import urllib3

from spectra_assure_api_client import SpectraAssureApiOperations

# The run id, then the suffix the test gave its project (conftest.Created.project).
NAME = re.compile(r"^sdktest-(?P<endpoint>[a-z0-9]+)-(?P<stamp>\d{8}-\d{6})-[0-9a-f]{4}(-.+)?$")


def quiet_if_unverified(no_ssl_verify: bool) -> None:
    """Staging is used without TLS verification, deliberately; do not warn on every request."""
    if no_ssl_verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def settings() -> dict[str, Any]:
    names = {"host": "RLPORTAL_HOST", "server": "RLPORTAL_SERVER", "organization": "RLPORTAL_ORG"}
    names |= {"group": "RLPORTAL_GROUP", "token": "RLPORTAL_ACCESS_TOKEN"}
    found: dict[str, Any] = {key: os.environ[env] for key, env in names.items() if os.environ.get(env)}
    found["no_ssl_verify"] = os.environ.get("RLPORTAL_NO_SSL_VERIFY") == "1"
    found["auto_adapt_to_throttle"] = True
    return found


def stale(name: str, endpoint: str, cutoff: datetime.datetime) -> bool:
    match = NAME.match(name)
    if match is None or match["endpoint"] != endpoint:
        return False
    return datetime.datetime.strptime(match["stamp"], "%Y%m%d-%H%M%S") < cutoff


def main() -> int:
    endpoint = os.environ.get("ENV_NAME", "")
    if not endpoint:
        print(
            "FATAL: ENV_NAME (the endpoint) is not set; run this through `make sweep ENDPOINT=<name>`", file=sys.stderr
        )
        return 2
    hours = int(os.environ.get("SWEEP_AGE_HOURS", "24"))
    dry_run = os.environ.get("SWEEP_DRY_RUN") == "1"
    cutoff = datetime.datetime.now() - datetime.timedelta(hours=hours)

    failed = 0
    options = settings()
    quiet_if_unverified(options["no_ssl_verify"])
    with SpectraAssureApiOperations(**options) as client:
        listing = client.list()
        if listing.status_code != 200:
            print(f"FATAL: listing the group's projects answered {listing.status_code}", file=sys.stderr)
            return 1
        projects = [p["name"] for p in listing.json()["projects"] if stale(p["name"], endpoint, cutoff)]
        print(f"{endpoint}: {len(projects)} test project(s) older than {hours} h{' (dry run)' if dry_run else ''}")

        for project in projects:
            packages = client.list(project=project)
            names = [p["name"] for p in packages.json().get("packages", [])] if packages.status_code == 200 else []
            print(f"  {project} ({len(names)} package(s))")
            if dry_run:
                continue
            for package in names:
                answer = client.delete(project=project, package=package)
                if answer.status_code not in (204, 404):
                    print(f"    could not delete package {package}: {answer.status_code}", file=sys.stderr)
                    failed += 1
            answer = client.delete(project=project)
            if answer.status_code not in (204, 404):
                print(f"    could not delete the project: {answer.status_code}", file=sys.stderr)
                failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

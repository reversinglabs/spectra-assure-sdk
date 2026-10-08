"""Shared plumbing for every operation: routing, URLs, parameter filtering.

Where an operation lives and which parameters it accepts now come from the
compiled API specification. The public `qp_*` helpers are kept
-- they are part of the customer-facing surface --
but they are thin views over the specification instead of separate lists that
have to be updated alongside it.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import (
    Any,
)
from urllib.parse import quote

import requests

from spectra_assure_api_client.communication.api import SpectraAssureApi
from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
    SpectraAssureWaitTimeoutExceeded,
)
from spectra_assure_api_client.communication.post import BodyKind
from spectra_assure_api_client.spec import Operation, SpectraAssureSpecError, resolve

from .constants import _ARCHIVE_POLL_INTERVAL

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsBase(
    ABC,
    SpectraAssureApi,
):
    # ------------------------------------------------------------------ routing

    def _resolve(self, action: str, what: str) -> Operation:
        """Find the specification operation backing this call."""
        try:
            return resolve(action, what)
        except SpectraAssureSpecError as exc:
            # Presented to the caller as an invalid action: from their side an
            # unroutable combination is exactly that.
            raise SpectraAssureInvalidAction(message=str(exc)) from exc

    def _context_path_values(self) -> dict[str, str]:
        """Path values every organization-scoped operation shares.

        The API specification spells them `{organization}` and `{group}`; the
        File Stream endpoints used `{organization_name}` and `{group_name}`
        while they had a document of their own. Both spellings are supplied and
        `render_path` uses whichever the template declares.
        """
        organization = str(self.organization)
        group = str(self.group)
        return {
            "organization": organization,
            "organization_name": organization,
            "group": group,
            "group_name": group,
        }

    def _url_for(self, operation: Operation, **path_values: str) -> str:
        values = {**self._context_path_values(), **path_values}
        return self.base_url + operation.render_path(**values)

    def _make_current_url(  # pylint: disable=too-many-arguments
        self,
        *,
        action: str,
        project: str | None = None,
        package: str | None = None,
        version: str | None = None,
        report_type: str | None = None,
    ) -> str:
        """Build the URL for a group/project/package/version operation.

        The purl ladder used to be assembled segment by segment here. The
        specification already spells each rung out as its own path template --
        `/list/{organization}/{group}`, `/list/{organization}/{group}/pkg:rl/{project}`,
        and so on -- so the rung is chosen by routing and the template rendered.
        """
        what = self._what(project=project, package=package, version=version)
        operation = self._resolve(action, what)

        values: dict[str, str] = {}
        if project is not None:
            values["project"] = project
        if package is not None:
            values["package"] = package
        if version is not None:
            values["version"] = version
        if report_type is not None:
            values["report_type"] = report_type

        return self._url_for(operation, **values)

    def _make_current_url_community(
        self,
        *,
        action: str,
        repository: str | None = None,  # mandatory for community_report_*
        package: str | None = None,  # mandatory, may have a namespace embedded
        version: str | None = None,  # optional
    ) -> str:
        """Build the URL for a community operation.

        Community paths cannot simply be rendered from their template.
        The specification writes them fully qualified --
        `/community/report/package/pkg:{community}/{namespace}/{package}@{version}`
        -- but the SDK accepts a package with the namespace already folded in and
        treats the version as optional. So the fixed prefix is taken from the
        specification and the variable tail is appended to match what the SDK
        has always sent.
        """
        operation = self._resolve(action, "community")

        prefix = "/".join(segment for segment in operation.path.split("/") if "{" not in segment)
        base = self.base_url + prefix

        if repository is None:
            return base

        if package is None:
            msg = f"package must not be None when a repository is given ('{action}')"
            raise SpectraAssureInvalidAction(message=msg)

        # Every value is percent-encoded, as it is for the other paths, so that it
        # cannot change the shape of the URL: a '?' or '#' in a version would
        # otherwise start a query string or a fragment, and requests drops a
        # fragment before sending. Two characters are kept as they are in the
        # package: the '/' between a namespace and a package name, which the
        # specification writes as a separator of its own, and the '@' that opens an
        # npm scope, which has always been sent unescaped.
        tail = f"/pkg:{quote(repository, safe='')}/{quote(package, safe='/@')}"

        if version is None:
            return base + tail

        return base + tail + "@" + quote(version, safe="")

    # -------------------------------------------------- parameter filtering

    @staticmethod
    def _qp_edit(
        *,
        what: str,
        **qp: Any,
    ) -> dict[str, Any]:
        return SpectraAssureApiOperationsBase._accepted("edit", what, qp)

    @staticmethod
    def _qp_reject(
        *,
        what: str,
        **qp: Any,
    ) -> dict[str, Any]:
        return SpectraAssureApiOperationsBase._accepted("reject", what, qp)

    @staticmethod
    def _qp_revoke(
        *,
        what: str,
        **qp: Any,
    ) -> dict[str, Any]:
        return SpectraAssureApiOperationsBase._accepted("revoke", what, qp)

    @staticmethod
    def _qp_scan(
        *,
        what: str,
        **qp: Any,
    ) -> dict[str, Any]:
        r = SpectraAssureApiOperationsBase._accepted("scan", what, qp)

        # A reproducible build takes its inputs from the recorded build, so
        # there is nothing to force or to diff against. The specification
        # states the incompatibility in prose only, so it stays checked here.
        if "build" in r and str(r["build"]).lower() == "repro":
            for k in ("force", "diff_with"):
                if k in r:
                    msg = f"'scan' query parameter {k} cannot be combined with 'build=repro'"
                    raise SpectraAssureInvalidAction(message=msg)

        return r

    @staticmethod
    def _qp_report(
        what: str,
        **qp: Any,
    ) -> dict[str, Any]:
        return SpectraAssureApiOperationsBase._accepted("report", what, qp)

    @staticmethod
    def _link_request_failure(status_code: int, what: str) -> str:
        """The message for a download-link request the Portal refused.

        The start is unchanged, so searches for it still match. A 402 means
        "Insufficient remaining capacity" in the specification: every download
        link draws on the group's download capacity, and what is left does not
        cover this artifact. It used to be reported only by its number (I-48).
        """
        msg = f"we get {status_code} from status lookup for {what}"
        if status_code == 402:
            msg += (
                ": insufficient remaining capacity; the download capacity left does not cover this artifact"
                " (every download link draws on it)"
            )
        return msg

    @staticmethod
    def _link_request_throttle(per_call: bool | None) -> bool:
        """Whether a download-link request retries on 429.

        The specification limits the status call with `download` to 10 requests
        a minute and tells clients to wait as long as Retry-After says. A download
        of more than ten versions therefore runs into the limit by design, and
        failing there leaves it half done (I-46). So link requests retry on 429,
        waiting as Retry-After says, even when the client's throttle handling is
        off; only an explicit `auto_adapt_to_throttle=False` for the call turns
        that off. Every other request follows the usual setting.
        """
        return per_call is not False

    @staticmethod
    def _import_body(  # pylint: disable=too-many-arguments
        *,
        action: str,
        key: str,
        value: str,
        auth_user: str | None,
        auth_pass: str | None,
        bearer_token: str | None,
    ) -> dict[str, Any]:
        """Check an import's source and credentials, and build its JSON body.

        One set of rules for url_import, purl_import and their File Stream
        twins (I-22), which each used to keep their own and did not agree:

        - a URL must contain '://', and a PURL must start with 'pkg:';
        - a bearer token cannot be combined with a user name or password, as
          the specification says for both import operations;
        - an empty credential counts as not given and is left out.

        The specification spells the credential keys with hyphens, which are not
        valid Python identifiers, so the SDK takes underscored arguments and
        maps them here.
        """
        if key == "url" and "://" not in value:
            msg = f"'{action}' no '://' in '{value}'; url must be in uri format '<proto>://<host>[:<port>]/<path>'"
            raise SpectraAssureInvalidAction(message=msg)

        if key == "purl" and not value.lower().startswith("pkg:"):
            msg = f"'{action}' no 'pkg:' in '{value}'; purl must start with 'pkg:'"
            raise SpectraAssureInvalidAction(message=msg)

        if bearer_token and (auth_user or auth_pass):
            msg = f"'{action}': a bearer token cannot be combined with a user name and password"
            raise SpectraAssureInvalidAction(message=msg)

        body: dict[str, Any] = {key: value}
        for name, credential in (("auth-user", auth_user), ("auth-pass", auth_pass), ("bearer-token", bearer_token)):
            if credential:
                body[name] = credential
        return body

    @staticmethod
    def _body_kind(operation: Operation, *, has_fields: bool) -> BodyKind:
        """The body a POST sends, from the media type the specification declares for it.

        A JSON body whose fields are all optional is left out when none is given,
        so `create` without a description sends no body, as before.
        """
        media = operation.body_media_types
        if "application/octet-stream" in media:
            return "file"
        if "multipart/form-data" in media:
            return "form"
        if "application/json" in media and (has_fields or operation.body_required):
            return "json"
        return "none"

    @staticmethod
    def _qp_status(
        *,
        what: str,
        **qp: Any,
    ) -> dict[str, Any]:
        return SpectraAssureApiOperationsBase._accepted_query("status", what, qp)

    @staticmethod
    def _accepted_query(action: str, what: str, qp: dict[str, Any]) -> dict[str, Any]:
        """Keep only the query parameters the specification declares for this operation.

        For operations that build their request body from named arguments, such
        as the imports. They must not use `_accepted`, which also keeps body
        fields: a body field passed in `**qp` (for example `auth-pass`) would
        then be sent in the query string, in the URL. Unroutable combinations
        yield an empty dict, as with `_accepted`.
        """
        try:
            operation = resolve(action, what)
        except SpectraAssureSpecError:
            return {}

        query = set(operation.query_params)
        return {k: v for k, v in qp.items() if k in query}

    @staticmethod
    def _accepted(action: str, what: str, qp: dict[str, Any]) -> dict[str, Any]:
        """Keep only the arguments the specification declares for this operation.

        Unroutable combinations yield an empty dict rather than raising:
        the `qp_*` helpers have always answered that way for parameters
        that do not apply at a given level,
        and callers rely on passing one shared bag of arguments across operations
        that accept different subsets of it.
        """
        try:
            operation = resolve(action, what)
        except SpectraAssureSpecError:
            return {}

        accepted = set(operation.accepted_parameters)
        return {k: v for k, v in qp.items() if k in accepted}

    @staticmethod
    def _require_reason(*, action: str, qp: dict[str, Any]) -> None:
        """Insist on the `reason` that approve, reject and revoke cannot do without.

        The specification (TPRMReason) requires a request body with a `reason`.
        Without one the SDK sent a request with no body at all, which the Portal
        can only refuse, so it is refused here instead, before anything is sent.

        The specification puts no minimum on the length, so an empty string is
        passed on and left to the Portal to judge.
        """
        if not isinstance(qp.get("reason"), str):
            msg = f"'{action}' requires a 'reason' (a string): the Portal API declares it mandatory"
            raise SpectraAssureInvalidAction(message=msg)

    # ------------------------------------------------------------- dispatch

    def _simple_operation(  # pylint: disable=too-many-arguments
        self,
        *,
        project: str | None = None,
        package: str | None = None,
        version: str | None = None,
        action: str,
        verb: str,
        supported: list[str],
        auto_adapt_to_throttle: bool | None = None,
        file_path: str | None = None,
        **qp: Any,
    ) -> requests.Response:
        what = self._what(
            project=project,
            package=package,
            version=version,
        )

        logger.debug(
            "Pr: %s, Pa: %s, Ve: %s, Act: %s, Verb: %s, Supp: %s, Qp: %s",
            project,
            package,
            version,
            action,
            verb,
            supported,
            qp,
        )

        if what not in supported:
            x = " and ".join(supported)
            msg = f"'{action}' is only supported for: {x}"
            raise SpectraAssureInvalidAction(message=msg)

        operation = self._resolve(action, what)

        # `scan` carries the incompatibility check that the specification only
        # states in prose, so it keeps its dedicated helper.
        filtered = self._qp_scan(what=what, **qp) if action == "scan" else self._accepted(action, what, qp)

        query_params, body_params = operation.split_parameters(filtered)

        url = self._make_current_url(
            action=action,
            project=project,
            package=package,
            version=version,
        )

        if verb == "delete":
            # The previous implementation computed these and then dropped them:
            # `_do_it_delete` was called with the (empty) body bag and never with
            # the query parameters, so `delete(..., build=...)` had no effect.
            return self._do_it_delete(
                url=url,
                auto_adapt_to_throttle=auto_adapt_to_throttle,
                url_params={k: str(v) for k, v in query_params.items()} or None,
            )

        if verb == "put":
            return self._do_it_put(
                url=url,
                auto_adapt_to_throttle=auto_adapt_to_throttle,
                url_params={k: str(v) for k, v in query_params.items()} or None,
                **body_params,
            )

        if verb == "post":
            # Query parameters in the query string, body properties in the body,
            # as the specification declares them; the kind of body as well.
            return self._post(
                action=action,
                url=url,
                body=self._body_kind(operation, has_fields=bool(body_params)),
                file_path=file_path,
                post_data=dict(body_params) if body_params else None,
                auto_adapt_to_throttle=auto_adapt_to_throttle,
                **query_params,
            )

        if verb == "get":
            return self._do_it_get(
                url=url,
                auto_adapt_to_throttle=auto_adapt_to_throttle,
                **query_params,
            )

        if verb == "patch":
            return self._do_it_patch(
                url=url,
                auto_adapt_to_throttle=auto_adapt_to_throttle,
                **body_params,
            )

        msg = f"Unsupported operation: {verb}"
        raise ValueError(msg)

    def _wait_for_rl_safe_archive(
        self,
        *,
        fetch: Callable[[], requests.Response],
        what: str,
        max_wait_time: int,
    ) -> requests.Response:
        """Request an RL-SAFE archive link, waiting while the archive is still being prepared.

        The API answers 202 until the analysis has finished and the archive can
        be produced, for project/package/version archives and for File Stream
        files alike. That is normally a step on the way, not a failure, so it is
        waited out rather than raised. Any other status than 200 is a real error
        and is raised at once.

        The specification gives two messages for that 202: "not done with
        analysis" and "does not have complete analysis". The second may never
        resolve, and it is waited out just the same; when the budget runs out
        the API's message is included in the exception so the cause is visible.

        `fetch` issues one request; `what` names the archive in messages.
        `max_wait_time` of 0 fails on the first 202.
        """
        waited = 0

        while True:
            data = fetch()

            if data.status_code == 200:
                return data

            if data.status_code != 202:
                msg = f"Error: rl-safe requests returns: {data.status_code} {data.text}"
                raise SpectraAssureInvalidAction(message=msg)

            if waited >= max_wait_time:
                # The API gives two reasons for a 202: the analysis is not done
                # yet, or the version has no complete analysis. Only the first
                # resolves by waiting, and the two cannot be told apart without
                # reading the message, so it is passed on to the caller.
                reason = " ".join(data.text.split())[:200]
                msg = (
                    f"the rl-safe archive for {what} was still being prepared "
                    f"after {waited}s (the API kept answering 202)"
                )
                if reason:
                    msg += f": {reason}"
                raise SpectraAssureWaitTimeoutExceeded(message=msg)

            logger.info(
                "rl-safe archive for %s is not ready yet (max %ds, current %ds)",
                what,
                max_wait_time,
                waited,
            )
            time.sleep(_ARCHIVE_POLL_INTERVAL)
            waited += _ARCHIVE_POLL_INTERVAL

    # --------------------------------------------------------------- STATIC

    @staticmethod
    def _what(  # gppv
        *,
        project: str | None = None,
        package: str | None = None,
        version: str | None = None,
    ) -> str:

        if project is None:
            return "group"

        if package is None:
            return "project"

        if version is None:
            return "package"

        return "version"

    # ------------------------------------------------------ PUBLIC ABSTRACT

    @abstractmethod
    def status(
        self,
        *,
        project: str,
        package: str,
        version: str,
        auto_adapt_to_throttle: bool | None = None,
        **qp: Any,
    ) -> Any:
        """Needed here for the download operation"""

    @abstractmethod
    def list(
        self,
        *,
        project: str | None = None,
        package: str | None = None,
        version: str | None = None,
        auto_adapt_to_throttle: bool | None = None,
        # **qp: Any,  # not actually used in list
    ) -> Any:
        """Needed here for the download operation"""

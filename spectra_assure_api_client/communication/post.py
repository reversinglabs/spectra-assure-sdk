import logging
import os
import re
import urllib.parse
from typing import (
    Any,
    Literal,
)

import requests

from .core import SpectraAssureApiCore
from .exceptions import (
    SpectraAssureInvalidAction,
)

logger = logging.getLogger(__name__)

# What a POST sends as its body; see SpectraAssureApiPost._post.
BodyKind = Literal["file", "json", "form", "none"]

# The action names below are only used by _do_it_post, the old entry point
# that infers the body from the action's name.

# Operations whose body is a JSON document assembled by the caller rather than
# the loose query-parameter bag.
_JSON_BODY_ACTIONS = frozenset(
    {
        "url_import",
        "purl_import",
        "community_find_packages",
        "audit_log_export",
        "audit_log_status",
    }
)

# Operations that upload a configuration file as multipart form data. The
# Portal expects the file part under a fixed name regardless of what the file
# is called on disk.
_PROFILE_IMPORT_ACTIONS = frozenset({"import_org_profile", "import_group_profile"})
_PROFILE_IMPORT_FIELD = "configuration_file"


# RFC 7230 token characters: a filename made only of these needs no quoting.
_TOKEN = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
# RFC 8187 attr-char, the characters left as they are in filename*.
_ATTR_CHAR_SAFE = "!#$&+-.^_`|~"


def _content_disposition(file_name: str) -> str:
    """The Content-Disposition header for uploading `file_name`, per RFC 6266.

    A name of token characters only, like the specification's example
    `attachment; filename=upload.exe`, is sent as it is. Any other name is sent
    as a quoted string with `"` and `\\` escaped; it used to go out unquoted, so
    a space or `;` cut it short for a parser (I-47). A name with characters
    outside printable ASCII gets an ASCII fallback in `filename` and the real
    name, UTF-8 encoded, in `filename*`; such a name used to make the upload
    fail with UnicodeEncodeError, because header values must be Latin-1.
    Control characters (a newline, say) never reach the header.
    """
    if _TOKEN.match(file_name):
        return f"attachment; filename={file_name}"

    fallback = "".join(ch if " " <= ch <= "~" else "_" for ch in file_name)
    quoted = fallback.replace("\\", "\\\\").replace('"', '\\"')
    value = f'attachment; filename="{quoted}"'
    if fallback != file_name:
        value += "; filename*=UTF-8''" + urllib.parse.quote(file_name, safe=_ATTR_CHAR_SAFE)
    return value


def _form_value(value: Any) -> Any:
    """A value as it is written into a multipart form field.

    requests writes a Python bool as "True" or "False". The specification types
    the form field `replace` as a boolean and writes it as true and false, and
    for this field the difference matters: false merges the imported profile
    into the existing configuration, true replaces it. Booleans are therefore
    written in lowercase. Query strings are not affected: the Portal is known to
    accept `download=True` there.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


class SpectraAssureApiPost(
    SpectraAssureApiCore,
):
    def _post(  # pylint: disable=too-many-arguments
        self,
        *,
        action: str,
        url: str,
        body: BodyKind,
        auto_adapt_to_throttle: bool | None,
        file_path: str | None = None,
        post_data: Any = None,
        **qp: Any,
    ) -> requests.Response:
        """POST to `url`, sending the request body the caller names.

        `body` says what the body is, so nothing is inferred from the action's
        name: "file" streams `file_path` as application/octet-stream, "json"
        sends `post_data` as JSON, "form" uploads `file_path` with `post_data`
        as multipart form data, and "none" sends no body. `qp` is always the
        query string and never the body. `action` names the call in messages.
        """
        logger.debug("_post %s %s (%s)", action, url, body)

        payload: Any
        multipart_field_name: str | None = None
        use_multipart = False

        if body == "file":
            # The archive is streamed as the raw request body.
            if file_path is None:
                msg = f"'{action}' needs a filename, none was given"
                logger.error(msg)
                raise SpectraAssureInvalidAction(message=msg)

            file_name = os.path.basename(file_path)
            headers = self._make_headers(
                {
                    "Content-Disposition": _content_disposition(file_name),
                    "Content-Type": "application/octet-stream",
                }
            )
            payload = None

        elif body == "json":
            if post_data is None:
                msg = f"post_data must not be None for '{action}'"
                logger.error(msg)
                raise SpectraAssureInvalidAction(message=msg)

            headers = self._make_headers()
            payload = post_data

        elif body == "form":
            if file_path is None:
                msg = f"'{action}' needs a filename, none was given"
                logger.error(msg)
                raise SpectraAssureInvalidAction(message=msg)

            if post_data is None:  # the replace bool goes here
                msg = f"post_data must not be None for '{action}' (it carries the 'replace' flag)"
                logger.error(msg)
                raise SpectraAssureInvalidAction(message=msg)

            use_multipart = True
            multipart_field_name = _PROFILE_IMPORT_FIELD
            payload = {name: _form_value(value) for name, value in post_data.items()}

            headers = self._make_headers()
            # requests derives the multipart Content-Type, boundary included.
            headers.pop("Content-Type", None)

        elif body == "none":
            if post_data is not None:
                msg = f"'{action}' sends no request body, but post_data was given"
                logger.error(msg)
                raise SpectraAssureInvalidAction(message=msg)

            headers = self._make_headers()
            payload = None

        else:
            msg = f"'{action}': unknown body kind {body!r}; use one of 'file', 'json', 'form' or 'none'"
            raise SpectraAssureInvalidAction(message=msg)

        # may raise OSError if the file does not exist or is not readable
        response = self._xx_with_retry(
            url=url,
            payload=payload,
            headers=headers,
            action="POST",
            url_params=qp,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            file_path=file_path,
            use_multipart=use_multipart,
            multipart_field_name=multipart_field_name,
        )

        return self._log_response_status(
            url=url,
            response=response,
        )

    def _do_it_post(  # pylint: disable=too-many-arguments
        self,
        *,
        action: str,
        url: str,
        auto_adapt_to_throttle: bool | None,
        file_path: str | None = None,
        post_data: Any = None,
        use_multipart: bool = False,  # noqa: ARG002  kept for signature compatibility
        origin_call: str | None = None,  # noqa: ARG002  kept for signature compatibility
        **qp: Any,
    ) -> requests.Response:
        """The old entry point, kept for the deprecated `do_it_post` alias (I-19).

        It infers the body from the action's name, as the SDK used to; the SDK
        itself calls `_post` with an explicit body kind (I-23). The inference
        is unchanged, including its last case: an unknown action without
        `post_data` sends its query parameters as the JSON body as well.
        """
        body: BodyKind
        if action == "scan":
            body = "file"
        elif action in _JSON_BODY_ACTIONS:
            body = "json"
        elif action in _PROFILE_IMPORT_ACTIONS:
            body = "form"
        elif post_data is not None:
            body = "json"
        elif qp:
            body, post_data = "json", dict(qp)
        else:
            body = "none"

        return self._post(
            action=action,
            url=url,
            body=body,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            file_path=file_path,
            post_data=post_data,
            **qp,
        )

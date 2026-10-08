"""Shared test helpers.

Client construction goes through `make_client` rather than splatting a dict of
settings: the constructor takes `str | None`, `int | None` and `bool | None`
across its parameters, so a `**dict[str, str]` cannot type-check against it.
"""

from __future__ import annotations

import io
import json
from typing import Any

import pytest
import requests

from spectra_assure_api_client import SpectraAssureApiOperations

HOST = "portal.example.com"
SERVER = "demo"
ORGANIZATION = "Org"
GROUP = "Grp"
TOKEN = "t" * 20  # noqa: S105  a fake token for tests

BASE = f"https://{HOST}/{SERVER}/api/public/v1"


def make_client(
    *,
    host: str | None = HOST,
    server: str | None = SERVER,
    organization: str | None = ORGANIZATION,
    group: str | None = GROUP,
    token: str | None = TOKEN,
    auto_adapt_to_throttle: bool | None = None,
    no_ssl_verify: bool | None = None,
    timeout: int | None = None,
    read_timeout: int | None = None,
    connect_timeout: int | None = None,
) -> SpectraAssureApiOperations:
    """Build a client for tests, with every setting explicitly typed."""
    return SpectraAssureApiOperations(
        host=host,
        server=server,
        organization=organization,
        group=group,
        token=token,
        auto_adapt_to_throttle=auto_adapt_to_throttle,
        no_ssl_verify=no_ssl_verify,
        timeout=timeout,
        read_timeout=read_timeout,
        connect_timeout=connect_timeout,
    )


def make_response(
    status: int = 200,
    *,
    payload: Any = None,
    headers: dict[str, str] | None = None,
    text: str = "",
) -> requests.Response:
    """A requests.Response with a body, without going near the network."""
    response = requests.Response()
    response.status_code = status
    response.headers.update(headers or {})

    body = text.encode() if text else json.dumps(payload if payload is not None else {"ok": True}).encode()
    response.raw = io.BytesIO(body)
    response._content = body  # noqa: SLF001  no public way to seed a Response body
    return response


class Recorder:
    """Stands in for `requests.<verb>`, recording each attempt.

    Queued responses are returned in order; once they run out every further
    call gets a plain 200. Request bodies are read eagerly, so a test can assert
    that a retried upload actually re-sent its contents.
    """

    def __init__(self, payloads: list[Any] | None = None, responses: list[requests.Response] | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.payloads: list[Any] = list(payloads or [])
        self.responses: list[requests.Response] = list(responses or [])

    def __call__(self, *args: Any, **kw: Any) -> requests.Response:
        """Stand in for either `Session.request(method, url, ...)` or `requests.get(url, ...)`.

        Patched onto `Session.request`, the call arrives as
        (self, method, url); the bound-method form drops `self`. Both shapes are
        accepted so a test can assert on the method as well as the URL.
        """
        positional = [a for a in args if isinstance(a, str)]
        if len(positional) >= 2:
            method, url = positional[0], positional[1]
        else:
            method, url = kw.get("method", ""), (positional[0] if positional else kw.get("url", ""))

        data: Any = kw.get("data")
        files: dict[str, Any] = kw.get("files") or {}
        body_bytes = data.read() if data is not None and hasattr(data, "read") else data

        self.calls.append(
            {
                "method": method,
                "url": url,
                "params": kw.get("params") or {},
                "json": kw.get("json"),
                # "not passed" and "passed as None" are indistinguishable from
                # the value alone, and the difference is what puts a body on the
                # wire, so record it.
                "json_passed": "json" in kw,
                "body_bytes": body_bytes,
                "files": {name: handle.read() for name, handle in files.items()},
                "headers": dict(kw.get("headers") or {}),
                "timeout": kw.get("timeout"),
                "verify": kw.get("verify"),
            }
        )

        if self.responses:
            return self.responses.pop(0)
        if self.payloads:
            return make_response(payload=self.payloads.pop(0))
        return make_response()


def install(monkeypatch: pytest.MonkeyPatch, verb: str, recorder: Recorder) -> Recorder:
    """Point the client's HTTP transport at a recorder for the duration of a test.

    The client issues everything through `requests.Session.request` now, so the
    recorder is patched there rather than onto a per-verb module function. The
    `verb` argument is kept because it documents which call the test expects;
    assert on `calls[0]["method"]` when the distinction matters.
    """
    monkeypatch.setattr(requests.Session, "request", recorder)
    return recorder


def capture_sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Record throttle waits instead of serving them."""
    recorded: list[float] = []
    monkeypatch.setattr(
        "spectra_assure_api_client.communication.core.time.sleep",
        recorded.append,
    )
    return recorded

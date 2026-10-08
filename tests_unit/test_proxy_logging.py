"""Proxy credentials must not reach the log, and must still reach the proxy."""

from __future__ import annotations

import logging
import urllib.parse
from typing import Any

import pytest
import requests

from spectra_assure_api_client import SpectraAssureApiOperations
from spectra_assure_api_client.communication import core

from .support import GROUP, HOST, ORGANIZATION, TOKEN, make_response

SECRET = "s3cr3t/with@odd:chars"  # noqa: S105  a fake password, used only to check that it is masked


def test_a_password_is_masked_and_the_rest_stays_readable() -> None:
    quoted = urllib.parse.quote(SECRET)

    redacted = core.redact_proxies({"http": f"http://alice:{quoted}@proxy.example.com:8080"})

    assert redacted == {"http": "http://alice:***@proxy.example.com:8080"}


@pytest.mark.parametrize(
    "url",
    [
        "http://proxy.example.com:8080",
        "http://alice@proxy.example.com:8080",  # a user name is not a secret, and has no password to mask
        "https://proxy.example.com",
    ],
)
def test_a_url_without_a_password_is_left_alone(url: str) -> None:
    assert core.redact_proxies({"https": url}) == {"https": url}


def test_an_at_sign_in_the_password_cannot_expose_the_tail() -> None:
    """The host follows the last '@'; an '@' inside the password must not end the masking early."""
    redacted = core.redact_proxies({"http": "http://alice:pa@ss@proxy.example.com:8080"})

    assert redacted == {"http": "http://alice:***@proxy.example.com:8080"}
    assert "pa@ss" not in str(redacted)


def test_a_malformed_url_does_not_leak_its_password() -> None:
    redacted = core.redact_proxies({"http": "http://alice:secret@[::1"})

    assert "secret" not in str(redacted)


def test_the_url_the_sdk_builds_for_a_password_with_a_slash_is_masked() -> None:
    """`quote()` leaves '/' alone, so a URL parser sees no credentials in this URL; it still has them."""
    url = f"http://alice:{urllib.parse.quote(SECRET)}@proxy.example.com:8080"

    assert core.redact_proxies({"http": url}) == {"http": "http://alice:***@proxy.example.com:8080"}


def test_the_input_is_not_modified() -> None:
    original = {"http": "http://alice:secret@proxy.example.com:8080"}

    core.redact_proxies(original)

    assert original == {"http": "http://alice:secret@proxy.example.com:8080"}


def client_with_proxy() -> SpectraAssureApiOperations:
    return SpectraAssureApiOperations(
        host=HOST,
        organization=ORGANIZATION,
        group=GROUP,
        token=TOKEN,
        proxy_server="proxy.example.com",
        proxy_port=8080,
        proxy_user="alice",
        proxy_password=SECRET,
    )


def test_the_debug_log_does_not_contain_the_proxy_password(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    sent: list[dict[str, Any]] = []

    def fake_request(_self: Any, _method: str, _url: str, **kw: Any) -> requests.Response:
        sent.append(kw)
        return make_response()

    monkeypatch.setattr(requests.Session, "request", fake_request)
    client = client_with_proxy()

    with caplog.at_level(logging.DEBUG, logger="spectra_assure_api_client"):
        client.list(project="pr")

    assert SECRET not in caplog.text
    assert urllib.parse.quote(SECRET) not in caplog.text
    assert urllib.parse.quote(SECRET, safe="") not in caplog.text
    # The line is still useful: it says which proxy and which user.
    assert "proxy.example.com:8080" in caplog.text
    assert "alice" in caplog.text
    # And the request itself still authenticates to the proxy.
    assert urllib.parse.quote(SECRET, safe="") in sent[0]["proxies"]["https"]


def test_a_password_from_the_environment_is_masked_too(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    for name in ("http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY", "no_proxy", "NO_PROXY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("https_proxy", "http://bob:hunter2@envproxy.example.com:3128")
    monkeypatch.setattr(requests.Session, "request", lambda *_a, **_k: make_response())
    client = SpectraAssureApiOperations(host=HOST, organization=ORGANIZATION, group=GROUP, token=TOKEN)

    with caplog.at_level(logging.DEBUG, logger="spectra_assure_api_client"):
        client.list(project="pr")

    assert "hunter2" not in caplog.text
    assert "envproxy.example.com:3128" in caplog.text

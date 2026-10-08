"""Retry-on-429 behaviour, and the shared session.

Retry is opt-in, and every request path shares one loop, uploads included.
These tests pin down the attempt count, where the delay comes from, the
three-state per-call override, and that all of it goes through one session.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
import requests

from spectra_assure_api_client import SpectraAssureApiOperations
from spectra_assure_api_client.communication import constants, core

from .support import Recorder, capture_sleeps, install, make_client, make_response


@pytest.fixture
def slept(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Capture throttle waits instead of serving them."""
    return capture_sleeps(monkeypatch)


@pytest.fixture
def client() -> SpectraAssureApiOperations:
    """Default client: retry off, as the released SDK ships it."""
    return make_client()


@pytest.fixture
def retrying() -> SpectraAssureApiOperations:
    """Client with retry switched on, as the example configures it."""
    return make_client(auto_adapt_to_throttle=True)


def test_retry_is_opt_in(client: SpectraAssureApiOperations) -> None:
    """Unchanged from the released SDK: callers ask for retry, they don't get it."""
    assert client.auto_adapt_to_throttle is False


def test_unset_means_opt_in() -> None:
    explicit = make_client(auto_adapt_to_throttle=None)
    assert explicit.auto_adapt_to_throttle is False


def test_explicit_true_is_respected() -> None:
    on = make_client(auto_adapt_to_throttle=True)
    assert on.auto_adapt_to_throttle is True


def test_throttled_request_is_retried_until_it_succeeds(
    monkeypatch: pytest.MonkeyPatch,
    retrying: SpectraAssureApiOperations,
    slept: list[float],
) -> None:
    transport = Recorder(
        responses=[
            make_response(429, headers={"Retry-After": "3"}),
            make_response(429, headers={"Retry-After": "4"}),
            make_response(200),
        ]
    )
    install(monkeypatch, "get", transport)

    response = retrying.list(project="pr")

    assert response.status_code == 200
    assert len(transport.calls) == 3
    assert slept == [3, 4]


def test_attempts_are_capped_and_the_429_is_returned(
    monkeypatch: pytest.MonkeyPatch,
    retrying: SpectraAssureApiOperations,
    slept: list[float],
) -> None:
    transport = Recorder(responses=[make_response(429, headers={"Retry-After": "1"})] * 10)
    install(monkeypatch, "get", transport)

    response = retrying.list(project="pr")

    assert response.status_code == 429
    assert len(transport.calls) == constants.MAX_THROTTLE_ATTEMPTS
    # No sleep after the final attempt: there is nothing left to wait for.
    assert len(slept) == constants.MAX_THROTTLE_ATTEMPTS - 1


def test_per_call_false_disables_retry(
    monkeypatch: pytest.MonkeyPatch,
    retrying: SpectraAssureApiOperations,
    slept: list[float],
) -> None:
    transport = Recorder(responses=[make_response(429, headers={"Retry-After": "1"})] * 5)
    install(monkeypatch, "get", transport)

    response = retrying.list(project="pr", auto_adapt_to_throttle=False)

    assert response.status_code == 429
    assert len(transport.calls) == 1
    assert slept == []


def test_per_call_true_enables_retry_on_a_client_that_has_it_off(
    monkeypatch: pytest.MonkeyPatch,
    slept: list[float],
) -> None:
    off = make_client(auto_adapt_to_throttle=False)
    transport = Recorder(responses=[make_response(429, headers={"Retry-After": "2"}), make_response(200)])
    install(monkeypatch, "get", transport)

    response = off.list(project="pr", auto_adapt_to_throttle=True)

    assert response.status_code == 200
    assert len(transport.calls) == 2


def test_non_throttle_errors_are_not_retried(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
    slept: list[float],
) -> None:
    transport = Recorder(responses=[make_response(404), make_response(200)])
    install(monkeypatch, "get", transport)

    response = client.list(project="pr")

    assert response.status_code == 404
    assert len(transport.calls) == 1
    assert slept == []


# ------------------------------------------------------------------- delay


def test_delay_prefers_the_retry_after_header() -> None:
    response = make_response(429, headers={"Retry-After": "17"}, text="available in 99 seconds")
    assert core.SpectraAssureApiCore._get_throttle_delay(response) == 17


def test_delay_falls_back_to_the_message_body() -> None:
    response = make_response(429, text="Expected available in 12 seconds.")
    # one second is added as a margin
    assert core.SpectraAssureApiCore._get_throttle_delay(response) == 13


def test_delay_falls_back_to_a_fixed_wait() -> None:
    response = make_response(429, text="slow down")
    assert core.SpectraAssureApiCore._get_throttle_delay(response) == constants.FALLBACK_THROTTLE_DELAY


def test_http_date_retry_after_is_parsed() -> None:
    """RFC 9110 allows a date as well as a number of seconds."""
    when = datetime.now(timezone.utc) + timedelta(seconds=45)
    response = make_response(429, headers={"Retry-After": when.strftime("%a, %d %b %Y %H:%M:%S GMT")})

    delay = core.SpectraAssureApiCore._get_throttle_delay(response)

    # to the second, allowing for the time the assertion takes to get here
    assert 40 <= delay <= 45


def test_a_retry_after_date_in_the_past_means_retry_now() -> None:
    when = datetime.now(timezone.utc) - timedelta(minutes=5)
    response = make_response(429, headers={"Retry-After": when.strftime("%a, %d %b %Y %H:%M:%S GMT")})

    assert core.SpectraAssureApiCore._get_throttle_delay(response) == 0


def test_an_implausibly_distant_retry_after_date_is_capped() -> None:
    """Clock skew must not turn into an arbitrarily long sleep."""
    when = datetime.now(timezone.utc) + timedelta(hours=6)
    response = make_response(429, headers={"Retry-After": when.strftime("%a, %d %b %Y %H:%M:%S GMT")})

    assert core.SpectraAssureApiCore._get_throttle_delay(response) == constants.MAX_DATE_THROTTLE_DELAY


def test_a_date_beginning_with_a_number_is_not_read_as_seconds() -> None:
    """Regression: "21 Oct ..." used to be read as a 21 second wait."""
    response = make_response(429, headers={"Retry-After": "21 Oct 2036 07:28:00 GMT"})

    assert core.SpectraAssureApiCore._get_throttle_delay(response) != 21


def test_an_unparseable_retry_after_falls_back() -> None:
    response = make_response(429, headers={"Retry-After": "soon-ish"}, text="slow down")

    assert core.SpectraAssureApiCore._get_throttle_delay(response) == constants.FALLBACK_THROTTLE_DELAY


# ------------------------------------------------------------------ uploads


def test_upload_body_is_resent_in_full_on_retry(
    monkeypatch: pytest.MonkeyPatch,
    retrying: SpectraAssureApiOperations,
    slept: list[float],
    tmp_path: Path,
) -> None:
    """The regression that made one retry loop into two.

    A file handle consumed by a throttled attempt is empty on the next one, so
    each attempt has to reopen the file. Without that, a retried upload sends a
    zero-byte body and the Portal accepts an empty artifact.
    """
    payload = b"artifact-contents-that-must-arrive-intact"
    upload = tmp_path / "artifact.bin"
    upload.write_bytes(payload)

    transport = Recorder(responses=[make_response(429, headers={"Retry-After": "1"}), make_response(200)])
    install(monkeypatch, "post", transport)

    response = retrying.scan(project="pr", package="pk", version="1.0", file_path=str(upload))

    assert response.status_code == 200
    assert len(transport.calls) == 2
    assert [call["body_bytes"] for call in transport.calls] == [payload, payload]


def test_multipart_upload_is_resent_in_full_on_retry(
    monkeypatch: pytest.MonkeyPatch,
    retrying: SpectraAssureApiOperations,
    slept: list[float],
    tmp_path: Path,
) -> None:
    payload = b'{"profile": true}'
    profile = tmp_path / "profile.json"
    profile.write_bytes(payload)

    transport = Recorder(responses=[make_response(429, headers={"Retry-After": "1"}), make_response(200)])
    install(monkeypatch, "post", transport)

    response = retrying.import_profile(organization="Org", file_path=str(profile))

    assert response.status_code == 200
    assert len(transport.calls) == 2
    for call in transport.calls:
        assert call["files"] == {"configuration_file": payload}


# ------------------------------------------------------------------ session


def test_the_client_reuses_one_session(client: SpectraAssureApiOperations) -> None:
    """The point of the change: one connection pool for the life of the client."""
    assert isinstance(client.session, requests.Session)
    assert client.session is client.session


def test_every_call_goes_through_that_session(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    seen: list[tuple[Any, str]] = []

    def record(self: Any, method: str, url: str, **kw: Any) -> requests.Response:
        seen.append((self, method))
        return make_response()

    monkeypatch.setattr(requests.Session, "request", record)

    client.list(project="pr")
    client.status(project="pr", package="pk", version="1.0")
    client.approve(project="pr", package="pk", version="1.0", reason="ok")

    assert [method for _, method in seen] == ["GET", "GET", "PUT"]
    # all three on the same session object, so the connection is pooled
    assert {id(session) for session, _ in seen} == {id(client.session)}


def test_retries_reuse_the_session_too(
    monkeypatch: pytest.MonkeyPatch,
    retrying: SpectraAssureApiOperations,
    slept: list[float],
) -> None:
    transport = Recorder(responses=[make_response(429, headers={"Retry-After": "1"}), make_response(200)])
    install(monkeypatch, "get", transport)

    retrying.list(project="pr")

    assert len(transport.calls) == 2
    assert {call["method"] for call in transport.calls} == {"GET"}


def test_close_is_idempotent_and_the_client_still_works(
    monkeypatch: pytest.MonkeyPatch,
    client: SpectraAssureApiOperations,
) -> None:
    """close() releases connections; requests opens a new one on the next call."""
    client.close()
    client.close()

    recorder = install(monkeypatch, "get", Recorder())
    client.list(project="pr")

    assert len(recorder.calls) == 1


def test_the_client_works_as_a_context_manager(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[bool] = []
    monkeypatch.setattr(requests.Session, "close", lambda self: closed.append(True))

    with make_client() as client:
        assert isinstance(client.session, requests.Session)

    assert closed == [True]


# ------------------------------------------------------------------ timeout


def test_the_connect_timeout_has_a_sane_default() -> None:
    client = make_client()

    assert client.connect_timeout == constants.DEFAULT_CONNECT_TIMEOUT
    assert client.connect_timeout < client.timeout

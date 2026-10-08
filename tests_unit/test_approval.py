"""approve, reject and revoke: `reason` is mandatory.

The specification (TPRMReason) requires a request body carrying a `reason`.
Leaving it out used to send a request with no body at all, which the Portal can
only refuse, so it is refused here, before anything goes over the wire.
"""

from __future__ import annotations

import pytest

from spectra_assure_api_client import SpectraAssureApiOperations, SpectraAssureInvalidAction

from .support import Recorder, install, make_client

METHODS = ["approve", "reject", "revoke"]


@pytest.fixture
def client() -> SpectraAssureApiOperations:
    return make_client()


@pytest.mark.parametrize("method", METHODS)
def test_a_missing_reason_is_refused_before_anything_is_sent(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, method: str
) -> None:
    recorder = install(monkeypatch, "put", Recorder())

    with pytest.raises(SpectraAssureInvalidAction, match=f"'{method}' requires a 'reason'"):
        getattr(client, method)(project="pr", package="pk", version="1.0")

    assert recorder.calls == []


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("reason", [None, 5, ["because"]])
def test_a_reason_that_is_not_a_string_is_refused(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, method: str, reason: object
) -> None:
    """`reason=None` is what a caller with an optional `reason` of their own passes along."""
    recorder = install(monkeypatch, "put", Recorder())

    with pytest.raises(SpectraAssureInvalidAction, match="reason"):
        getattr(client, method)(project="pr", package="pk", version="1.0", reason=reason)

    assert recorder.calls == []


@pytest.mark.parametrize("method", METHODS)
def test_a_reason_travels_in_the_body(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, method: str
) -> None:
    recorder = install(monkeypatch, "put", Recorder())

    getattr(client, method)(project="pr", package="pk", version="1.0", reason="looks fine")

    assert recorder.calls[0]["method"] == "PUT"
    assert recorder.calls[0]["json"] == {"reason": "looks fine"}
    assert recorder.calls[0]["params"] == {}


@pytest.mark.parametrize("method", METHODS)
def test_an_empty_reason_is_left_to_the_portal(
    monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations, method: str
) -> None:
    """The specification sets no minimum length, so the SDK is not stricter than the API."""
    recorder = install(monkeypatch, "put", Recorder())

    getattr(client, method)(project="pr", package="pk", version="1.0", reason="")

    assert recorder.calls[0]["json"] == {"reason": ""}

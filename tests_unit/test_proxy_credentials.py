"""Proxy credentials survive being put into the proxy URL, whatever characters they contain.

The URL is `http://<user>:<password>@<server>:<port>`. requests percent-decodes
the user name and the password when it builds the Proxy-Authorization header, so
both must be percent-encoded completely. Before, a '/' in the password made the
URL unparseable, and a '/' in the user name made it name a different host.
"""

from __future__ import annotations

import base64
import http.server
import threading
from collections.abc import Iterator

import pytest
import requests.adapters
from urllib3.util import parse_url

from spectra_assure_api_client import SpectraAssureApiOperations

from .support import GROUP, HOST, ORGANIZATION, TOKEN

CREDENTIALS = [
    ("alice", "secret"),
    ("alice", "se/cret"),  # was: LocationParseError, every request failed
    ("al/ice", "secret"),  # was: parsed as host 'al', requests went elsewhere
    ("alice", "se@cr:et"),
    ("al@ice", "secret"),
    ("al:ice", "secret"),
    ("alice", "p%41ss"),  # a literal '%' must not be decoded into 'A'
    ("alice", "sp ace#?&=+"),
    # Non-ASCII within Latin-1 only: requests encodes the Basic credentials as
    # Latin-1, so a character outside it (such as the euro sign) cannot be sent
    # to a proxy at all, with or without this encoding.
    ("ålice", "sëcrét"),
]


def client_with(
    user: str, password: str, *, server: str = "proxy.example.com", port: int = 8080
) -> SpectraAssureApiOperations:
    return SpectraAssureApiOperations(
        host=HOST,
        organization=ORGANIZATION,
        group=GROUP,
        token=TOKEN,
        proxy_server=server,
        proxy_port=port,
        proxy_user=user,
        proxy_password=password,
    )


@pytest.mark.parametrize(("user", "password"), CREDENTIALS)
def test_the_proxy_url_names_the_configured_proxy(user: str, password: str) -> None:
    for url in client_with(user, password).proxies.values():
        parsed = parse_url(url)

        assert parsed.host == "proxy.example.com"
        assert parsed.port == 8080


@pytest.mark.parametrize(("user", "password"), CREDENTIALS)
def test_requests_recovers_the_exact_credentials(user: str, password: str) -> None:
    """What reaches the proxy is what requests decodes from the URL."""
    headers = requests.adapters.HTTPAdapter().proxy_headers(client_with(user, password).proxies["https"])

    assert headers["Proxy-Authorization"] == requests.auth._basic_auth_str(user, password)  # noqa: SLF001


def test_no_credentials_gives_a_plain_proxy_url() -> None:
    client = SpectraAssureApiOperations(
        host=HOST,
        organization=ORGANIZATION,
        group=GROUP,
        token=TOKEN,
        proxy_server="proxy.example.com",
        proxy_port=8080,
    )

    assert client.proxies == {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}


# ------------------------------------------------------------------ end to end


class _RecordingProxy(http.server.BaseHTTPRequestHandler):
    """Answers every request itself, as a forward proxy would, and records the proxy credentials."""

    seen: list[tuple[str, str | None]] = []

    def do_GET(self) -> None:  # noqa: N802  name fixed by BaseHTTPRequestHandler
        type(self).seen.append((self.path, self.headers.get("Proxy-Authorization")))
        body = b"{}"
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        """Keep the test output clean."""


@pytest.fixture
def proxy() -> Iterator[int]:
    _RecordingProxy.seen = []
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _RecordingProxy)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.parametrize(("user", "password"), [("al/ice", "se/cr@t:x"), ("alice", "p%41ss")])
def test_the_proxy_receives_the_exact_credentials(
    monkeypatch: pytest.MonkeyPatch, proxy: int, user: str, password: str
) -> None:
    """A real request through a local stand-in proxy: the header it receives decodes to the configured values."""
    for name in ("no_proxy", "NO_PROXY"):
        monkeypatch.delenv(name, raising=False)
    client = client_with(user, password, server="127.0.0.1", port=proxy)

    response = client._do_it_get(url="http://portal.test/api/public/v1/list", auto_adapt_to_throttle=None)

    assert response.status_code == 200
    path, auth = _RecordingProxy.seen[0]
    assert path == "http://portal.test/api/public/v1/list"  # it really went through the proxy
    assert auth is not None
    scheme, _, encoded = auth.partition(" ")
    assert scheme == "Basic"
    assert base64.b64decode(encoded).decode("utf-8") == f"{user}:{password}"

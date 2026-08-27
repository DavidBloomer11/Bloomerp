from __future__ import annotations

import base64
import hashlib
import html
import secrets
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlsplit

import click
import requests

from ..base import BLOOMERP_IO_URL


CALLBACK_TIMEOUT_SECONDS = 300


class _CallbackServer(HTTPServer):
    expected_state: str
    authorization_code: str | None = None


class _CallbackHandler(BaseHTTPRequestHandler):
    server: _CallbackServer

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        parameters = parse_qs(parsed.query)
        code = parameters.get("code", [""])[0]
        state = parameters.get("state", [""])[0]

        if parsed.path != "/callback" or not code or state != self.server.expected_state:
            self._respond(400, "The CLI authorization callback was invalid.")
            return

        self.server.authorization_code = code
        self._respond(200, "Bloomerp CLI is now authenticated. You can close this window.")

    def _respond(self, status: int, message: str) -> None:
        body = (
            "<!doctype html><html><head><title>Bloomerp CLI</title></head>"
            f"<body><h1>{html.escape(message)}</h1></body></html>"
        ).encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def browser_login(server_url: str = BLOOMERP_IO_URL) -> str:
    callback_server = _CallbackServer(("127.0.0.1", 0), _CallbackHandler)
    callback_server.expected_state = secrets.token_urlsafe(32)
    verifier, challenge = _pkce_pair()
    callback_url = f"http://127.0.0.1:{callback_server.server_port}/callback"
    authorization_parameters = urlencode(
        {
            "redirect_uri": callback_url,
            "state": callback_server.expected_state,
            "code_challenge": challenge,
            "key_name": "Bloomerp CLI",
        }
    )
    authorization_url = (
        f"{server_url.rstrip('/')}/cli/auth/authorize/?{authorization_parameters}"
    )

    click.echo("Opening Bloomerp.io in your browser...")
    if not webbrowser.open(authorization_url):
        click.echo(f"Open this URL to continue:\n{authorization_url}")

    deadline = time.monotonic() + CALLBACK_TIMEOUT_SECONDS
    while callback_server.authorization_code is None and time.monotonic() < deadline:
        callback_server.timeout = min(1, max(0, deadline - time.monotonic()))
        callback_server.handle_request()
    callback_server.server_close()

    if callback_server.authorization_code is None:
        raise click.ClickException("Timed out waiting for browser authorization.")

    try:
        response = requests.post(
            f"{server_url.rstrip('/')}/api/auth/cli/exchange/",
            json={
                "code": callback_server.authorization_code,
                "code_verifier": verifier,
            },
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise click.ClickException(f"Could not complete browser login: {exc}") from exc

    api_key = response.json().get("api_key")
    if not api_key:
        raise click.ClickException("Bloomerp.io did not return an API key.")
    return str(api_key)

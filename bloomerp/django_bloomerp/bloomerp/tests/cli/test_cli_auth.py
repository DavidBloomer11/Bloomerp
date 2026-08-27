import json
import os
from importlib.metadata import version
from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from bloomerp.cli.client import BloomerpCliClient
from bloomerp.cli.credentials import delete_api_key, load_api_key, save_api_key
from bloomerp.cli.main import main


@patch("bloomerp.cli.auth.login.save_api_key")
@patch("bloomerp.cli.auth.login.BloomerpCliClient.session")
@patch("bloomerp.cli.auth.login.browser_login")
def test_auth_login_uses_browser_flow_and_saves_validated_key(
    browser_login: Mock,
    session: Mock,
    save_api_key_mock: Mock,
):
    """
    UC: We want to log in with the CLI using the browser
    
    Acceptance Criteria: We can login using the browser, which will generate an API key
    """
    browser_login.return_value = "blp_live_test_secret"
    session.return_value = {
        "authenticated": True,
        "user": {"email": "developer@example.com"},
    }

    result = CliRunner().invoke(main, ["auth", "login"])

    assert result.exit_code == 0
    assert "Logged in as developer@example.com" in result.output
    save_api_key_mock.assert_called_once_with("blp_live_test_secret")


@patch("bloomerp.cli.auth.login.save_api_key")
@patch("bloomerp.cli.auth.login.BloomerpCliClient.session")
def test_auth_login_accepts_a_supplied_api_key(
    session: Mock,
    save_api_key_mock: Mock,
):
    session.return_value = {
        "authenticated": True,
        "user": {"email": "developer@example.com"},
    }

    result = CliRunner().invoke(
        main,
        ["auth", "login", "--api-key", "blp_live_supplied_secret"],
    )

    assert result.exit_code == 0
    save_api_key_mock.assert_called_once_with("blp_live_supplied_secret")


def test_credentials_are_stored_per_server_with_restricted_permissions(tmp_path: Path):
    path = tmp_path / "credentials.json"

    with patch.dict(
        os.environ,
        {"BLOOMERP_CREDENTIALS_FILE": str(path), "BLOOMERP_API_KEY": ""},
    ):
        save_api_key("first-key", "https://first.example")
        save_api_key("second-key", "https://second.example")

        assert load_api_key("https://first.example") == "first-key"
        assert load_api_key("https://second.example") == "second-key"
        assert path.stat().st_mode & 0o777 == 0o600
        assert delete_api_key("https://first.example")
        assert load_api_key("https://first.example") is None


@patch("bloomerp.cli.client.requests.request")
def test_client_sends_the_api_key_header(request: Mock):
    request.return_value.status_code = 200
    request.return_value.raise_for_status.return_value = None

    BloomerpCliClient(
        server_url="https://api.example",
        api_key="blp_live_test_secret",
    ).request("GET", "/api/auth/session/")

    assert request.call_args.kwargs["headers"] == {
        "X-API-Key": "blp_live_test_secret"
    }

